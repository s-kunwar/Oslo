# -*- coding: utf-8 -*-
"""
Alternative transcription backends for speech recognition

Currently supports Moonshine ASR streaming models.
Extensible architecture for adding additional backends (Whisper, etc.).
"""

import logging
from typing import Dict, Tuple, Optional
import torch
from transformers import AutoModelForCausalLM, AutoProcessor

logger = logging.getLogger(__name__)


class TranscriptionBackend:
    """Base interface for transcription backends."""

    def transcribe(self, audio: bytes, language: Optional[str] = None) -> str:
        """Transcribe audio to text."""
        raise NotImplementedError


class MoonshineBackend(TranscriptionBackend):
    """Moonshine streaming speech recognition backend."""

    def __init__(
        self,
        model_name: str = "usefulsensors/moonshine-streaming-small",
        device: str = "cpu",
    ):
        """Initialize Moonshine backend.

        Args:
            model_name: HuggingFace model identifier
            device: Compute device ('cpu' or 'cuda')
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.processor = None

    def load(self) -> Tuple[AutoModelForCausalLM, AutoProcessor]:
        """Load model and processor."""
        if self.model is None:
            logger.info(f"Loading {self.model_name} on {self.device}...")
            self.processor = AutoProcessor.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            self.model = self.model.to(self.device)
        return self.model, self.processor

    def unload(self) -> None:
        """Free model memory."""
        if self.model is not None:
            del self.model
            del self.processor
            self.model = None
            self.processor = None
            torch.cuda.empty_cache() if self.device == "cuda" else None
