# -*- coding: utf-8 -*-
"""
CLI entry point for OSLO - Open Speech Language Optimizer.

Usage:
    oslo run                          # Run with defaults
    oslo run --source en --target hi  # Specify languages
    oslo run --no-parallel            # Disable parallel processing
    oslo run --backend moonshine      # Use specific backend
"""

import argparse
import asyncio
import os
import sys
from typing import Optional

import numpy as np
import sounddevice as sd
from silero_vad import load_silero_vad, VADIterator

from oslo.config import (
    AUDIO_CONFIG,
    TRANSCRIPTION_CONFIG,
    TRANSLATION_CONFIG,
    PERFORMANCE_CONFIG,
    PREPROCESSING_CONFIG,
    VAD_CONFIG,
    PARALLEL_CONFIG,
    BATCHING_CONFIG,
    LOGGING_CONFIG,
)
from oslo.audio.processor import AudioProcessor
from oslo.transcription.model import model_manager
from oslo.processing.parallel import ParallelProcessor, WorkerConfig
from oslo.processing.batcher import AdaptiveBatcher
from oslo.translation.groq_client import GroqTranslator


# Performance tracking
performance_metrics = {
    "transcription_latency": [],
    "translation_latency": [],
    "audio_quality": [],
}


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description="OSLO - Open Speech Language Optimizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    oslo run                          # Run with defaults (English to Hindi)
    oslo run --source en --target es  # English to Spanish
    oslo run --no-parallel            # Disable parallel processing
    oslo run --device cuda            # Use GPU acceleration
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the speech translator")
    run_parser.add_argument(
        "--source", "-s",
        default="en",
        help="Source language code (default: en)"
    )
    run_parser.add_argument(
        "--target", "-t",
        default="hi",
        help="Target language code (default: hi)"
    )
    run_parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Disable parallel processing"
    )
    run_parser.add_argument(
        "--device", "-d",
        default="auto",
        choices=["auto", "cuda", "cpu"],
        help="Device for inference (default: auto)"
    )
    run_parser.add_argument(
        "--model", "-m",
        default="usefulsensors/moonshine-streaming-small",
        help="Transcription model to use"
    )
    run_parser.add_argument(
        "--translation-model",
        default="llama-3.1-8b-instant",
        help="Translation model (Groq API)"
    )
    run_parser.add_argument(
        "--api-key",
        default=None,
        help="Groq API key (default: GROQ_API_KEY env var)"
    )
    run_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    return parser


def update_config(args: argparse.Namespace) -> None:
    """Update configuration based on CLI arguments."""
    # Update language settings
    TRANSLATION_CONFIG["source_language"] = args.source
    TRANSLATION_CONFIG["target_language"] = args.target
    TRANSLATION_CONFIG["model"] = args.translation_model

    # Build translation prompt
    language_names = {
        "en": "English", "hi": "Hindi", "es": "Spanish", "fr": "French",
        "de": "German", "ja": "Japanese", "zh": "Chinese", "ar": "Arabic",
        "pt": "Portuguese", "ru": "Russian", "ko": "Korean", "it": "Italian",
    }
    source_name = language_names.get(args.source, args.source)
    target_name = language_names.get(args.target, args.target)
    TRANSLATION_CONFIG["system_prompt"] = (
        f"Translate from {source_name} to {target_name}. Output ONLY the translation."
    )

    # Update device
    if args.device == "cuda":
        TRANSCRIPTION_CONFIG["device"] = "cuda"
    elif args.device == "cpu":
        TRANSCRIPTION_CONFIG["device"] = "cpu"

    # Update parallel processing
    if args.no_parallel:
        PARALLEL_CONFIG["enable_parallel"] = False

    # Update logging
    LOGGING_CONFIG["enable_performance_logging"] = args.verbose


