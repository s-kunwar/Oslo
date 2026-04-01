# -*- coding: utf-8 -*-
"""
Audio preprocessing module for speech transcription optimization.
Implements noise reduction, filtering, and audio quality improvements.
"""

import numpy as np
import librosa
import noisereduce as nr
from scipy import signal


class AudioProcessor:
    """Audio preprocessing pipeline for speech transcription."""

    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate

        # High-pass filter parameters (remove low-frequency noise)
        self.highpass_cutoff = 80  # Hz
        self.highpass_order = 4

        # Noise reduction parameters
        self.noise_reduction_stationary = True
        self.noise_reduction_prop_decrease = 0.95

        # AGC (Automatic Gain Control) parameters
        self.agc_target_level = -20  # dBFS
        self.agc_attack_time = 0.01  # seconds
        self.agc_release_time = 0.1  # seconds

        # Initialize filters
        self._init_filters()

    def _init_filters(self):
        """Initialize digital filters."""
        # High-pass filter coefficients
        nyquist = self.sample_rate / 2
        cutoff_normalized = self.highpass_cutoff / nyquist
        self.b, self.a = signal.butter(
            self.highpass_order,
            cutoff_normalized,
            btype='high'
        )

        # Initialize AGC state
        self.agc_gain = 1.0
        self.agc_prev_level = 0.0

    def preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Apply complete audio preprocessing pipeline.

        Args:
            audio_data: Raw audio data as numpy array

        Returns:
            Processed audio data
        """
        if len(audio_data) == 0:
            return audio_data

        # 1. Normalize audio to float32
        audio_processed = audio_data.astype(np.float32)

        # 2. Apply high-pass filter (remove low-frequency noise)
        audio_processed = self._apply_highpass_filter(audio_processed)

        # 3. Apply noise reduction
        audio_processed = self._apply_noise_reduction(audio_processed)

        # 4. Apply AGC (Automatic Gain Control)
        audio_processed = self._apply_agc(audio_processed)

        # 5. Normalize to target level
        audio_processed = self._normalize_audio(audio_processed)

        return audio_processed

    def _apply_highpass_filter(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply high-pass filter to remove low-frequency noise."""
        if len(audio_data) < self.highpass_order * 3:
            return audio_data

        # Apply filter with zero-phase filtering
        audio_filtered = signal.filtfilt(self.b, self.a, audio_data)
        return audio_filtered

    def _apply_noise_reduction(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply spectral noise reduction."""
        if len(audio_data) < 512:  # Minimum length for noise reduction
            return audio_data

        try:
            # Use stationary noise reduction for speech
            audio_reduced = nr.reduce_noise(
                y=audio_data,
                sr=self.sample_rate,
                stationary=self.noise_reduction_stationary,
                prop_decrease=self.noise_reduction_prop_decrease
            )
            return audio_reduced
        except Exception as e:
            print(f"Noise reduction failed: {e}")
            return audio_data

    def _apply_agc(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply simple Automatic Gain Control."""
        if len(audio_data) == 0:
            return audio_data

        # Calculate current RMS level
        rms_level = np.sqrt(np.mean(audio_data ** 2))
        if rms_level == 0:
            return audio_data

        # Convert to dBFS
        current_level_db = 20 * np.log10(rms_level)

        # Calculate target gain
        target_gain = 10 ** ((self.agc_target_level - current_level_db) / 20)

        # Smooth gain changes
        alpha_attack = np.exp(-1.0 / (self.agc_attack_time * self.sample_rate))
        alpha_release = np.exp(-1.0 / (self.agc_release_time * self.sample_rate))

        if target_gain > self.agc_gain:
            alpha = alpha_attack
        else:
            alpha = alpha_release

        self.agc_gain = alpha * self.agc_gain + (1 - alpha) * target_gain

        # Apply gain
        audio_agc = audio_data * self.agc_gain

        # Prevent clipping
        max_val = np.max(np.abs(audio_agc))
        if max_val > 1.0:
            audio_agc = audio_agc / max_val

        return audio_agc

    def _normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Normalize audio to optimal level for speech recognition."""
        if len(audio_data) == 0:
            return audio_data

        # Target RMS level for speech (around -20 dBFS)
        target_rms = 0.1

        # Calculate current RMS
        rms_current = np.sqrt(np.mean(audio_data ** 2))
        if rms_current == 0:
            return audio_data

        # Apply normalization
        gain = target_rms / rms_current
        audio_normalized = audio_data * gain

        # Soft clipping to prevent distortion
        audio_normalized = np.tanh(audio_normalized * 0.8) / 0.8

        return audio_normalized

    def extract_speech_features(self, audio_data: np.ndarray) -> dict:
        """Extract features for speech quality assessment."""
        if len(audio_data) == 0:
            return {}

        features = {}

        # RMS level
        features['rms'] = np.sqrt(np.mean(audio_data ** 2))

        # Spectral centroid (brightness)
        spectral_centroid = librosa.feature.spectral_centroid(
            y=audio_data, sr=self.sample_rate
        )[0]
        features['spectral_centroid_mean'] = np.mean(spectral_centroid)

        # Zero-crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio_data)[0]
        features['zero_crossing_rate'] = np.mean(zcr)

        # Signal-to-noise ratio estimate
        features['snr_estimate'] = self._estimate_snr(audio_data)

        return features

    def _estimate_snr(self, audio_data: np.ndarray) -> float:
        """Estimate signal-to-noise ratio."""
        if len(audio_data) < 1024:
            return 0.0

        try:
            # Simple SNR estimation using spectral subtraction
            stft = librosa.stft(audio_data, n_fft=512)
            magnitude = np.abs(stft)

            # Estimate noise floor from first few frames
            noise_estimate = np.median(magnitude[:, :10], axis=1)

            # Calculate SNR
            signal_power = np.mean(magnitude ** 2)
            noise_power = np.mean(noise_estimate ** 2)

            if noise_power == 0:
                return float('inf')

            snr_db = 10 * np.log10(signal_power / noise_power)
            return max(snr_db, 0)
        except:
            return 0.0


def create_audio_processor(sample_rate=16000):
    """Factory function to create audio processor."""
    return AudioProcessor(sample_rate)