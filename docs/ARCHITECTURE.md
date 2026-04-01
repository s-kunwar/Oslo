# OSLO Architecture

This document describes the architecture of OSLO (Open Speech Language Optimizer).

## Overview

OSLO is a real-time speech translation system that captures audio from a microphone, detects speech using Voice Activity Detection (VAD), transcribes using the Moonshine ASR model, and translates using the Groq API.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Audio Input (Microphone)                      │
└─────────────────────────────┬───────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    VAD (Silero) - Speech Detection                    │
│              Detects speech start/end, buffers audio                   │
└─────────────────────────────┬───────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                Audio Preprocessing (AudioProcessor)                   │
│   • Noise reduction (spectral gating)                                 │
│   • High-pass filtering (80Hz cutoff)                                 │
│   • Automatic Gain Control (-20 dBFS target)                          │
│   • Audio normalization                                               │
└─────────────────────────────┬───────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Adaptive Batching (AdaptiveBatcher)                      │
│   Groups audio segments for optimal parallel processing               │
└─────────────────────────────┬───────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│            Parallel Processing (ParallelProcessor)                    │
│   • Multiple workers with resource monitoring                         │
│   • Adaptive worker count based on CPU/memory                         │
│   • Fallback to sequential on resource pressure                       │
└─────────────────────────────┬───────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│         Transcription (ModelManager → Moonshine ASR)                  │
│   • usefulSensors/moonshine-streaming-small                           │
│   • Optimized inference (128 tokens, greedy search)                  │
└─────────────────────────────┬───────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                Translation (Groq API → Llama)                         │
│   • llama-3.1-8b-instant model                                       │
│   • Language-pair specific prompts                                    │
└─────────────────────────────┬───────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Output (Text)                                │
│   Original transcript + Translation printed to console                │
└─────────────────────────────────────────────────────────────────────┘
```

## Package Structure

```
oslo/
├── __init__.py              # Package exports
├── config.py                # Centralized configuration
├── cli.py                   # Command-line interface
│
├── audio/                   # Audio processing
│   ├── __init__.py
│   └── processor.py         # AudioProcessor class
│
├── transcription/           # Speech-to-text
│   ├── __init__.py
│   ├── model.py             # ModelManager class
│   └── moonshine_voice.py   # Alternative backend
│
├── processing/              # Processing pipeline
│   ├── __init__.py
│   ├── parallel.py          # ParallelProcessor
│   └── batcher.py           # AdaptiveBatcher
│
└── translation/             # Text translation
    ├── __init__.py
    └── groq_client.py       # Groq API client
```

## Key Components

### 1. Audio Processing (`oslo.audio`)

The `AudioProcessor` class handles all audio preprocessing:

- **Noise Reduction**: Uses spectral gating to remove background noise
- **High-Pass Filter**: Removes low-frequency rumble below 80Hz
- **AGC**: Automatic Gain Control to normalize volume
- **Feature Extraction**: Extracts RMS, SNR, spectral features

```python
from oslo.audio import AudioProcessor

processor = AudioProcessor(sample_rate=16000)
processed_audio = processor.preprocess_audio(raw_audio)
features = processor.extract_speech_features(audio)
```

### 2. Transcription (`oslo.transcription`)

Two transcription backends are available:

**Primary (Moonshine via Transformers)**:
```python
from oslo.transcription import model_manager

model, processor = model_manager.get_model(device="cpu")
# Use model for transcription
```

**Alternative (MoonshineVoice package)**:
```python
from oslo.transcription import MoonshineVoiceTranscriber

transcriber = MoonshineVoiceTranscriber(language="en")
text = transcriber.transcribe(audio_data)
```

### 3. Processing (`oslo.processing`)

**ParallelProcessor**: Manages concurrent transcription with resource monitoring

```python
from oslo.processing import ParallelProcessor, WorkerConfig

config = WorkerConfig(max_workers=2)
processor = ParallelProcessor(config, transcription_func)
results = await processor.process_batch(audio_segments)
```

**AdaptiveBatcher**: Groups audio segments for optimal processing

```python
from oslo.processing import AdaptiveBatcher

batcher = AdaptiveBatcher(max_batch_size=3)
batcher.add_segment(audio_data, sample_rate)
if batcher.should_process_batch():
    batch = batcher.get_batch()
```

### 4. Translation (`oslo.translation`)

The `GroqTranslator` class provides translation via Groq API:

```python
from oslo.translation import GroqTranslator

translator = GroqTranslator(api_key="your_key")
translation = await translator.translate_async(
    text="Hello",
    source_language="en",
    target_language="hi"
)
```

### 5. Configuration (`oslo.config`)

All configuration is centralized:

```python
from oslo.config import (
    AUDIO_CONFIG,        # Audio processing settings
    TRANSCRIPTION_CONFIG, # Model parameters
    TRANSLATION_CONFIG,   # Translation settings
    PARALLEL_CONFIG,      # Parallel processing
    PREPROCESSING_CONFIG, # Audio preprocessing
    VAD_CONFIG,          # Voice activity detection
)
```

## Data Flow

1. **Audio Capture**: `sounddevice` captures 16kHz mono audio in chunks
2. **VAD**: Silero VAD detects speech start/end boundaries
3. **Buffering**: Audio chunks are buffered during speech
4. **Preprocessing**: `AudioProcessor` cleans and normalizes audio
5. **Batching**: Optional batching for parallel processing
6. **Transcription**: Moonshine ASR converts speech to text
7. **Translation**: Groq API translates text
8. **Output**: Results printed to console

## Threading Model

- **Main Thread**: asyncio event loop
- **Audio Callback**: Runs in separate thread (sounddevice)
- **Transcription**: Can run in parallel workers (asyncio tasks)
- **Translation**: Async, uses thread pool for blocking API calls

## Resource Management

- **Memory**: Model loaded once (singleton pattern)
- **CPU**: Adaptive worker count based on load
- **GPU**: Optional CUDA support for inference

## Configuration Options

### Audio Settings
```python
AUDIO_CONFIG = {
    "sample_rate": 16000,
    "chunk_size": 512,
    "vad_threshold": 0.5,
    "min_speech_duration": 0.3,
    "max_speech_duration": 10.0,
}
```

### Model Settings
```python
TRANSCRIPTION_CONFIG = {
    "model_name": "usefulSensors/moonshine-streaming-small",
    "device": "cuda" if torch.cuda.is_available() else "cpu",
    "max_new_tokens": 128,
    "num_beams": 1,
}
```

### Translation Settings
```python
TRANSLATION_CONFIG = {
    "model": "llama-3.1-8b-instant",
    "max_tokens": 256,
    "temperature": 0.7,
    "source_language": "en",
    "target_language": "hi",
}
```

## Extending OSLO

### Adding a New Transcription Backend

1. Create a new file in `oslo/transcription/`
2. Implement a class with `transcribe(audio_data, sample_rate)` method
3. Register in `oslo/transcription/__init__.py`

### Adding a New Translation Backend

1. Create a new file in `oslo/translation/`
2. Implement async `translate(text, source, target)` method
3. Add configuration in `oslo/config.py`

### Adding CLI Commands

1. Add new subparser in `oslo/cli.py`
2. Implement command function
3. Add to main entry point