# OSLO - Open Speech Language Optimizer

A universal, high-performance real-time speech translation assistant.

## Project Overview

OSLO captures audio from the microphone, detects speech using Voice Activity Detection (VAD), transcribes using the Moonshine ASR model, and translates using the Groq API. The system is optimized for low latency with parallel processing, adaptive batching, and audio preprocessing.

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Set API key
export GROQ_API_KEY=your_key

# Run
oslo run --source en --target hi --verbose
```

## Package Structure

```
oslo/
├── oslo/                       # Main package
│   ├── __init__.py             # Exports: AudioProcessor, ModelManager, etc.
│   ├── config.py                # All configuration constants
│   ├── cli.py                   # CLI entry point (oslo run)
│   │
│   ├── audio/
│   │   └── processor.py         # AudioProcessor class
│   │
│   ├── transcription/
│   │   ├── model.py             # ModelManager (singleton)
│   │   └── moonshine_voice.py   # Alternative backend
│   │
│   ├── processing/
│   │   ├── parallel.py          # ParallelProcessor, WorkerConfig
│   │   └── batcher.py           # AdaptiveBatcher, SmartBatcher
│   │
│   └── translation/
│       └── groq_client.py       # GroqTranslator class
│
├── tests/                       # Test suite
├── examples/                    # Example scripts
├── docs/                        # Documentation
├── requirements.txt             # Dependencies
└── pyproject.toml               # Package config + CLI
```

## Architecture

```
Audio Input → VAD (Silero) → AudioProcessor → AdaptiveBatcher →
ParallelProcessor → Transcription (Moonshine) → Translation (Groq) → Output
```

## Key Components

### oslo.config
All configuration constants:
- `AUDIO_CONFIG` - Audio settings (sample_rate, chunk_size, VAD)
- `TRANSCRIPTION_CONFIG` - Model parameters
- `TRANSLATION_CONFIG` - Translation settings
- `PARALLEL_CONFIG` - Parallel processing settings

### oslo.audio.processor.AudioProcessor
Audio preprocessing pipeline:
- `preprocess_audio(audio)` - Full pipeline (noise reduction, AGC, filtering)
- `extract_speech_features(audio)` - Get RMS, SNR, spectral features

### oslo.transcription.model.ModelManager
Singleton model manager:
- `get_model(device, use_quantization)` - Load/get model
- `cleanup()` - Free memory

### oslo.processing.parallel.ParallelProcessor
Multi-worker transcription:
- `process_batch(segments)` - Process audio segments in parallel
- Adaptive worker count based on CPU/memory

### oslo.processing.batcher.AdaptiveBatcher
Smart audio batching:
- `add_segment(audio, sample_rate)` - Add audio to batch
- `should_process_batch()` - Check if ready to process
- `get_batch()` - Get batch for processing

### oslo.translation.groq_client.GroqTranslator
Translation via Groq API:
- `translate(text, source, target)` - Sync translation
- `translate_async(text, source, target)` - Async translation

## CLI Usage

```bash
# Basic usage
oslo run

# Specify languages
oslo run --source en --target es

# Verbose output
oslo run --verbose

# Use GPU
oslo run --device cuda

# Disable parallel processing
oslo run --no-parallel
```

## Configuration

Edit `oslo/config.py` or set environment variables:

```python
# Change translation target
TRANSLATION_CONFIG["target_language"] = "es"
TRANSLATION_CONFIG["system_prompt"] = "Translate to Spanish. Output ONLY the translation."

# Adjust parallel workers
PARALLEL_CONFIG["max_workers"] = 4

# Enable/disable features
PREPROCESSING_CONFIG["enable_noise_reduction"] = True
PARALLEL_CONFIG["enable_parallel"] = True
```

## Running Tests

```bash
# All tests
pytest tests/

# Specific test
python tests/test_audio_processor.py
python tests/test_parallel_processor.py
python tests/test_integration.py
```

## Dependencies

Core:
- `torch`, `transformers` - ML framework
- `sounddevice` - Audio capture
- `numpy`, `librosa`, `scipy` - Audio processing
- `silero-vad` - Voice activity detection
- `groq` - Translation API
- `psutil` - System monitoring

## Common Tasks

### Change Translation Language

Edit `oslo/config.py`:
```python
TRANSLATION_CONFIG["source_language"] = "en"
TRANSLATION_CONFIG["target_language"] = "es"
TRANSLATION_CONFIG["system_prompt"] = "Translate to Spanish..."
```

### Use Alternative Backend

```python
from oslo.transcription import MoonshineVoiceTranscriber

transcriber = MoonshineVoiceTranscriber(language="en")
text = transcriber.transcribe(audio_data)
```

### Add New Audio Preprocessing

```python
# In oslo/audio/processor.py, AudioProcessor class
def preprocess_audio(self, audio_data):
    # Add custom preprocessing here
    audio = self._apply_highpass_filter(audio)
    audio = self._apply_noise_reduction(audio)
    # Custom step
    audio = self._custom_filter(audio)
    return audio
```

## File Reference

| File | Purpose |
|------|---------|
| `oslo/cli.py` | CLI entry point, main loop |
| `oslo/config.py` | All configuration |
| `oslo/audio/processor.py` | Audio preprocessing |
| `oslo/transcription/model.py` | Model management |
| `oslo/transcription/moonshine_voice.py` | Alternative backend |
| `oslo/processing/parallel.py` | Parallel processing |
| `oslo/processing/batcher.py` | Audio batching |
| `oslo/translation/groq_client.py` | Translation client |
| `examples/basic_usage.py` | Simple example |
| `examples/pipecat_integration.py` | WebRTC streaming example |

## Performance

Current benchmarks:
- End-to-End Latency: 0.3-1.2s (40% faster than baseline)
- Transcription: 80-300ms
- Translation: 150-600ms

## Troubleshooting

**High latency**: Check audio preprocessing settings, reduce `max_new_tokens`

**Poor accuracy**: Adjust VAD threshold, check microphone quality

**Memory issues**: Reduce `max_workers`, disable parallel processing

**CUDA OOM**: Use CPU mode (`--device cpu`), reduce batch size