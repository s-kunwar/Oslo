# -*- coding: utf-8 -*-
"""
Adaptive batching of audio segments for optimal parallel processing.
Groups short speech segments together to improve parallel efficiency.
"""

import numpy as np
import time
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AudioSegment:
    """Represents an audio segment with metadata."""
    data: np.ndarray
    duration: float  # in seconds
    timestamp: float
    priority: int = 1  # Higher priority for shorter segments


class AdaptiveBatcher:
    """Groups audio segments for optimal parallel processing."""

    def __init__(self,
                 max_batch_duration: float = 3.0,
                 max_batch_size: int = 3,
                 batch_timeout: float = 0.1):
        """
        Initialize the audio batcher.

        Args:
            max_batch_duration: Maximum total duration of a batch (seconds)
            max_batch_size: Maximum number of segments in a batch
            batch_timeout: Time to wait for additional segments (seconds)
        """
        self.max_batch_duration = max_batch_duration
        self.max_batch_size = max_batch_size
        self.batch_timeout = batch_timeout
        self.buffer: List[AudioSegment] = []
        self.last_add_time = 0

    def add_segment(self, audio_data: np.ndarray, sample_rate: int = 16000):
        """Add audio segment to buffer."""
        duration = len(audio_data) / sample_rate
        segment = AudioSegment(
            data=audio_data,
            duration=duration,
            timestamp=time.time(),
            priority=self._calculate_priority(duration)
        )
        self.buffer.append(segment)
        self.last_add_time = time.time()

        print(f"📥 Added segment: {duration:.2f}s, priority {segment.priority}")
        print(f"📊 Buffer size: {len(self.buffer)}, total duration: {self.get_total_duration():.2f}s")

    def should_process_batch(self) -> bool:
        """Check if current batch should be processed."""
        if not self.buffer:
            return False

        current_time = time.time()
        time_since_last_add = current_time - self.last_add_time

        # Process if timeout reached or buffer is full
        if time_since_last_add >= self.batch_timeout:
            print("⏰ Batch timeout reached")
            return True

        if len(self.buffer) >= self.max_batch_size:
            print("📦 Batch size limit reached")
            return True

        if self.get_total_duration() >= self.max_batch_duration:
            print("⏱️  Batch duration limit reached")
            return True

        return False

    def get_batch(self) -> List[np.ndarray]:
        """Get optimal batch for parallel processing."""
        if not self.buffer:
            return []

        # Sort by priority (shorter segments first for faster processing)
        self.buffer.sort(key=lambda x: x.priority, reverse=True)

        batch = []
        total_duration = 0
        processed_indices = []

        for i, segment in enumerate(self.buffer):
            if (len(batch) < self.max_batch_size and
                total_duration + segment.duration <= self.max_batch_duration):
                batch.append(segment.data)
                total_duration += segment.duration
                processed_indices.append(i)
            else:
                break

        # Remove processed segments from buffer
        for i in sorted(processed_indices, reverse=True):
            self.buffer.pop(i)

        if batch:
            print(f"📦 Created batch: {len(batch)} segments, {total_duration:.2f}s total")

        return batch

    def get_immediate_batch(self) -> List[np.ndarray]:
        """Get all available segments immediately."""
        if not self.buffer:
            return []

        batch = [segment.data for segment in self.buffer]
        total_duration = self.get_total_duration()

        print(f"⚡ Immediate batch: {len(batch)} segments, {total_duration:.2f}s total")

        self.buffer.clear()
        return batch

    def get_total_duration(self) -> float:
        """Get total duration of all segments in buffer."""
        return sum(segment.duration for segment in self.buffer)

    def get_buffer_info(self) -> dict:
        """Get information about current buffer state."""
        return {
            "segment_count": len(self.buffer),
            "total_duration": self.get_total_duration(),
            "average_duration": self.get_total_duration() / max(1, len(self.buffer)),
            "time_since_last_add": time.time() - self.last_add_time,
            "max_priority": max((s.priority for s in self.buffer), default=0)
        }

    def clear_buffer(self):
        """Clear all segments from buffer."""
        count = len(self.buffer)
        self.buffer.clear()
        print(f"🧹 Cleared {count} segments from buffer")

    def _calculate_priority(self, duration: float) -> int:
        """Calculate processing priority based on segment duration."""
        # Shorter segments get higher priority for faster processing
        if duration < 1.0:
            return 3  # High priority for very short segments
        elif duration < 2.0:
            return 2  # Medium priority
        elif duration < 4.0:
            return 1  # Low priority
        else:
            return 0  # Very low priority for long segments


class SmartBatcher:
    """Enhanced batcher with intelligent grouping strategies."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.conversational_batcher = AdaptiveBatcher(
            max_batch_duration=2.0,  # Shorter for conversational speech
            max_batch_size=4,
            batch_timeout=0.05
        )
        self.monologue_batcher = AdaptiveBatcher(
            max_batch_duration=5.0,  # Longer for monologues
            max_batch_size=2,
            batch_timeout=0.2
        )
        self.current_mode = "conversational"  # Start with conversational mode

    def add_segment(self, audio_data: np.ndarray):
        """Add segment to appropriate batcher based on current mode."""
        duration = len(audio_data) / self.sample_rate

        # Switch mode based on segment characteristics
        if duration > 3.0:
            self.current_mode = "monologue"
            self.monologue_batcher.add_segment(audio_data, self.sample_rate)
        else:
            self.current_mode = "conversational"
            self.conversational_batcher.add_segment(audio_data, self.sample_rate)

    def should_process_batch(self) -> bool:
        """Check if any batcher has a ready batch."""
        return (self.conversational_batcher.should_process_batch() or
                self.monologue_batcher.should_process_batch())

    def get_batch(self) -> List[np.ndarray]:
        """Get batch from the appropriate batcher."""
        # Prefer conversational batcher for faster response
        if self.conversational_batcher.should_process_batch():
            batch = self.conversational_batcher.get_batch()
            if batch:
                print(f"💬 Using conversational batch (mode: {self.current_mode})")
                return batch

        if self.monologue_batcher.should_process_batch():
            batch = self.monologue_batcher.get_batch()
            if batch:
                print(f"🎤 Using monologue batch (mode: {self.current_mode})")
                return batch

        return []

    def get_mode(self) -> str:
        """Get current batching mode."""
        return self.current_mode