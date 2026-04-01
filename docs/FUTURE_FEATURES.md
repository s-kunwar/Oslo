# Future Features Roadmap

This document outlines planned features and improvements for OSLO.

## Phase 1: Current Implementation ✅

- [x] Real-time speech capture
- [x] Voice Activity Detection (VAD)
- [x] Audio preprocessing (noise reduction, AGC, filtering)
- [x] Speech-to-text (Moonshine ASR)
- [x] Translation (Groq API)
- [x] Parallel processing
- [x] Adaptive batching

## Phase 2: Multi-Language Translation Models

**Status**: Planned

**Description**: Integrate local translation models for offline support.

**Models to integrate**:
- M2M100 (Meta) - 100 languages
- NLLB-200 (Meta) - 200 languages
- NLLB-200-Distilled - Smaller, faster variant

**Benefits**:
- Offline translation capability
- Lower latency (no API calls)
- No rate limits
- Privacy (data stays local)

**Implementation**:
```python
# Proposed API
from oslo.translation import LocalTranslator

translator = LocalTranslator(model="nllb-200-distilled")
translation = translator.translate(text, source="en", target="hi")
```

## Phase 3: Real-Time Streaming (Pipecat Integration)

**Status**: Experimental (skeleton in `examples/pipecat_integration.py`)

**Description**: Enable real-time audio streaming via WebRTC.

**Components**:
- Daily.co WebRTC transport
- Real-time audio pipeline
- Browser-based client support

**Benefits**:
- Browser-based application
- Lower latency for streaming
- Multi-party audio support

**Requirements**:
- Daily.co account
- WebRTC infrastructure
- Browser client

## Phase 4: Text-to-Speech (Voice Output)

**Status**: Planned

**Description**: Add voice output to hear translations.

**Potential providers**:
- Smallest.ai (Waves API) - Fast, high quality
- ElevenLabs - Voice cloning
- Azure Speech - Enterprise option
- Coqui TTS - Open source

**Implementation**:
```python
# Proposed API
from oslo.tts import VoiceOutput

voice = VoiceOutput(provider="smallest")
await voice.speak(translation, language="hi")
```

## Phase 5: Voice Cloning

**Status**: Research

**Description**: Preserve speaker's voice in translation.

**Approach**:
- Extract voice embeddings from original audio
- Apply voice characteristics to translated speech
- Support multiple voice profiles

**Challenges**:
- Model size and latency
- Quality preservation
- Language cross-compatibility

## Phase 6: Multi-Speaker Support

**Status**: Planned

**Description**: Handle multiple speakers in conversation.

**Components**:
- Speaker diarization
- Per-speaker voice profiles
- Speaker-specific translation context

## Phase 7: Context-Aware Translation

**Status**: Research

**Description**: Maintain conversation context for better translations.

**Components**:
- Conversation history buffer
- Context window management
- Speaker intent detection

## Phase 8: Mobile/Desktop Applications

**Status**: Planned

**Description**: Native applications for major platforms.

**Platforms**:
- iOS (Swift)
- Android (Kotlin)
- Desktop (Electron/Tauri)

## Contributing

Want to help implement these features? See [CONTRIBUTING.md](CONTRIBUTING.md).

## Feature Requests

Have a feature idea? Open an issue on GitHub with the label `enhancement`.