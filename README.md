# OSLO - Open Speech Language Optimizer

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

A high-performance real-time speech translation system. Designed for low-latency, multi-language transcription and translation with intelligent audio processing and parallel optimizations

## Features

- **Streaming Speech Recognition** - Moonshine ASR for efficient speech-to-text
- **Multi-Language Translation** - 100+ languages via Groq API integration
- **Real-Time Audio Processing** - Noise reduction, AGC, high-pass filtering
- **Adaptive Batching** - Smart segment grouping for optimal throughput
- **Parallel Transcription** - Multi-worker processing with resource monitoring
- **Voice Activity Detection** - Silero VAD for robust speech isolation
- **Easy CLI & Library API** - Command-line tool or programmatic access

## Quick Start

### Installation

```bash
git clone https://github.com/s-kunwar/oslo.git
cd oslo
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
export GROQ_API_KEY=your_groq_api_key
```

### Using the CLI

```bash
# Translate English speech to Hindi
oslo run --source en --target hi

# Translate to Spanish
oslo run --source en --target es

# Enable verbose logging
oslo run --source en --target hi --verbose

# Use GPU acceleration
oslo run --source en --target hi --device cuda
```

### Using as a Library

```python
import asyncio
from oslo import AudioProcessor, ModelManager, GroqTranslator

async def translate_speech():
    # Initialize components
    audio_processor = AudioProcessor(sample_rate=16000)
    model, processor = ModelManager().get_model(device="cpu")
    translator = GroqTranslator(api_key="your_key")
    
    # Your audio processing pipeline here
    # See examples/basic_usage.py for complete example

asyncio.run(translate_speech())
```

## Architecture

The system follows a modular pipeline:

```
Audio Input
    ↓
Voice Activity Detection (Silero VAD)
    ↓
Audio Preprocessing (noise reduction, filtering)
    ↓
Adaptive Batching
    ↓
Parallel Transcription (Moonshine ASR)
    ↓
Translation (Groq API)
    ↓
Output
```

## Project Structure

```
oslo/
├── oslo/
│   ├── __init__.py              # Package exports
│   ├── config.py                # Centralized configuration
│   ├── cli.py                   # Command-line interface
│   │
│   ├── audio/
│   │   ├── __init__.py
│   │   └── processor.py         # Audio preprocessing pipeline
│   │
│   ├── transcription/
│   │   ├── __init__.py
│   │   ├── model.py             # Model loading and caching
│   │   └── backends.py          # Alternative transcription backends
│   │
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── parallel.py          # Parallel worker orchestration
│   │   └── batcher.py           # Adaptive audio batching
│   │
│   └── translation/
│       ├── __init__.py
│       └── groq.py              # Groq API translation client
│
├── examples/
│   ├── basic_usage.py           # Simple transcription and translation
│   └── streaming_integration.py  # Real-time streaming example
│
├── tests/
│   ├── test_audio_processor.py
│   ├── test_parallel_processor.py
│   └── test_integration.py
│
├── docs/
│   ├── ARCHITECTURE.md          # System design deep dive
│   ├── CONFIGURATION.md         # Configuration reference
│   └── PERFORMANCE.md           # Performance tuning guide
│
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Package configuration
└── LICENSE                      # MIT License
```

## Configuration

All configuration is centralized in `oslo/config.py`. Key settings:

```python
from oslo.config import AUDIO_CONFIG, TRANSCRIPTION_CONFIG, TRANSLATION_CONFIG

# Audio processing
AUDIO_CONFIG["sample_rate"] = 16000
AUDIO_CONFIG["chunk_size"] = 512

# Model inference
TRANSCRIPTION_CONFIG["device"] = "cuda"  # or "cpu"
TRANSCRIPTION_CONFIG["max_new_tokens"] = 128

# Translation
TRANSLATION_CONFIG["target_language"] = "es"
```

See `docs/CONFIGURATION.md` for all available options.

## API Reference

### AudioProcessor

Preprocess audio with noise reduction, filtering, and feature extraction:

```python
from oslo.audio import AudioProcessor

processor = AudioProcessor(sample_rate=16000)
processed_audio = processor.preprocess_audio(raw_audio)
features = processor.extract_speech_features(audio)
```

### ModelManager

Load and manage transcription models with automatic caching:

```python
from oslo.transcription import ModelManager

manager = ModelManager()
model, processor = manager.get_model(device="cpu")
# Use model for transcription...
manager.cleanup()  # Free resources
```

### ParallelProcessor

Process multiple audio segments concurrently:

```python
from oslo.processing import ParallelProcessor, WorkerConfig

config = WorkerConfig(max_workers=4)
processor = ParallelProcessor(config, transcription_fn)
results = await processor.process_batch(audio_segments)
```

### GroqTranslator

Translate text using Groq's fast API:

```python
from oslo.translation import GroqTranslator

translator = GroqTranslator(api_key="your_key")
translation = await translator.translate_async(
    text="Hello world",
    source_language="en",
    target_language="hi"
)
```

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_audio_processor.py -v

# Run with coverage
pytest --cov=oslo tests/
```

## Performance

Current benchmarks on Intel i7-13960H with 16GB RAM:

- **Transcription latency**: 80-300ms (Moonshine ASR)
- **Translation latency**: 150-600ms (Groq API)
- **End-to-end latency**: 0.3-1.2s (40% reduction from baseline)
- **Throughput**: 4-8 concurrent transcriptions

See `docs/PERFORMANCE.md` for optimization techniques.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes with clear messages
4. Push to the branch and open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Moonshine ASR](https://github.com/usefulsensors/moonshine) - Streaming speech recognition
- [Groq](https://groq.com) - Fast inference API
- [Silero VAD](https://github.com/snakers4/silero-vad) - Voice activity detection
- [Hugging Face Transformers](https://huggingface.co/transformers/) - Model infrastructure
