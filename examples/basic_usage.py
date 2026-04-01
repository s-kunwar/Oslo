# -*- coding: utf-8 -*-
"""
Basic usage example for OSLO.

This example shows how to use OSLO as a library for speech translation.
"""

import asyncio
import os
import numpy as np
from scipy.io import wavfile

from oslo import (
    AudioProcessor,
    ModelManager,
    GroqTranslator,
    AdaptiveBatcher,
    AUDIO_CONFIG,
)


async def translate_audio_file(
    audio_file: str,
    source_language: str = "en",
    target_language: str = "hi",
    api_key: str = None,
):
    """
    Translate an audio file from one language to another.

    Args:
        audio_file: Path to audio file (WAV format)
        source_language: Source language code
        target_language: Target language code
        api_key: Groq API key (optional, uses env var)

    Returns:
        Tuple of (transcript, translation)
    """
    # Initialize components
    audio_processor = AudioProcessor(sample_rate=AUDIO_CONFIG["sample_rate"])
    model_manager = ModelManager()
    translator = GroqTranslator(api_key=api_key)

    # Load audio file
    print(f"📂 Loading audio file: {audio_file}")
    sample_rate, audio_data = wavfile.read(audio_file)

    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = audio_data[:, 0]

    # Resample if needed
    if sample_rate != AUDIO_CONFIG["sample_rate"]:
        import librosa
        audio_data = librosa.resample(
            audio_data.astype(np.float32),
            orig_sr=sample_rate,
            target_sr=AUDIO_CONFIG["sample_rate"]
        )

    # Preprocess audio
    print("🔧 Preprocessing audio...")
    audio_processed = audio_processor.preprocess_audio(audio_data.astype(np.float32))

    # Get transcription model
    print("🚀 Loading transcription model...")
    model, processor = model_manager.get_model(device="cpu")

    # Transcribe
    print("📝 Transcribing...")
    # Note: This is a simplified example - full implementation would use
    # the transcribe_optimized function from oslo.cli
    import torch

    inputs = processor(
        audio_processed.tolist(),
        sampling_rate=AUDIO_CONFIG["sample_rate"],
        return_tensors="pt"
    )

    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=128, num_beams=1)

    transcript = processor.batch_decode(outputs, skip_special_tokens=True)[0].strip()

    # Translate
    print("🌍 Translating...")
    translation = await translator.translate_async(
        transcript,
        source_language=source_language,
        target_language=target_language
    )

    # Cleanup
    model_manager.cleanup()

    return transcript, translation


async def main():
    """Main example function."""
    print("=" * 60)
    print("OSLO Basic Usage Example")
    print("=" * 60)
    print()

    # Check for API key
    if not os.environ.get("GROQ_API_KEY"):
        print("❌ Error: GROQ_API_KEY environment variable not set")
        print("   Set it with: export GROQ_API_KEY=your_key")
        return

    # Example: Translate an audio file
    audio_file = "example.wav"  # Replace with your audio file

    print(f"Translating {audio_file}...")
    print(f"  Source: English (en)")
    print(f"  Target: Hindi (hi)")
    print()

    try:
        transcript, translation = await translate_audio_file(
            audio_file,
            source_language="en",
            target_language="hi"
        )

        print()
        print("=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"📝 Transcript: {transcript}")
        print(f"🌍 Translation: {translation}")
        print("=" * 60)

    except FileNotFoundError:
        print(f"❌ File not found: {audio_file}")
        print("   Create a WAV file or specify a different path")


if __name__ == "__main__":
    asyncio.run(main())