# -*- coding: utf-8 -*-
"""
Parallel processing module for speech transcription.
Optimized for CPU-based inference with memory and thermal constraints.
"""

import asyncio
import os
import time
from typing import List, Optional, Callable
import numpy as np
import torch
from dataclasses import dataclass
import psutil  # For system monitoring


@dataclass
class WorkerConfig:
    """Configuration for parallel processing workers."""
    max_workers: int = 2  # Conservative default for 16GB RAM
    cpu_threshold: float = 0.75  # Reduce workers if CPU > 75%
    memory_threshold: float = 0.80  # Reduce workers if memory > 80%
    batch_size: int = 1  # Process one audio segment at a time per worker
    use_gpu: bool = False  # Default to CPU for memory efficiency
    adaptive_workers: bool = True  # Dynamically adjust worker count
    fallback_sequential: bool = True  # Fallback if parallel fails


class SystemMonitor:
    """Monitors system resources for adaptive processing."""

    def __init__(self):
        self.last_check = 0
        self.cpu_cache = 0.0
        self.memory_cache = 0.0
        self.cache_ttl = 2.0  # Cache results for 2 seconds

    def get_cpu_percent(self) -> float:
        """Get CPU usage percentage (0.0 to 1.0)."""
        current_time = time.time()
        if current_time - self.last_check > self.cache_ttl:
            self.cpu_cache = psutil.cpu_percent(interval=0.1) / 100.0
            self.memory_cache = psutil.virtual_memory().percent / 100.0
            self.last_check = current_time
        return self.cpu_cache

    def get_memory_percent(self) -> float:
        """Get memory usage percentage (0.0 to 1.0)."""
        current_time = time.time()
        if current_time - self.last_check > self.cache_ttl:
            self.cpu_cache = psutil.cpu_percent(interval=0.1) / 100.0
            self.memory_cache = psutil.virtual_memory().percent / 100.0
            self.last_check = current_time
        return self.memory_cache

    def get_available_memory_gb(self) -> float:
        """Get available memory in GB."""
        return psutil.virtual_memory().available / (1024**3)

    def get_temperature_warning(self) -> bool:
        """Check if system might be overheating."""
        # Simple heuristic based on CPU usage and temperature if available
        cpu_usage = self.get_cpu_percent()
        # High CPU usage for extended periods might indicate thermal issues
        return cpu_usage > 0.85


