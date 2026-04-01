# -*- coding: utf-8 -*-
"""
Translation module using Groq API.
Provides fast translation with support for multiple language pairs.
"""

import os
import time
from typing import Optional
from groq import Groq


class GroqTranslator:
    """Groq API client for fast translation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.1-8b-instant",
        max_tokens: int = 256,
        temperature: float = 0.7,
    ):
        """
        Initialize the Groq translator.

        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: Model to use for translation
            max_tokens: Maximum tokens in response
            temperature: Temperature for generation
        """
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Groq API key required. Set GROQ_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Performance tracking
        self.latency_history = []

    def translate(
        self,
        text: str,
        source_language: str = "en",
        target_language: str = "hi",
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Translate text from source to target language.

        Args:
            text: Text to translate
            source_language: Source language code (e.g., "en")
            target_language: Target language code (e.g., "hi")
            system_prompt: Custom system prompt (optional)

        Returns:
            Translated text
        """
        start_time = time.time()

        if not text or not text.strip():
            return ""

        # Build system prompt
        if system_prompt is None:
            system_prompt = self._build_system_prompt(source_language, target_language)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            translation = response.choices[0].message.content.strip()

            # Track performance
            latency = time.time() - start_time
            self.latency_history.append(latency)

            return translation

        except Exception as e:
            print(f"❌ Translation error: {e}")
            return ""

    async def translate_async(
        self,
        text: str,
        source_language: str = "en",
        target_language: str = "hi",
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Async version of translate method.

        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            system_prompt: Custom system prompt (optional)

        Returns:
            Translated text
        """
        # Groq client is synchronous, so we run in thread pool
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.translate,
            text,
            source_language,
            target_language,
            system_prompt
        )

    def _build_system_prompt(
        self,
        source_language: str,
        target_language: str
    ) -> str:
        """Build system prompt for translation."""
        language_names = {
            "en": "English",
            "hi": "Hindi",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "ja": "Japanese",
            "zh": "Chinese",
            "ar": "Arabic",
            "pt": "Portuguese",
            "ru": "Russian",
            "ko": "Korean",
            "it": "Italian",
        }

        source_name = language_names.get(source_language, source_language)
        target_name = language_names.get(target_language, target_language)

        return f"Translate from {source_name} to {target_name}. Output ONLY the translation, no explanations."

    def get_stats(self) -> dict:
        """Get translation statistics."""
        if not self.latency_history:
            return {
                "total_translations": 0,
                "average_latency": 0,
                "min_latency": 0,
                "max_latency": 0,
            }

        return {
            "total_translations": len(self.latency_history),
            "average_latency": sum(self.latency_history) / len(self.latency_history),
            "min_latency": min(self.latency_history),
            "max_latency": max(self.latency_history),
        }


def create_translator(
    api_key: Optional[str] = None,
    model: str = "llama-3.1-8b-instant",
    **kwargs
) -> GroqTranslator:
    """
    Factory function to create a Groq translator.

    Args:
        api_key: Groq API key (optional, uses env var if not provided)
        model: Model to use for translation
        **kwargs: Additional arguments passed to GroqTranslator

    Returns:
        GroqTranslator instance
    """
    return GroqTranslator(api_key=api_key, model=model, **kwargs)