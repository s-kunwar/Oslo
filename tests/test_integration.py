# -*- coding: utf-8 -*-
"""
Integration tests for OSLO package.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    """Test that all package imports work correctly."""
    print("🧪 Testing Package Imports...")

    errors = []

    # Test core imports
    try:
        from oslo import (
            __version__,
            AudioProcessor,
            ModelManager,
            model_manager,
            ParallelProcessor,
            WorkerConfig,
            AdaptiveBatcher,
            SmartBatcher,
        )
        print("✅ Core imports successful")
    except ImportError as e:
        errors.append(f"Core import error: {e}")
        print(f"❌ Core import failed: {e}")

    # Test config imports
    try:
        from oslo.config import (
            AUDIO_CONFIG,
            TRANSCRIPTION_CONFIG,
            TRANSLATION_CONFIG,
            PERFORMANCE_CONFIG,
        )
        print("✅ Config imports successful")
    except ImportError as e:
        errors.append(f"Config import error: {e}")
        print(f"❌ Config import failed: {e}")

    # Test audio module
    try:
        from oslo.audio import AudioProcessor, create_audio_processor
        print("✅ Audio module imports successful")
    except ImportError as e:
        errors.append(f"Audio import error: {e}")
        print(f"❌ Audio import failed: {e}")

    # Test transcription module
    try:
        from oslo.transcription import ModelManager, model_manager
        print("✅ Transcription module imports successful")
    except ImportError as e:
        errors.append(f"Transcription import error: {e}")
        print(f"❌ Transcription import failed: {e}")

    # Test processing module
    try:
        from oslo.processing import (
            ParallelProcessor,
            WorkerConfig,
            SystemMonitor,
            AdaptiveBatcher,
            SmartBatcher,
        )
        print("✅ Processing module imports successful")
    except ImportError as e:
        errors.append(f"Processing import error: {e}")
        print(f"❌ Processing import failed: {e}")

    # Test translation module
    try:
        from oslo.translation import GroqTranslator, create_translator
        print("✅ Translation module imports successful")
    except ImportError as e:
        errors.append(f"Translation import error: {e}")
        print(f"❌ Translation import failed: {e}")

    return len(errors) == 0


def test_config_values():
    """Test that configuration values are valid."""
    print("\n🧪 Testing Configuration Values...")

    from oslo.config import (
        AUDIO_CONFIG,
        TRANSCRIPTION_CONFIG,
        TRANSLATION_CONFIG,
        PERFORMANCE_CONFIG,
    )

    errors = []

    # Check audio config
    if AUDIO_CONFIG["sample_rate"] != 16000:
        errors.append("Sample rate should be 16000")
    if AUDIO_CONFIG["chunk_size"] <= 0:
        errors.append("Chunk size must be positive")

    # Check transcription config
    if TRANSCRIPTION_CONFIG["max_new_tokens"] <= 0:
        errors.append("max_new_tokens must be positive")

    # Check translation config
    if not TRANSLATION_CONFIG["model"]:
        errors.append("Translation model must be specified")

    # Check performance config
    if PERFORMANCE_CONFIG["max_queue_size"] <= 0:
        errors.append("max_queue_size must be positive")

    if errors:
        for error in errors:
            print(f"❌ {error}")
        return False

    print("✅ All configuration values are valid")
    return True


def test_audio_processor_creation():
    """Test AudioProcessor can be created."""
    print("\n🧪 Testing AudioProcessor Creation...")

    try:
        from oslo.audio import AudioProcessor, create_audio_processor

        # Test direct creation
        processor1 = AudioProcessor(sample_rate=16000)
        print("✅ AudioProcessor created directly")

        # Test factory creation
        processor2 = create_audio_processor(sample_rate=16000)
        print("✅ AudioProcessor created via factory")

        return True
    except Exception as e:
        print(f"❌ AudioProcessor creation failed: {e}")
        return False


def test_batcher_creation():
    """Test AdaptiveBatcher can be created."""
    print("\n🧪 Testing Batcher Creation...")

    try:
        from oslo.processing import AdaptiveBatcher, SmartBatcher

        # Test AdaptiveBatcher
        batcher1 = AdaptiveBatcher(max_batch_size=3)
        print("✅ AdaptiveBatcher created")

        # Test SmartBatcher
        batcher2 = SmartBatcher(sample_rate=16000)
        print("✅ SmartBatcher created")

        return True
    except Exception as e:
        print(f"❌ Batcher creation failed: {e}")
        return False


def test_worker_config():
    """Test WorkerConfig dataclass."""
    print("\n🧪 Testing WorkerConfig...")

    try:
        from oslo.processing import WorkerConfig

        # Test default config
        config1 = WorkerConfig()
        print(f"✅ Default WorkerConfig: max_workers={config1.max_workers}")

        # Test custom config
        config2 = WorkerConfig(max_workers=4, adaptive_workers=False)
        print(f"✅ Custom WorkerConfig: max_workers={config2.max_workers}")

        return True
    except Exception as e:
        print(f"❌ WorkerConfig failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("="*70)
    print("🧪 OSLO INTEGRATION TEST SUITE")
    print("="*70)
    print()

    results = []

    # Run tests
    results.append(("Package Imports", test_imports()))
    results.append(("Configuration Values", test_config_values()))
    results.append(("AudioProcessor Creation", test_audio_processor_creation()))
    results.append(("Batcher Creation", test_batcher_creation()))
    results.append(("WorkerConfig", test_worker_config()))

    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\n📊 Total: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All integration tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    exit(main())