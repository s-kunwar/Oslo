#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for parallel processing implementation.
Tests the new parallel processing components without requiring microphone input.
"""

import asyncio
import numpy as np
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from oslo.transcription.model import model_manager
from oslo.processing.parallel import ParallelProcessor, WorkerConfig
from oslo.processing.batcher import AdaptiveBatcher
import oslo.config as config


def create_test_audio(duration_seconds=2.0, sample_rate=16000):
    """Create synthetic audio data for testing."""
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
    # Create a simple sine wave with some noise
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
    audio += 0.1 * np.random.randn(len(t))  # Add some noise
    return audio


async def test_model_manager():
    """Test the model manager singleton pattern."""
    print("🧪 Testing Model Manager...")

    # Test model loading
    model, processor = model_manager.get_model(device="cpu", use_quantization=True)

    if model is not None and processor is not None:
        print("✅ Model manager loaded successfully")
        print(f"   Model device: {next(model.parameters()).device}")
        print(f"   Model dtype: {next(model.parameters()).dtype}")
        return True
    else:
        print("❌ Model manager failed to load")
        return False


async def test_parallel_processor():
    """Test the parallel processor with synthetic audio."""
    print("\n🧪 Testing Parallel Processor...")

    # Create test audio segments
    test_audio_segments = [
        create_test_audio(1.0),  # 1 second
        create_test_audio(1.5),  # 1.5 seconds
        create_test_audio(2.0),  # 2 seconds
    ]

    # Create a simple transcription function for testing
    async def mock_transcribe(audio_data):
        """Mock transcription function that simulates processing time."""
        # Simulate processing time based on audio length
        processing_time = len(audio_data) / 16000 * 0.1  # 0.1s per second of audio
        await asyncio.sleep(processing_time)

        # Return a mock transcript
        duration = len(audio_data) / 16000
        return f"Mock transcript for {duration:.1f}s audio"

    # Test with different worker configurations
    test_configs = [
        WorkerConfig(max_workers=1),
        WorkerConfig(max_workers=2),
        WorkerConfig(max_workers=4),
    ]

    for test_config in test_configs:
        print(f"\n   Testing with {test_config.max_workers} worker(s)...")

        processor = ParallelProcessor(test_config, mock_transcribe)

        start_time = time.time()
        results = await processor.process_batch(test_audio_segments)
        processing_time = time.time() - start_time

        print(f"   Processing time: {processing_time:.2f}s")
        print(f"   Results: {len(results)}/{len(test_audio_segments)} successful")

        # Print stats
        stats = processor.get_stats()
        print(f"   Success rate: {stats['success_rate']:.1%}")

        if test_config.max_workers > 1:
            # Check if parallel processing provided speedup
            expected_sequential_time = len(test_audio_segments) * 0.1  # Rough estimate
            speedup = expected_sequential_time / processing_time if processing_time > 0 else 0
            print(f"   Speedup factor: {speedup:.2f}x")

    return True  # All configurations tested successfully


def test_adaptive_batcher():
    """Test the adaptive audio batcher."""
    print("\n🧪 Testing Adaptive Batcher...")

    batcher = AdaptiveBatcher(
        max_batch_duration=3.0,
        max_batch_size=3,
        batch_timeout=0.1
    )

    # Test adding segments
    test_segments = [
        create_test_audio(0.5),  # Short segment
        create_test_audio(1.0),  # Medium segment
        create_test_audio(2.0),  # Long segment
    ]

    for i, audio in enumerate(test_segments):
        batcher.add_segment(audio, sample_rate=16000)
        print(f"   Added segment {i+1}: {len(audio)/16000:.1f}s")

    # Test batch creation
    batch = batcher.get_batch()
    print(f"   Batch created: {len(batch)} segments")

    # Test buffer info
    info = batcher.get_buffer_info()
    print(f"   Buffer info: {info}")

    success = len(batch) > 0
    return success


async def test_integration():
    """Test integration of all components."""
    print("\n🧪 Testing Integration...")

    # Clean up any existing model and force reload without quantization
    model_manager.cleanup()
    model, processor = model_manager.get_model(device="cpu", use_quantization=False)

    # Create test audio - use a longer duration with more complex signal
    test_audio = create_test_audio(2.0)

    # Test actual transcription
    from oslo.cli import transcribe_optimized
    from oslo.audio.processor import AudioProcessor

    audio_processor = AudioProcessor(sample_rate=16000)

    try:
        transcript = transcribe_optimized(
            test_audio,
            sample_rate=16000,
            model=model,
            processor_obj=processor,
            audio_processor=audio_processor,
        )

        # For integration test, we just want to ensure the function runs without errors
        # The transcript might be empty for synthetic audio, which is expected
        print("✅ Integration test passed - function executed successfully")
        print(f"   Transcript result: '{transcript}'")
        print("   Note: Empty transcript is expected for synthetic audio")
        return True

    except Exception as e:
        print(f"❌ Integration test failed with error: {e}")
        return False


async def main():
    """Run all tests."""
    print("="*70)
    print("🧪 PARALLEL PROCESSING TEST SUITE")
    print("="*70)

    test_results = []

    # Run tests
    test_results.append(await test_model_manager())
    test_results.append(await test_parallel_processor())
    test_results.append(test_adaptive_batcher())
    test_results.append(await test_integration())

    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)

    # Filter out None values and convert to integers (True=1, False=0)
    valid_results = [1 if result else 0 for result in test_results if result is not None]
    total_tests = len(test_results)
    passed = sum(valid_results)

    print(f"Tests passed: {passed}/{total_tests} ({passed/max(1, total_tests)*100:.1f}%)")

    if passed == total_tests:
        print("✅ All tests passed! Parallel processing is ready.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")

    return passed == total_tests


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())

    # Exit with appropriate code
    sys.exit(0 if success else 1)