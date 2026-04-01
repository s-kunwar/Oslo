# -*- coding: utf-8 -*-
"""
Configuration parameters for OSLO speech transcription optimization.
"""

import torch

# Audio Processing Configuration
AUDIO_CONFIG = {
    "sample_rate": 16000,
    "chunk_size": 512,  # 32ms at 16kHz
    "blocksize": 512,  # Required by sounddevice InputStream
    "vad_threshold": 0.5,  # Voice activity detection sensitivity
    "min_speech_duration": 0.3,  # Minimum speech duration in seconds
    "max_speech_duration": 10.0,  # Maximum speech duration in seconds
}

# Transcription Model Configuration
TRANSCRIPTION_CONFIG = {
    "model_name": "usefulsensors/moonshine-streaming-small",
    "device": "cuda" if torch.cuda.is_available() else "cpu",
    "max_new_tokens": 128,  # Reduced for faster inference
    "num_beams": 1,  # Greedy search for speed
    "temperature": 0.8,  # Slight randomness for better accuracy
    "top_p": 0.9,  # Nucleus sampling
    "repetition_penalty": 1.1,  # Avoid repeated words
    "use_cache": True,
    "attn_implementation": "sdpa",  # FlashAttention for speed
}

# Translation Configuration
TRANSLATION_CONFIG = {
    "model": "llama-3.1-8b-instant",  # Fast model for real-time
    "max_tokens": 256,
    "temperature": 0.7,
    "system_prompt": "Translate to Hindi. Output ONLY the translation.",
    "source_language": "en",
    "target_language": "hi",
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    "max_queue_size": 10,  # Maximum items in processing queue
    "parallel_workers": 2,  # Number of parallel transcription workers
    "cache_size": 100,  # Number of phrases to cache
    "latency_target": 2.0,  # Target latency in seconds
}

# Audio Preprocessing Configuration
PREPROCESSING_CONFIG = {
    "enable_noise_reduction": True,
    "enable_highpass_filter": True,
    "enable_agc": True,
    "highpass_cutoff": 80,  # Hz
    "agc_target_level": -20,  # dBFS
    "noise_reduction_prop_decrease": 0.95,
}

# VAD Configuration
VAD_CONFIG = {
    "sampling_rate": 16000,
    "min_silence_duration": 0.3,  # Minimum silence to end speech
    "speech_pad_ms": 200,  # Padding around speech segments
    "threshold": 0.5,  # VAD threshold
    "pre_voice_ms": 100,  # Pre-voice buffer
    "post_voice_ms": 200,  # Post-voice buffer
}

# Logging Configuration
LOGGING_CONFIG = {
    "enable_performance_logging": True,
    "log_latency": True,
    "log_accuracy": True,
    "log_audio_quality": True,
}

# Parallel Processing Configuration
PARALLEL_CONFIG = {
    "max_workers": 2,  # Conservative for 16GB RAM (i7-13960H)
    "cpu_threshold": 0.75,  # Reduce workers if CPU > 75%
    "memory_threshold": 0.80,  # Reduce workers if memory > 80%
    "batch_size": 1,  # Process one audio segment at a time per worker
    "use_gpu": False,  # Default to CPU for memory efficiency
    "adaptive_workers": True,  # Dynamically adjust worker count
    "fallback_sequential": True,  # Fallback if parallel fails
    "enable_parallel": True,  # Enable/disable parallel processing
}

# Audio Batching Configuration
BATCHING_CONFIG = {
    "max_batch_duration": 3.0,  # Maximum total duration of a batch (seconds)
    "max_batch_size": 3,  # Maximum number of segments in a batch
    "batch_timeout": 0.1,  # Time to wait for additional segments (seconds)
    "enable_batching": True,  # Enable adaptive batching
    "smart_batching": True,  # Use intelligent grouping strategies
}

# Update Performance Configuration with parallel settings
PERFORMANCE_CONFIG = {
    "max_queue_size": 10,
    "parallel_workers": PARALLEL_CONFIG["max_workers"],  # Link to parallel config
    "cache_size": 100,
    "latency_target": 1.5,  # Reduced from 2.0s due to parallel processing
    "enable_parallel": PARALLEL_CONFIG["enable_parallel"],
}