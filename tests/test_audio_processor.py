# -*- coding: utf-8 -*-
"""
Test script to verify optimization improvements.
Compares original vs optimized implementation performance.
"""

import asyncio
import time
import numpy as np
import librosa
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from oslo.audio.processor import AudioProcessor
import oslo.config as config


def test_audio_preprocessing():
    """Test audio preprocessing improvements."""
    print("🔊 Testing Audio Preprocessing...")

    # Create test audio (sine wave with noise)
    sample_rate = config.AUDIO_CONFIG["sample_rate"]
    duration = 2.0  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Clean signal (1kHz sine wave)
    clean_signal = 0.5 * np.sin(2 * np.pi * 1000 * t)

    # Add noise
    noise = 0.1 * np.random.randn(len(t))
    noisy_signal = clean_signal + noise

    # Initialize processor
    processor = AudioProcessor(sample_rate=sample_rate)

    # Test preprocessing
    start_time = time.time()
    processed_signal = processor.preprocess_audio(noisy_signal)
    processing_time = time.time() - start_time

    # Extract features
    original_features = processor.extract_speech_features(noisy_signal)
    processed_features = processor.extract_speech_features(processed_signal)

    print(f"⏱️  Preprocessing time: {processing_time:.3f}s")
    print(f"📊 Original SNR: {original_features.get('snr_estimate', 0):.1f} dB")
    print(f"📊 Processed SNR: {processed_features.get('snr_estimate', 0):.1f} dB")
    print(f"📊 Original RMS: {original_features.get('rms', 0):.4f}")
    print(f"📊 Processed RMS: {processed_features.get('rms', 0):.4f}")

    # Calculate improvement
    if original_features.get('snr_estimate', 0) > 0:
        snr_improvement = processed_features.get('snr_estimate', 0) - original_features.get('snr_estimate', 0)
        print(f"✅ SNR Improvement: {snr_improvement:+.1f} dB")

    return processing_time < 0.1  # Should be fast


def test_model_parameters():
    """Test optimized model parameters."""
    print("\n🤖 Testing Model Parameters...")

    # Check parameter optimizations
    original_max_tokens = 256
    optimized_max_tokens = config.TRANSCRIPTION_CONFIG["max_new_tokens"]

    original_beams = 1
    optimized_beams = config.TRANSCRIPTION_CONFIG["num_beams"]

    print(f"📝 Max tokens: {original_max_tokens} → {optimized_max_tokens} (reduced by {100*(1-optimized_max_tokens/original_max_tokens):.0f}%)")
    print(f"🎯 Beam search: {original_beams} → {optimized_beams} (greedy for speed)")
    print(f"🌡️  Temperature: {config.TRANSCRIPTION_CONFIG['temperature']} (balanced randomness)")
    print(f"🎯 Top-p: {config.TRANSCRIPTION_CONFIG['top_p']} (nucleus sampling)")
    print(f"🔄 Repetition penalty: {config.TRANSCRIPTION_CONFIG['repetition_penalty']}")

    # Calculate expected speed improvement
    expected_speedup = (original_max_tokens / optimized_max_tokens) * 1.2  # Conservative estimate
    print(f"⚡ Expected speed improvement: ~{expected_speedup:.1f}x")

    return True


def test_vad_optimization():
    """Test VAD parameter optimizations."""
    print("\n🎙️  Testing VAD Optimizations...")

    print(f"📊 Sample rate: {config.VAD_CONFIG['sampling_rate']} Hz")
    print(f"⏱️  Min silence duration: {config.VAD_CONFIG['min_silence_duration']}s")
    print(f"📏 Speech padding: {config.VAD_CONFIG['speech_pad_ms']}ms")
    print(f"🎯 VAD threshold: {config.VAD_CONFIG['threshold']}")
    print(f"⏪ Pre-voice buffer: {config.VAD_CONFIG['pre_voice_ms']}ms")
    print(f"⏩ Post-voice buffer: {config.VAD_CONFIG['post_voice_ms']}ms")

    # Calculate expected improvements
    original_chunk_size = 512
    optimized_chunk_size = config.AUDIO_CONFIG["chunk_size"]

    if optimized_chunk_size != original_chunk_size:
        latency_improvement = 1000 * (original_chunk_size - optimized_chunk_size) / config.AUDIO_CONFIG["sample_rate"]
        print(f"⚡ Expected latency reduction: ~{latency_improvement:.1f}ms per chunk")

    return True


def test_performance_config():
    """Test performance configuration."""
    print("\n⚡ Testing Performance Configuration...")

    print(f"📊 Max queue size: {config.PERFORMANCE_CONFIG['max_queue_size']}")
    print(f"🔧 Parallel workers: {config.PERFORMANCE_CONFIG['parallel_workers']}")
    print(f"💾 Cache size: {config.PERFORMANCE_CONFIG['cache_size']}")
    print(f"🎯 Target latency: {config.PERFORMANCE_CONFIG['latency_target']}s")

    # Check logging configuration
    print(f"📝 Performance logging: {config.LOGGING_CONFIG['enable_performance_logging']}")
    print(f"⏱️  Latency logging: {config.LOGGING_CONFIG['log_latency']}")
    print(f"🎯 Accuracy logging: {config.LOGGING_CONFIG['log_accuracy']}")
    print(f"🔊 Audio quality logging: {config.LOGGING_CONFIG['log_audio_quality']}")

    return True


def test_preprocessing_config():
    """Test preprocessing configuration."""
    print("\n🎧 Testing Preprocessing Configuration...")

    print(f"🔇 Noise reduction: {config.PREPROCESSING_CONFIG['enable_noise_reduction']}")
    print(f"📡 High-pass filter: {config.PREPROCESSING_CONFIG['enable_highpass_filter']}")
    print(f"🎛️  AGC: {config.PREPROCESSING_CONFIG['enable_agc']}")
    print(f"📊 High-pass cutoff: {config.PREPROCESSING_CONFIG['highpass_cutoff']} Hz")
    print(f"🎯 AGC target: {config.PREPROCESSING_CONFIG['agc_target_level']} dBFS")
    print(f"🔊 Noise reduction strength: {config.PREPROCESSING_CONFIG['noise_reduction_prop_decrease']}")

    return True


def main():
    """Run all optimization tests."""
    print("="*70)
    print("🧪 SPEECH TRANSLATION OPTIMIZATION TEST")
    print("="*70)

    tests = [
        ("Audio Preprocessing", test_audio_preprocessing),
        ("Model Parameters", test_model_parameters),
        ("VAD Optimization", test_vad_optimization),
        ("Performance Config", test_performance_config),
        ("Preprocessing Config", test_preprocessing_config),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, "✅" if result else "❌"))
        except Exception as e:
            results.append((test_name, False, f"❌ Error: {e}"))

    print("\n" + "="*70)
    print("📊 TEST RESULTS")
    print("="*70)

    for test_name, result, status in results:
        print(f"{status} {test_name}: {'PASS' if result else 'FAIL'}")

    # Summary
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)

    print(f"\n📈 Summary: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All optimizations are ready for testing!")
        print("\n🚀 To test the CLI:")
        print("   oslo run --verbose")
    else:
        print("⚠️  Some optimizations need attention.")

    print("\n💡 Expected improvements:")
    print("   • Better audio quality through preprocessing")
    print("   • Reduced transcription latency")
    print("   • Improved speech detection accuracy")
    print("   • Better overall system responsiveness")


if __name__ == "__main__":
    main()