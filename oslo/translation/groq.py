# -*- coding: utf-8 -*-
"""
Groq API client for real-time translation.

Provides both synchronous and asynchronous interfaces for translating text
across 100+ languages using Groq's high-performance inference API.
"""

import asyncio
import logging
from typing import Optional
from groq import Groq, AsyncGroq

logger = logging.getLogger(__name__)


class GroqTranslator:
    """Translation client using Groq API."""

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.1-8b-instant",
        timeout: float = 30.0,
    ):
        """Initialize Groq translator.

        Args:
            api_key: Groq API key
            model: Model identifier (default: llama-3.1-8b-instant)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.client = Groq(api_key=api_key)
        self.async_client = AsyncGroq(api_key=api_key)

    def translate(
        self,
        text: str,
        source_language: str = "en",
        target_language: str = "hi",
        system_prompt: Optional[str] = None,
    ) -> str:
        """Translate text synchronously.

        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            system_prompt: Custom system prompt

        Returns:
            Translated text
        """
        if not system_prompt:
            system_prompt = (
                f"Translate from {source_language} to {target_language}. "
                "Output ONLY the translation."
            )

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=256,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
            )
            return message.content[0].text.strip()
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text

    async def translate_async(
        self,
        text: str,
        source_language: str = "en",
        target_language: str = "hi",
        system_prompt: Optional[str] = None,
    ) -> str:
        """Translate text asynchronously.

        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            system_prompt: Custom system prompt

        Returns:
            Translated text
        """
        if not system_prompt:
            system_prompt = (
                f"Translate from {source_language} to {target_language}. "
                "Output ONLY the translation."
            )

        try:
            message = await self.async_client.messages.create(
                model=self.model,
                max_tokens=256,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
            )
            return message.content[0].text.strip()
        except Exception as e:
            logger.error(f"Async translation error: {e}")
            return text
