# -*- coding: utf-8 -*-
"""
Alternative transcription backend using moonshine_voice package.

This module provides a simpler transcription interface using the
moonshine_voice library instead of transformers directly.

Note: This requires the moonshine_voice package to be installed.
Install with: pip install moonshine-voice
"""

from typing import Optional, Tuple
import numpy as np


class MoonshineVoiceTranscriber:
    """
    Transcription backend using moonshine_voice package.

    This is an alternative to the transformers-based ModelManager.
    It provides a simpler API but requires the moonshine_voice package.
    """

    def __init__(
        self,
        language: str = "en",
        model_path: Optional[str] = None,
        model_arch: Optional[str] = None,
    ):
        """
        Initialize the MoonshineVoice transcriber.

        Args:
            language: Language code for model selection (default: "en")
            model_path: Path to specific model (optional)
            model_arch: Model architecture (optional)
        """
        try:
            import moonshine_voice
            self._moonshine_voice = moonshine_voice
        except ImportError:
            raise ImportError(
                "moonshine_voice package not installed. "
                "Install with: pip install moonshine-voice"
            )

        # Get model for language
        if model_path and model_arch:
            self.model_path = model_path
            self.model_arch = model_arch
        else:
            self.model_path, self.model_arch = moonshine_voice.get_model_for_language(language)

        # Initialize transcriber
        self.transcriber = moonshine_voice.Transcriber(
            model_path=self.model_path,
            model_arch=self.model_arch
        )

        self._is_loaded = True

    def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
    ) -> str:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate of audio (default: 16000)

        Returns:
            Transcribed text
        """
        if not self._is_loaded:
            raise RuntimeError("Transcriber not loaded. Call load() first.")

        try:
            # Convert to list if needed
            audio_list = audio_data.tolist() if hasattr(audio_data, 'tolist') else list(audio_data)

            # Transcribe without streaming (batch mode)
            result = self.transcriber.transcribe_without_streaming(
                audio_list,
                sample_rate=sample_rate
            )

            # Extract text from result
            if result and result.lines:
                text = " ".join(line.text for line in result.lines)
                return text.strip()

            return ""

        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return ""

    def transcribe_streaming(
        self,
        audio_chunks,
        sample_rate: int = 16000,
    ):
        """
        Streaming transcription (generator).

        Args:
            audio_chunks: Iterator of audio chunks
            sample_rate: Sample rate of audio

        Yields:
            Partial transcription results
        """
        if not self._is_loaded:
            raise RuntimeError("Transcriber not loaded. Call load() first.")

        # Note: moonshine_voice streaming support may vary
        # This is a placeholder for streaming interface
        for chunk in audio_chunks:
            text = self.transcribe(chunk, sample_rate)
            if text:
                yield text

    def cleanup(self):
        """Clean up resources."""
        if self.transcriber is not None:
            del self.transcriber
            self.transcriber = None
            self._is_loaded = False


def create_transcriber(
    language: str = "en",
    **kwargs
) -> MoonshineVoiceTranscriber:
    """
    Factory function to create a MoonshineVoice transcriber.

    Args:
        language: Language code for model selection
        **kwargs: Additional arguments passed to MoonshineVoiceTranscriber

    Returns:
        MoonshineVoiceTranscriber instance
    """
    return MoonshineVoiceTranscriber(language=language, **kwargs)


# Supported languages
SUPPORTED_LANGUAGES = [
    "en",  # English
    "es",  # Spanish
    "fr",  # French
    "de",  # German
    "zh",  # Chinese
    "ja",  # Japanese
    "ko",  # Korean
    "pt",  # Portuguese
    "ru",  # Russian
    "ar",  # Arabic
    "hi",  # Hindi
    "it",  # Italian
]