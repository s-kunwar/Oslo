"""
OSLO - Open Speech Language Optimizer.

A universal, high-performance real-time speech translation assistant.
"""

__version__ = "1.0.0"
__author__ = "OSLO Contributors"

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
from oslo.transcription.model import ModelManager, model_manager
from oslo.processing.parallel import ParallelProcessor, WorkerConfig
from oslo.processing.batcher import AdaptiveBatcher, SmartBatcher

__all__ = [
    # Version
    "__version__",
    "__author__",
    # Config
    "AUDIO_CONFIG",
    "TRANSCRIPTION_CONFIG",
    "TRANSLATION_CONFIG",
    "PERFORMANCE_CONFIG",
    "PREPROCESSING_CONFIG",
    "VAD_CONFIG",
    "PARALLEL_CONFIG",
    "BATCHING_CONFIG",
    "LOGGING_CONFIG",
    # Audio
    "AudioProcessor",
    # Transcription
    "ModelManager",
    "model_manager",
    # Processing
    "ParallelProcessor",
    "WorkerConfig",
    "AdaptiveBatcher",
    "SmartBatcher",
]