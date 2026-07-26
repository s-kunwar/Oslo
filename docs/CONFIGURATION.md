# Configuration Reference

## Overview

OSLO uses a centralized configuration system in `oslo/config.py`. All settings can be modified programmatically or via environment variables.

## Audio Configuration

```python
AUDIO_CONFIG = {
    "sample_rate": 16000,           # Sampling rate in Hz
    "chunk_size": 512,              # Samples per chunk (32ms at 16kHz)
    "blocksize": 512,               # sounddevice stream blocksize
    "vad_threshold": 0.5,           # Voice activity detection sensitivity (0-1)
    "min_speech_duration": 0.3,     # Minimum speech duration (seconds)
    "max_speech_duration": 10.0,    # Maximum speech duration (seconds)
}
```

## Transcription Configuration

```python
TRANSCRIPTION_CONFIG = {
    "model_name": "usefulsensors/moonshine-streaming-small",
    "device": "cuda" or "cpu",          # Inference device
    "max_new_tokens": 128,              # Maximum output tokens
    "num_beams": 1,                     # Greedy search (1) or beam search (>1)
    "temperature": 0.8,                # Sampling temperature
    "top_p": 0.9,                      # Nucleus sampling
    "repetition_penalty": 1.1,         # Avoid repeated tokens
    "use_cache": True,                 # KV cache for speed
    "attn_implementation": "sdpa",     # FlashAttention-2
}
```

## Translation Configuration

```python
TRANSLATION_CONFIG = {
    "model": "llama-3.1-8b-instant",   # Groq model ID
    "max_tokens": 256,                  # Maximum translation length
    "temperature": 0.7,                 # Response variation
    "system_prompt": "...",            # Custom system prompt
    "source_language": "en",            # Source language code
    "target_language": "hi",            # Target language code
}
```

## Audio Preprocessing

```python
PREPROCESSING_CONFIG = {
    "enable_noise_reduction": True,     # Spectral gating
    "enable_highpass_filter": True,     # Remove low frequencies
    "enable_agc": True,                 # Automatic gain control
    "highpass_cutoff": 80,              # Hz
    "agc_target_level": -20,            # dBFS
    "noise_reduction_prop_decrease": 0.95,  # Aggressiveness
}
```

## Parallel Processing

```python
PARALLEL_CONFIG = {
    "max_workers": 2,                   # Concurrent workers
    "cpu_threshold": 0.75,              # CPU usage threshold
    "memory_threshold": 0.80,           # Memory usage threshold
    "batch_size": 1,                    # Segments per worker
    "use_gpu": False,                   # GPU acceleration
    "adaptive_workers": True,           # Dynamic worker count
    "fallback_sequential": True,        # Sequential fallback
    "enable_parallel": True,            # Enable/disable
}
```

## Adaptive Batching

```python
BATCHING_CONFIG = {
    "max_batch_duration": 3.0,          # Maximum batch duration (seconds)
    "max_batch_size": 3,                # Maximum segments per batch
    "batch_timeout": 0.1,               # Wait time for additional segments
    "enable_batching": True,            # Enable/disable
    "smart_batching": True,             # Intelligent grouping
}
```

## Customization

### Changing Translation Language

```python
from oslo.config import TRANSLATION_CONFIG

TRANSLATION_CONFIG["target_language"] = "es"
TRANSLATION_CONFIG["system_prompt"] = "Translate to Spanish. Output ONLY the translation."
```

### Adjusting Performance

For faster transcription (lower quality):
```python
TRANSCRIPTION_CONFIG["max_new_tokens"] = 64
TRANSCRIPTION_CONFIG["temperature"] = 0.5
```

For higher accuracy:
```python
TRANSCRIPTION_CONFIG["max_new_tokens"] = 256
TRANSCRIPTION_CONFIG["temperature"] = 0.8
```

### GPU Acceleration

```python
TRANSCRIPTION_CONFIG["device"] = "cuda"
PARALLEL_CONFIG["use_gpu"] = True
```

### Reducing Memory Usage

```python
PARALLEL_CONFIG["max_workers"] = 1
BATCHING_CONFIG["max_batch_size"] = 1
TRANSCRIPTION_CONFIG["max_new_tokens"] = 64
```