def transcribe_optimized(
    audio_array: np.ndarray,
    sample_rate: int = 16000,
    model=None,
    processor_obj=None,
    audio_processor: Optional[AudioProcessor] = None,
) -> str:
    """Optimized transcription with preprocessing and better parameters."""
    import time
    import torch

    start_time = time.time()

    # Use provided model/processor or fallback to global ones
    if model is None:
        model, processor_obj = model_manager.get_model(
            device=TRANSCRIPTION_CONFIG["device"]
        )

    try:
        # 1. Apply audio preprocessing
        if audio_processor and (
            PREPROCESSING_CONFIG["enable_noise_reduction"] or
            PREPROCESSING_CONFIG["enable_highpass_filter"] or
            PREPROCESSING_CONFIG["enable_agc"]
        ):
            audio_array = audio_processor.preprocess_audio(audio_array)

        # 2. Extract audio quality metrics
        if audio_processor and LOGGING_CONFIG["log_audio_quality"]:
            features = audio_processor.extract_speech_features(audio_array)
            performance_metrics["audio_quality"].append(features)

        # 3. Normalize audio
        if audio_array.max() > 1.0:
            audio_array = audio_array / 32768.0

        # 4. Prepare inputs
        inputs = processor_obj(
            audio_array.tolist(),
            sampling_rate=sample_rate,
            return_tensors="pt"
        ).to(TRANSCRIPTION_CONFIG["device"])

        # Ensure input dtype matches model dtype
        try:
            if hasattr(model, 'dtype') and model.dtype is not None:
                inputs = inputs.to(model.dtype)
            else:
                inputs = inputs.float()
        except Exception:
            inputs = inputs.float()

        # 5. Generate transcription
        with torch.no_grad():
            generate_kwargs = {
                "max_new_tokens": TRANSCRIPTION_CONFIG["max_new_tokens"],
                "num_beams": TRANSCRIPTION_CONFIG["num_beams"],
                "repetition_penalty": TRANSCRIPTION_CONFIG["repetition_penalty"],
                "use_cache": TRANSCRIPTION_CONFIG["use_cache"],
            }

            if TRANSCRIPTION_CONFIG.get("temperature") is not None:
                generate_kwargs["temperature"] = TRANSCRIPTION_CONFIG["temperature"]
            if TRANSCRIPTION_CONFIG.get("top_p") is not None:
                generate_kwargs["top_p"] = TRANSCRIPTION_CONFIG["top_p"]

            outputs = model.generate(**inputs, **generate_kwargs)

        # 6. Decode transcript
        transcript = processor_obj.batch_decode(
            outputs,
            skip_special_tokens=True
        )[0].strip()

        # 7. Track performance
        latency = time.time() - start_time
        performance_metrics["transcription_latency"].append(latency)

        if LOGGING_CONFIG["log_latency"]:
            print(f"⏱️  Transcription latency: {latency:.3f}s")

        return transcript

    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return ""


