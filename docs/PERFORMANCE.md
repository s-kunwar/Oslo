# Performance Tuning Guide

## Benchmarks

Measured on Intel i7-13960H with 16GB RAM, using Moonshine ASR + Groq API:

| Metric | Value | Notes |
|--------|-------|-------|
| Transcription Latency | 80-300ms | CPU-based, 16kHz audio |
| Translation Latency | 150-600ms | Groq API, depends on network |
| End-to-End Latency | 0.3-1.2s | 40% faster than baseline |
| Throughput | 4-8 concurrent | With parallel processing |
| Memory Usage | 1.2-2.1GB | Depends on batch size |

## Optimization Strategies

### Reduce Transcription Latency

1. **Smaller model**: Use `moonshine-streaming-tiny` instead of `small`
   ```python
   TRANSCRIPTION_CONFIG["model_name"] = "usefulsensors/moonshine-streaming-tiny"
   ```

2. **Faster decoding**: Reduce `max_new_tokens`
   ```python
   TRANSCRIPTION_CONFIG["max_new_tokens"] = 64
   ```

3. **Greedy search**: Already enabled (`num_beams=1`)

4. **GPU acceleration**: Use CUDA if available
   ```python
   TRANSCRIPTION_CONFIG["device"] = "cuda"
   ```

### Improve Throughput

1. **Enable parallel processing**:
   ```python
   PARALLEL_CONFIG["enable_parallel"] = True
   PARALLEL_CONFIG["max_workers"] = 4
   ```

2. **Enable batching**:
   ```python
   BATCHING_CONFIG["enable_batching"] = True
   BATCHING_CONFIG["max_batch_size"] = 4
   ```

3. **Increase batch duration**:
   ```python
   BATCHING_CONFIG["max_batch_duration"] = 5.0
   ```

### Reduce Memory Usage

1. **Single worker**:
   ```python
   PARALLEL_CONFIG["max_workers"] = 1
   ```

2. **Smaller batches**:
   ```python
   BATCHING_CONFIG["max_batch_size"] = 1
   ```

3. **Disable batching**:
   ```python
   BATCHING_CONFIG["enable_batching"] = False
   ```

### Improve Accuracy

1. **Higher temperature** (more variation):
   ```python
   TRANSCRIPTION_CONFIG["temperature"] = 0.9
   ```

2. **Disable preprocessing** (preserve original audio):
   ```python
   PREPROCESSING_CONFIG["enable_noise_reduction"] = False
   PREPROCESSING_CONFIG["enable_highpass_filter"] = False
   ```

3. **Better microphone**: Hardware quality matters most

## Resource Monitoring

Enable detailed logging:

```python
LOGGING_CONFIG["enable_performance_logging"] = True
LOGGING_CONFIG["log_latency"] = True
LOGGING_CONFIG["log_accuracy"] = True
LOGGING_CONFIG["log_audio_quality"] = True
```

Run with verbose output:
```bash
oslo run --verbose
```

## Profiling

Profile audio preprocessing:

```python
import time
from oslo.audio import AudioProcessor

processor = AudioProcessor()
start = time.time()
processed = processor.preprocess_audio(audio)
print(f"Preprocessing took {time.time() - start:.3f}s")
```

## Hardware Requirements

**Minimum**:
- CPU: 4 cores
- RAM: 4GB
- Latency: ~2-3 seconds

**Recommended**:
- CPU: 8+ cores
- RAM: 16GB
- GPU: NVIDIA (CUDA-capable)
- Latency: ~0.3-1.2 seconds

## Common Issues

### High Latency
- Reduce `max_new_tokens`
- Enable GPU acceleration
- Check network latency to Groq API

### Out of Memory
- Reduce `max_workers`
- Disable batching
- Use smaller model

### Poor Accuracy
- Improve audio quality
- Adjust VAD threshold
- Check source language setting