class ParallelProcessor:
    """Manages parallel transcription workers with resource monitoring."""

    def __init__(self, config: WorkerConfig, transcription_func: Callable):
        self.config = config
        self.transcription_func = transcription_func
        self.system_monitor = SystemMonitor()
        self.active_tasks = 0
        self.total_processed = 0
        self.failed_count = 0

        # Initialize semaphore for limiting concurrent workers
        self.semaphore = asyncio.Semaphore(self.config.max_workers)

    async def process_batch(self, audio_segments: List[np.ndarray]) -> List[str]:
        """Process multiple audio segments in parallel with resource monitoring."""
        if not audio_segments:
            return []

        print(f"🔧 Processing {len(audio_segments)} audio segments in parallel")

        # Check system resources before processing
        if not self._check_system_resources():
            print("⚠️  System resources low, falling back to sequential processing")
            return await self._fallback_sequential(audio_segments)

        # Adjust worker count based on system load
        optimal_workers = self._calculate_optimal_workers()

        # Update semaphore if needed
        if optimal_workers != self.semaphore._value:
            print(f"🔄 Adjusting workers: {self.semaphore._value} → {optimal_workers}")
            self.semaphore = asyncio.Semaphore(optimal_workers)

        # Process in parallel with limited concurrency
        tasks = []
        for i, audio in enumerate(audio_segments):
            task = asyncio.create_task(
                self._process_single_with_limit(audio, f"segment_{i}")
            )
            tasks.append(task)

        # Gather results with timeout and error handling
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            transcripts = self._process_results(results)

            self.total_processed += len(audio_segments)
            print(f"✅ Parallel batch completed: {len(transcripts)}/{len(audio_segments)} successful")

            return transcripts

        except Exception as e:
            print(f"❌ Parallel processing error: {e}")
            self.failed_count += 1

            # Fallback to sequential processing
            if self.config.fallback_sequential:
                return await self._fallback_sequential(audio_segments)
            else:
                return []

    async def _process_single_with_limit(self, audio_data: np.ndarray, segment_id: str):
        """Process single audio segment with concurrency limit."""
        async with self.semaphore:
            self.active_tasks += 1
            try:
                start_time = time.time()

                # Check resources again before starting
                if not self._check_system_resources():
                    raise RuntimeError("System resources too low for processing")

                transcript = await self.transcription_func(audio_data)
                processing_time = time.time() - start_time

                print(f"📝 {segment_id}: {processing_time:.2f}s")
                return transcript

            except Exception as e:
                print(f"❌ {segment_id} failed: {e}")
                raise
            finally:
                self.active_tasks -= 1

    def _calculate_optimal_workers(self) -> int:
        """Dynamically adjust worker count based on system load."""
        if not self.config.adaptive_workers:
            return self.config.max_workers

        cpu_load = self.system_monitor.get_cpu_percent()
        memory_usage = self.system_monitor.get_memory_percent()

        base_workers = self.config.max_workers

        # Reduce workers if system is under load
        if cpu_load > self.config.cpu_threshold:
            reduction = max(1, int(base_workers * 0.5))  # Reduce by 50%
            base_workers = max(1, base_workers - reduction)
            print(f"📉 High CPU ({cpu_load:.1%}), reducing to {base_workers} workers")

        if memory_usage > self.config.memory_threshold:
            base_workers = max(1, base_workers - 1)
            print(f"📉 High memory ({memory_usage:.1%}), reducing to {base_workers} workers")

        # Further reduce if system might be overheating
        if self.system_monitor.get_temperature_warning():
            base_workers = max(1, base_workers - 1)
            print(f"🌡️  Thermal warning, reducing to {base_workers} workers")

        return base_workers

    def _check_system_resources(self) -> bool:
        """Check if system has enough resources for processing."""
        cpu_load = self.system_monitor.get_cpu_percent()
        memory_usage = self.system_monitor.get_memory_percent()
        available_memory = self.system_monitor.get_available_memory_gb()

        # Critical thresholds - don't process if system is overloaded
        if cpu_load > 0.95:
            print("🚨 CPU critically high, skipping processing")
            return False

        if memory_usage > 0.95:
            print("🚨 Memory critically high, skipping processing")
            return False

        if available_memory < 1.0:  # Less than 1GB available
            print("🚨 Memory critically low, skipping processing")
            return False

        return True

    async def _fallback_sequential(self, audio_segments: List[np.ndarray]) -> List[str]:
        """Fallback to sequential processing."""
        print("🔄 Falling back to sequential processing")
        transcripts = []

        for i, audio in enumerate(audio_segments):
            try:
                transcript = await self.transcription_func(audio)
                transcripts.append(transcript)
                print(f"📝 Sequential {i}: completed")
            except Exception as e:
                print(f"❌ Sequential {i} failed: {e}")
                transcripts.append("")

        return transcripts

    def _process_results(self, results: List) -> List[str]:
        """Process results from parallel tasks, handling exceptions."""
        transcripts = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Task {i} failed with: {result}")
                transcripts.append("")
            else:
                transcripts.append(result)

        return transcripts

    def get_stats(self) -> dict:
        """Get processing statistics."""
        return {
            "total_processed": self.total_processed,
            "failed_count": self.failed_count,
            "success_rate": (self.total_processed - self.failed_count) / max(1, self.total_processed),
            "active_tasks": self.active_tasks,
            "max_workers": self.config.max_workers,
            "current_workers": self.semaphore._value
        }