# 🎯 OSLO - Open Speech Language Optimizer

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

A universal, high-performance real-time speech translation assistant that provides low-latency translation across all languages.

## 🚀 Features

- **Real-time Speech Recognition** - Using Moonshine ASR model
- **Multi-language Translation** - Via Groq API (Llama models)
- **Audio Preprocessing** - Noise reduction, AGC, filtering
- **Parallel Processing** - Multi-worker transcription
- **Adaptive Batching** - Optimal segment grouping
- **CLI Interface** - Easy to use command-line tool

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/oslo.git
cd oslo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set API key
export GROQ_API_KEY=your_api_key_here
```

## 🎯 Quick Start

### Using the CLI

```bash
# Run with defaults (English to Hindi)
oslo run

# Specify languages
oslo run --source en --target es

# Enable verbose output
oslo run --verbose

# Use GPU acceleration
oslo run --device cuda
```

### Using as a Library

```python
import asyncio
from oslo import AudioProcessor, ModelManager, GroqTranslator

async def translate_audio():
    # Initialize components
    audio_processor = AudioProcessor(sample_rate=16000)
    model, processor = ModelManager().get_model(device="cpu")
    translator = GroqTranslator(api_key="your_key")

    # Process and translate
    # ... (see examples/basic_usage.py for full example)

asyncio.run(translate_audio())
```

## 📁 Project Structure

```
oslo/
├── oslo/                       # Main package
│   ├── __init__.py             # Package exports
│   ├── config.py               # Configuration
│   ├── cli.py                  # CLI entry point
│   │
│   ├── audio/                  # Audio processing
│   │   ├── __init__.py
│   │   └── processor.py        # AudioProcessor class
│   │
│   ├── transcription/          # Speech-to-text
│   │   ├── __init__.py
│   │   ├── model.py            # ModelManager
│   │   └── moonshine_voice.py  # Alternative backend
│   │
│   ├── processing/             # Processing pipeline
│   │   ├── __init__.py
│   │   ├── parallel.py         # ParallelProcessor
│   │   └── batcher.py          # AdaptiveBatcher
│   │
│   └── translation/            # Translation
│       ├── __init__.py
│       └── groq_client.py      # Groq API client
│
├── tests/                      # Test suite
├── examples/                   # Example scripts
├── docs/                       # Documentation
├── requirements.txt            # Dependencies
├── pyproject.toml              # Package configuration
└── LICENSE                     # MIT License
```

## 🔧 Configuration

Configuration is centralized in `oslo/config.py`:

```python
from oslo.config import AUDIO_CONFIG, TRANSLATION_CONFIG

# Audio settings
AUDIO_CONFIG["sample_rate"] = 16000
AUDIO_CONFIG["chunk_size"] = 512

# Translation settings
TRANSLATION_CONFIG["source_language"] = "en"
TRANSLATION_CONFIG["target_language"] = "hi"
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test
python tests/test_audio_processor.py

# Run integration tests
python tests/test_integration.py
```

## 📖 Documentation

- [Architecture](docs/ARCHITECTURE.md) - System architecture details
- [Optimizations](docs/OPTIMIZATIONS.md) - Performance improvements
- [Future Features](docs/FUTURE_FEATURES.md) - Roadmap

## 🔗 API Reference

### AudioProcessor

```python
from oslo.audio import AudioProcessor

processor = AudioProcessor(sample_rate=16000)
processed = processor.preprocess_audio(raw_audio)
features = processor.extract_speech_features(audio)
```

### ModelManager

```python
from oslo.transcription import model_manager

model, processor = model_manager.get_model(device="cpu")
# Use model for transcription...
model_manager.cleanup()  # Free memory
```

### ParallelProcessor

```python
from oslo.processing import ParallelProcessor, WorkerConfig

config = WorkerConfig(max_workers=2)
processor = ParallelProcessor(config, transcription_func)
results = await processor.process_batch(audio_segments)
```

### GroqTranslator

```python
from oslo.translation import GroqTranslator

translator = GroqTranslator(api_key="your_key")
translation = await translator.translate_async(
    text="Hello",
    source_language="en",
    target_language="hi"
)
```

## 🤝 Contributing

Contributions are welcome! Please see our documentation for details.

## 📜 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **Moonshine ASR Team** for the excellent streaming speech recognition model
- **Groq** for high-performance AI inference API
- **Silero VAD** for robust voice activity detection
- **Hugging Face** for the transformers library

---

**⭐ If you find OSLO useful, please give it a star on GitHub!**