async def run_translation_loop(
    translator: GroqTranslator,
    audio_processor: AudioProcessor,
    model,
    processor,
    verbose: bool = False,
) -> None:
    """Run the main translation loop."""
    import torch

    # Initialize VAD
    vad_model = load_silero_vad(onnx=True)
    vad_iterator = VADIterator(vad_model, sampling_rate=VAD_CONFIG["sampling_rate"])

    # Initialize parallel processing if enabled
    parallel_processor = None
    audio_batcher = None

    if PARALLEL_CONFIG["enable_parallel"]:
        print("🔧 Parallel processing enabled")
        parallel_config = {k: v for k, v in PARALLEL_CONFIG.items()
                         if k in ['max_workers', 'cpu_threshold', 'memory_threshold',
                                 'batch_size', 'use_gpu', 'adaptive_workers', 'fallback_sequential']}
        worker_config = WorkerConfig(**parallel_config)

        async def transcribe_parallel(audio_data):
            return transcribe_optimized(
                audio_data,
                sample_rate=AUDIO_CONFIG["sample_rate"],
                model=model,
                processor_obj=processor,
                audio_processor=audio_processor,
            )

        parallel_processor = ParallelProcessor(worker_config, transcribe_parallel)

        if BATCHING_CONFIG["enable_batching"]:
            audio_batcher = AdaptiveBatcher(
                max_batch_duration=BATCHING_CONFIG["max_batch_duration"],
                max_batch_size=BATCHING_CONFIG["max_batch_size"],
                batch_timeout=BATCHING_CONFIG["batch_timeout"]
            )
            print("📦 Adaptive batching enabled")

    # Speech queue
    speech_queue = asyncio.Queue(maxsize=PERFORMANCE_CONFIG["max_queue_size"])

    # Event loop reference
    loop = asyncio.get_running_loop()

    async def process_audio():
        """Process audio from queue."""
        while True:
            try:
                if PARALLEL_CONFIG["enable_parallel"] and BATCHING_CONFIG["enable_batching"] and audio_batcher:
                    # Use batching for parallel processing
                    audio_data = await asyncio.wait_for(
                        speech_queue.get(),
                        timeout=BATCHING_CONFIG["batch_timeout"]
                    )
                    audio_batcher.add_segment(audio_data, AUDIO_CONFIG["sample_rate"])

                    if audio_batcher.should_process_batch():
                        audio_batch = audio_batcher.get_batch()
                        if audio_batch:
                            transcripts = await parallel_processor.process_batch(audio_batch)

                            for i, transcript in enumerate(transcripts):
                                if transcript and transcript.strip():
                                    if verbose:
                                        print(f"📝 Transcribed [{i}]: '{transcript}'")

                                    translation = await translator.translate_async(transcript)

                                    if verbose:
                                        print(f"🌍 Translated [{i}]: '{translation}'")

                                    print(f"\n💬 Message {i+1}: {transcript}")
                                    print(f"🌐 Translation: {translation}")
                                    print("-" * 60)

                            for _ in range(len(audio_batch)):
                                speech_queue.task_done()
                else:
                    # Sequential processing
                    audio_data = await speech_queue.get()

                    if verbose:
                        print(f"🔊 Processing {len(audio_data)} samples...")

                    transcript = transcribe_optimized(
                        audio_data,
                        sample_rate=AUDIO_CONFIG["sample_rate"],
                        model=model,
                        processor_obj=processor,
                        audio_processor=audio_processor,
                    )

                    if not transcript.strip():
                        if verbose:
                            print("⚠️  Empty transcript, skipping...")
                        speech_queue.task_done()
                        continue

                    if verbose:
                        print(f"📝 Transcribed: '{transcript}'")

                    translation = await translator.translate_async(transcript)

                    if verbose:
                        print(f"🌍 Translated: '{translation}'")

                    print(f"\n💬 Last Message: {transcript}")
                    print(f"🌐 Translation: {translation}")
                    print("-" * 60)

                    speech_queue.task_done()

            except asyncio.TimeoutError:
                # Process any remaining batched audio
                if (PARALLEL_CONFIG["enable_parallel"] and
                    BATCHING_CONFIG["enable_batching"] and
                    audio_batcher and
                    audio_batcher.get_buffer_info()["segment_count"] > 0):

                    audio_batch = audio_batcher.get_immediate_batch()
                    if audio_batch:
                        transcripts = await parallel_processor.process_batch(audio_batch)

                        for i, transcript in enumerate(transcripts):
                            if transcript and transcript.strip():
                                translation = await translator.translate_async(transcript)
                                print(f"\n💬 Message {i+1}: {transcript}")
                                print(f"🌐 Translation: {translation}")
                                print("-" * 60)

                        for _ in range(len(audio_batch)):
                            speech_queue.task_done()

            except Exception as e:
                print(f"❌ Processing error: {e}")
                try:
                    speech_queue.task_done()
                except:
                    pass

    async def capture_audio():
        """Capture audio from microphone."""
        chunk_size = AUDIO_CONFIG["chunk_size"]
        audio_buffer = []
        speech_active = False

        def callback(indata, frames, time_info, status):
            nonlocal speech_active

            audio_chunk = indata.flatten().astype(np.float32)
            speech_dict = vad_iterator(audio_chunk)

            if speech_dict:
                if "start" in speech_dict:
                    if not speech_active:
                        speech_active = True
                        audio_buffer.clear()
                        if verbose:
                            print("🎙️  Speech started...")

                if "end" in speech_dict:
                    if speech_active and audio_buffer:
                        speech_active = False

                        speech_duration = len(audio_buffer) * chunk_size / AUDIO_CONFIG["sample_rate"]

                        if (speech_duration >= AUDIO_CONFIG["min_speech_duration"] and
                            speech_duration <= AUDIO_CONFIG["max_speech_duration"]):

                            full_audio = np.concatenate(audio_buffer)

                            # Apply preprocessing
                            if (PREPROCESSING_CONFIG["enable_noise_reduction"] or
                                PREPROCESSING_CONFIG["enable_highpass_filter"] or
                                PREPROCESSING_CONFIG["enable_agc"]):
                                full_audio = audio_processor.preprocess_audio(full_audio)

                            asyncio.run_coroutine_threadsafe(speech_queue.put(full_audio), loop)

                            if verbose:
                                print(f"📤 Queued {len(audio_buffer)} chunks ({speech_duration:.2f}s)")

                        audio_buffer.clear()

            # Buffer audio while speech is active
            if speech_active:
                audio_buffer.append(audio_chunk)

                # Prevent buffer overflow
                if len(audio_buffer) * chunk_size / AUDIO_CONFIG["sample_rate"] > AUDIO_CONFIG["max_speech_duration"]:
                    speech_active = False
                    audio_buffer.clear()
                    if verbose:
                        print("⚠️  Speech too long, resetting...")

        with sd.InputStream(
            samplerate=AUDIO_CONFIG["sample_rate"],
            channels=1,
            callback=callback,
            blocksize=chunk_size
        ):
            while True:
                await asyncio.sleep(0.05)

    print("🎤 Starting OSLO speech translation...")
    print(f"📡 Listening for speech ({TRANSLATION_CONFIG['source_language']} → {TRANSLATION_CONFIG['target_language']})...")
    print("-" * 60)

    try:
        await asyncio.gather(capture_audio(), process_audio())
    except asyncio.CancelledError:
        print("\n🛑 Shutting down...")
        print_performance_summary()


