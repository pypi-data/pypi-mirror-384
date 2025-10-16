# Metrics Structure Change Summary

## What Changed

We've simplified the metrics structure to be more transparent and accurate.

### Before (Old Structure)
```python
class ResponseMetrics(BaseModel):
    duration_ms: float | None = None
    ttfb_ms: float | None = None
    round_trip_time_s: float | None = None
    inference_time_s: float | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    input_tokens: int | None = None
    output_tokens_per_sec: float | None = None
    total_tokens_per_sec: float | None = None
```

**Problem:** Many fields were calculated/estimated by the SDK, which could cause confusion. For example:
- `ttfb_ms` was estimated as `queue_time + prompt_time` for Cerebras (not actual TTFB)
- `round_trip_time_s` and `inference_time_s` were calculated, not from provider
- For Bedrock, we had no provider data but still filled in estimated values

### After (New Structure)
```python
class ResponseMetrics(BaseModel):
    # SDK-measured metric (always present)
    duration_ms: float
    
    # Provider-supplied metrics (null if provider doesn't provide them)
    provider_time_info: dict[str, float | int] | None = None
```

**Benefits:**
- ✅ **Transparent**: Clear what's SDK-measured vs provider-supplied
- ✅ **Accurate**: No estimation or calculation of provider metrics
- ✅ **Flexible**: Supports different providers with different metrics
- ✅ **Honest**: If a provider doesn't provide timing info, it's null

## Provider-Specific Metrics

### Cerebras
Provides timing info in the response:
```python
response.metrics = {
    "duration_ms": 2824.47,  # SDK-measured
    "provider_time_info": {  # From Cerebras
        "queue_time": 212.5,
        "prompt_time": 0.7,
        "completion_time": 2254,
        "total_time": 2467,
        "created": 1729089471
    }
}
```

### Bedrock
Currently does not provide detailed timing info:
```python
response.metrics = {
    "duration_ms": 1523.89,  # SDK-measured
    "provider_time_info": {  # From Bedrock (if available)
        "latencyMs": 1500  # May or may not be present
    }
}
```

If Bedrock doesn't send metrics field, it will be:
```python
response.metrics = {
    "duration_ms": 1523.89,
    "provider_time_info": None
}
```

## Migration Guide

### If you were using `duration_ms`
✅ **No change needed** - still available and works the same way

```python
# Still works
print(f"Duration: {response.metrics.duration_ms}ms")
```

### If you were using calculated fields
❌ **Need to update** - these fields no longer exist

**Old code:**
```python
# ❌ These fields no longer exist
print(f"TTFB: {response.metrics.ttfb_ms}ms")
print(f"Inference: {response.metrics.inference_time_s}s")
print(f"Throughput: {response.metrics.total_tokens_per_sec} tokens/sec")
```

**New code - Option 1: Access provider data directly**
```python
# ✅ Access provider-specific metrics
if response.metrics.provider_time_info:
    time_info = response.metrics.provider_time_info
    
    # For Cerebras
    if "completion_time" in time_info:
        print(f"Completion time: {time_info['completion_time']}ms")
    if "queue_time" in time_info:
        print(f"Queue time: {time_info['queue_time']}ms")
```

**New code - Option 2: Calculate your own metrics**
```python
# ✅ Calculate tokens/sec if you need it
if response.usage.total_tokens > 0 and response.metrics.duration_ms > 0:
    tokens_per_sec = (response.usage.total_tokens / response.metrics.duration_ms) * 1000
    print(f"Throughput: {tokens_per_sec:.2f} tokens/sec")
```

**New code - Option 3: Access full raw response**
```python
# ✅ Access complete provider response
if response.provider_metadata and response.provider_metadata.raw:
    raw = response.provider_metadata.raw
    # Access any provider-specific fields here
    print(f"Raw response: {raw}")
```

## Example: Updated Demo Code

### Before
```python
print(f"⚡ TTFB: {response.metrics.ttfb_ms:.2f}ms")
print(f"🏎️  Duration: {response.metrics.duration_ms:.2f}ms")
print(f"📈 Throughput: {response.metrics.total_tokens_per_sec:.2f} tokens/sec")
```

### After
```python
# SDK-measured duration (always available)
print(f"🏎️  Duration: {response.metrics.duration_ms:.2f}ms")

# Provider-specific timing (if available)
if response.metrics.provider_time_info:
    time_info = response.metrics.provider_time_info
    print(f"⚡ Provider timing: {time_info}")
    
    # Cerebras-specific
    if "completion_time" in time_info:
        print(f"   Completion: {time_info['completion_time']}ms")
    if "queue_time" in time_info:
        print(f"   Queue: {time_info['queue_time']}ms")

# Calculate throughput from token counts
tokens = response.usage.total_tokens
duration_s = response.metrics.duration_ms / 1000
throughput = tokens / duration_s if duration_s > 0 else 0
print(f"📈 Throughput: {throughput:.2f} tokens/sec (calculated from token count)")
```

## Why This Change?

1. **Transparency**: Users were confused about how `ttfb_ms` and other metrics were calculated
2. **Accuracy**: Bedrock doesn't provide timing metrics, but we were showing estimated values
3. **Honesty**: If a provider doesn't send data, we shouldn't make it up
4. **Flexibility**: Different providers have different metrics - this structure supports all

## Questions?

- **Q: Can I still get tokens per second?**
  - A: Yes! Calculate it yourself: `tokens / (duration_ms / 1000)`. This is more honest since it's based on client-side measurement.

- **Q: Why not keep the convenience fields?**
  - A: They were confusing users. "Bedrock doesn't send TTFB, how do you calculate it?" We don't. We measure SDK duration only.

- **Q: What about provider_metadata.raw?**
  - A: Still available! It contains the complete raw response from the provider with ALL fields.

