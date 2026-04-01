# -*- coding: utf-8 -*-
"""
Manages transcription model with memory optimization for CPU-based inference.
Singleton pattern ensures model is loaded only once.
"""

import torch
from transformers import MoonshineStreamingForConditionalGeneration, AutoProcessor
import gc


class ModelManager:
    """Singleton model manager for memory efficiency."""

    _instance = None
    _model = None
    _processor = None
    _device = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance

    def get_model(self, device="cpu", use_quantization=True):
        """Get or load model with optimization for the specified device."""
        if self._model is None or self._device != device:
            self._load_model(device, use_quantization)
        return self._model, self._processor

    def _load_model(self, device="cpu", use_quantization=True):
        """Load model with CPU optimization and memory efficiency."""
        print(f"🚀 Loading model for {device} with quantization={use_quantization}")

        # Clear any existing model from memory
        if self._model is not None:
            del self._model
            del self._processor
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        # Load processor
        self._processor = AutoProcessor.from_pretrained(
            "usefulsensors/moonshine-streaming-small"
        )

        # Determine optimal torch dtype
        if device == "cuda" and torch.cuda.is_available():
            torch_dtype = torch.float16  # Use FP16 for GPU
        else:
            torch_dtype = torch.float32  # Use FP32 for CPU stability
            device = "cpu"  # Force CPU if CUDA not available

        # Load model with memory optimization
        self._model = MoonshineStreamingForConditionalGeneration.from_pretrained(
            "usefulsensors/moonshine-streaming-small",
            torch_dtype=torch_dtype,
            device_map=device,
            low_cpu_mem_usage=True,  # Critical for memory efficiency
            attn_implementation="sdpa" if device != "cpu" else "eager"
        )

        # Apply quantization for CPU if requested and available
        if use_quantization and device == "cpu":
            try:
                # Simple quantization by converting to FP16
                self._model = self._model.half()
                print("✅ Applied FP16 quantization for CPU inference")
            except Exception as e:
                print(f"⚠️  Quantization failed: {e}, using FP32")

        self._model.eval()
        self._device = device

        # Print memory usage
        if device == "cpu":
            model_size = sum(p.numel() * p.element_size() for p in self._model.parameters())
            print(f"📊 Model size: {model_size / (1024**2):.1f} MB")

        print("✅ Model loaded successfully")

    def cleanup(self):
        """Clean up model from memory."""
        if self._model is not None:
            del self._model
            del self._processor
            self._model = None
            self._processor = None
            self._device = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print("🧹 Model cleaned up from memory")


# Global instance for easy access
model_manager = ModelManager()