def print_performance_summary():
    """Print performance metrics summary."""
    if not performance_metrics["transcription_latency"]:
        return

    print("\n" + "=" * 60)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 60)

    # Latency statistics
    print("\n⏱️  LATENCY STATISTICS")
    print("-" * 30)
    if performance_metrics["transcription_latency"]:
        avg_trans = np.mean(performance_metrics["transcription_latency"])
        min_trans = np.min(performance_metrics["transcription_latency"])
        max_trans = np.max(performance_metrics["transcription_latency"])
        print(f"Transcription: {avg_trans:.3f}s (min: {min_trans:.3f}s, max: {max_trans:.3f}s)")

    if performance_metrics["translation_latency"]:
        avg_transl = np.mean(performance_metrics["translation_latency"])
        min_transl = np.min(performance_metrics["translation_latency"])
        max_transl = np.max(performance_metrics["translation_latency"])
        print(f"Translation: {avg_transl:.3f}s (min: {min_transl:.3f}s, max: {max_transl:.3f}s)")

    # Processing volume
    print("\n📈 PROCESSING VOLUME")
    print("-" * 30)
    print(f"Total transcriptions: {len(performance_metrics['transcription_latency'])}")
    print(f"Total translations: {len(performance_metrics['translation_latency'])}")


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "run":
        # Update configuration
        update_config(args)

        # Get API key
        api_key = args.api_key or os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("❌ Error: GROQ_API_KEY environment variable not set")
            print("   Set it with: export GROQ_API_KEY=your_key")
            sys.exit(1)

        # Initialize components
        print(f"🚀 Loading model on {TRANSCRIPTION_CONFIG['device']}...")
        model, processor = model_manager.get_model(
            device=TRANSCRIPTION_CONFIG["device"]
        )

        audio_processor = AudioProcessor(sample_rate=AUDIO_CONFIG["sample_rate"])
        translator = GroqTranslator(
            api_key=api_key,
            model=TRANSLATION_CONFIG["model"],
        )

        # Run the translation loop
        try:
            asyncio.run(run_translation_loop(
                translator=translator,
                audio_processor=audio_processor,
                model=model,
                processor=processor,
                verbose=args.verbose,
            ))
        except KeyboardInterrupt:
            print_performance_summary()


if __name__ == "__main__":
    main()