# UnifiedAI SDK

OpenAI-compatible Python SDK unifying multiple providers (Cerebras, AWS Bedrock) with Solo and Comparison modes, strict models, and built‑in telemetry.

## Highlights
- **🔄 100% Backwards Compatible**: Drop-in replacements for Cerebras SDK and boto3 Bedrock
- **OpenAI-compatible API**: `UnifiedAI().chat.completions.create(...)` (sync) and `AsyncUnifiedAI` (async)
- **Multi-Provider Support**: Cerebras and AWS Bedrock (extensible architecture)
- **Dual Modes**: Solo execution or side-by-side Comparison
- **Rich Metrics**: Duration, TTFB, tokens/sec, provider-specific timing
- **Observability**: Structured logs, Prometheus metrics, OpenTelemetry tracing hooks
- **Flexible Credentials**: Pass at client construction or use environment variables
- **🌟 Cross-Provider Access**: Use Cerebras models through Bedrock API (and vice versa!)

## 🎯 Three Ways to Use UnifiedAI

UnifiedAI offers **three interfaces** - choose the one that fits your needs:

| Interface | Use Case | Migration Effort |
|-----------|----------|------------------|
| **Cerebras Compat** | Migrating from Cerebras SDK | Change 1 line |
| **Bedrock Compat** | Migrating from boto3 Bedrock | Change 1 line |
| **UnifiedAI Native** | New projects, multi-provider | Learn new API |

---

## 🔷 Interface 1: Cerebras SDK Compatibility

### Drop-in Replacement for Cerebras Cloud SDK

**Migration:** Change **one line** in your code:

```python
# BEFORE (Cerebras SDK)
from cerebras.cloud.sdk import Cerebras

client = Cerebras(api_key="sk-...")
response = client.chat.completions.create(
    model="llama3.1-8b",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.choices[0].message.content)
```

```python
# AFTER (UnifiedAI - 100% compatible!)
from unifiedai import Cerebras  # ← Only change this line!

client = Cerebras(api_key="sk-...")  # Same constructor
response = client.chat.completions.create(  # Same method
    model="llama3.1-8b",  # Same model IDs
    messages=[{"role": "user", "content": "Hello"}]  # Same message format
)
print(response.choices[0].message.content)  # Same response format
```

### ✅ What's Compatible

- **Constructor**: `Cerebras(api_key="...", base_url="...")`
- **Chat Completions**: `client.chat.completions.create(...)`
- **List Models**: `client.models.list()`
- **Streaming**: `stream=True` parameter
- **Parameters**: `temperature`, `max_tokens`, `top_p`, etc.
- **Response Format**: OpenAI-style `choices`, `usage`, `model`
- **Async Support**: `AsyncCerebras` for async/await

### 🌟 NEW: Access Bedrock Models (Cross-Provider!)

```python
from unifiedai import Cerebras

client = Cerebras(api_key="sk-...")

# Use Cerebras models (native)
response = client.chat.completions.create(
    model="llama3.1-8b",
    messages=[{"role": "user", "content": "Hello"}]
)

# Use AWS Bedrock models (NEW!)
response = client.chat.completions.create(
    model="bedrock.anthropic.claude-3-haiku-20240307-v1:0",  # ← Bedrock model!
    messages=[{"role": "user", "content": "Hello from Bedrock!"}]
)
```

### Async Example

```python
from unifiedai import AsyncCerebras

async with AsyncCerebras(api_key="sk-...") as client:
    response = await client.chat.completions.create(
        model="llama3.1-8b",
        messages=[{"role": "user", "content": "Hello"}]
    )
    print(response.choices[0].message.content)
```

---

## 🔶 Interface 2: AWS Bedrock Compatibility

### Drop-in Replacement for boto3 bedrock-runtime

**Migration:** Replace `boto3.client()` with `BedrockRuntime()`:

```python
# BEFORE (boto3 bedrock-runtime)
import boto3

client = boto3.client('bedrock-runtime', region_name='us-east-1')
response = client.converse(
    modelId='anthropic.claude-3-haiku-20240307-v1:0',
    messages=[
        {
            "role": "user",
            "content": [{"text": "Hello"}]
        }
    ]
)
print(response['output']['message']['content'][0]['text'])
```

```python
# AFTER (UnifiedAI - 100% compatible!)
from unifiedai import BedrockRuntime  # ← Replace boto3.client()

client = BedrockRuntime(region_name='us-east-1')  # Same parameters
response = client.converse(  # Same method
    modelId='anthropic.claude-3-haiku-20240307-v1:0',  # Same model IDs
    messages=[  # Same message format
        {
            "role": "user",
            "content": [{"text": "Hello"}]
        }
    ]
)
print(response['output']['message']['content'][0]['text'])  # Same response format
```

### ✅ What's Compatible

- **Constructor**: `BedrockRuntime(region_name="...", aws_access_key_id="...", ...)`
- **Converse API**: `client.converse(modelId="...", messages=[...], inferenceConfig={...})`
- **List Models**: `client.list_foundation_models(byProvider="...")`
- **Message Format**: Bedrock-style with `content` as list of dicts
- **Response Format**: boto3-style dict with `output`, `usage`, `metrics`
- **Inference Config**: `temperature`, `maxTokens`, `topP`, `stopSequences`

### 🌟 NEW: Access Cerebras Models (Cross-Provider!)

```python
from unifiedai import BedrockRuntime

client = BedrockRuntime(
    region_name='us-east-1',
    cerebras_api_key='sk-...'  # Add Cerebras key
)

# Use Bedrock models (native)
response = client.converse(
    modelId='anthropic.claude-3-haiku-20240307-v1:0',
    messages=[
        {"role": "user", "content": [{"text": "Hello"}]}
    ]
)

# Use Cerebras models (NEW!)
response = client.converse(
    modelId='cerebras.llama3.1-8b',  # ← Cerebras model!
    messages=[
        {"role": "user", "content": [{"text": "Hello from Cerebras!"}]}
    ]
)
```

### List Foundation Models (boto3 compatible)

```python
# List all models
response = client.list_foundation_models()
for model in response['modelSummaries']:
    print(f"{model['modelId']} - {model['providerName']}")

# Filter by provider
response = client.list_foundation_models(byProvider="Anthropic")
response = client.list_foundation_models(byProvider="Cerebras")  # NEW!
```

---

## 🔹 Interface 3: UnifiedAI Native (Multi-Provider from Day 1)

For **new projects** or when you want **multi-provider features** from the start:

### Single Provider (Solo Mode)

```python
from unifiedai import UnifiedAI

# Cerebras
client = UnifiedAI(
    provider="cerebras",
    model="llama3.1-8b",
    credentials={"api_key": "sk-..."}
)

# Bedrock
client = UnifiedAI(
    provider="bedrock",
    model="anthropic.claude-3-haiku-20240307-v1:0",
    credentials={
        "aws_access_key_id": "...",
        "aws_secret_access_key": "...",
        "region_name": "us-east-1"
    }
)

# Use
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.choices[0].message["content"])
print(f"Tokens: {response.usage.total_tokens}")
print(f"Duration: {response.metrics.duration_ms:.2f}ms")
```

### Multi-Provider (Comparison Mode)

A/B test two providers simultaneously:

```python
from unifiedai import UnifiedAI

client = UnifiedAI(
    credentials_by_provider={
        "cerebras": {"api_key": "sk-..."},
        "bedrock": {
            "aws_access_key_id": "...",
            "aws_secret_access_key": "...",
            "region_name": "us-east-1"
        }
    }
)

# Compare same model on different providers
result = client.chat.completions.compare(
    providers=["cerebras", "bedrock"],
    models={
        "cerebras": "llama3.1-8b",
        "bedrock": "meta.llama3-1-8b-instruct-v1:0"  # Same model, different ID
    },
    messages=[{"role": "user", "content": "Explain quantum computing"}]
)

# Analyze results
print(f"Winner: {result.winner}")
print(f"Cerebras: {result.provider_a.metrics.duration_ms:.2f}ms")
print(f"Bedrock: {result.provider_b.metrics.duration_ms:.2f}ms")
```

### Async (for FastAPI, web backends)

```python
from unifiedai import AsyncUnifiedAI

async with AsyncUnifiedAI(provider="cerebras", model="llama3.1-8b") as client:
    response = await client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello"}]
    )
```

### Streaming

```python
async with AsyncUnifiedAI(provider="cerebras", model="llama3.1-8b") as client:
    async for chunk in client.chat.completions.stream(
        messages=[{"role": "user", "content": "Write a story"}]
    ):
        print(chunk.delta.get("content", ""), end="")
```

### List Models

```python
# List models from specific provider
models = client.models.list(provider="cerebras")
for model in models:
    print(f"{model.id} - {model.owned_by}")

# List from all configured providers
all_models = client.models.list()
```

---

## 📊 Interface Comparison

| Feature | Cerebras Compat | Bedrock Compat | UnifiedAI Native |
|---------|----------------|----------------|------------------|
| **Migration** | 1 line change | 1 line change | New API |
| **Cerebras Models** | ✅ Native | ✅ With `cerebras.` prefix | ✅ Native |
| **Bedrock Models** | ✅ With `bedrock.` prefix | ✅ Native | ✅ Native |
| **Response Format** | OpenAI-like | boto3 dict | OpenAI-like |
| **Comparison Mode** | ❌ | ❌ | ✅ |
| **Async Support** | ✅ AsyncCerebras | ❌ (sync only) | ✅ AsyncUnifiedAI |
| **Streaming** | ✅ | ❌ (not yet) | ✅ |
| **Rich Metrics** | ✅ Basic | ✅ Basic | ✅ Comprehensive |

**Recommendation:**
- **Migrating existing code?** → Use compatibility layers (Cerebras or Bedrock)
- **New project?** → Use UnifiedAI Native for maximum features
- **Need comparison mode?** → UnifiedAI Native is the only option

---

## 🚀 Quick Start Examples

### Example 1: Migrate from Cerebras SDK (5 seconds)

```python
# Change one line:
# from cerebras.cloud.sdk import Cerebras
from unifiedai import Cerebras

# Everything else stays the same!
```

### Example 2: Migrate from boto3 Bedrock (10 seconds)

```python
# Change one line:
# client = boto3.client('bedrock-runtime', region_name='us-east-1')
from unifiedai import BedrockRuntime
client = BedrockRuntime(region_name='us-east-1')

# Everything else stays the same!
```

### Example 3: New Project with A/B Testing

```python
from unifiedai import AsyncUnifiedAI

async with AsyncUnifiedAI(credentials_by_provider={...}) as client:
    result = await client.chat.completions.compare(
        providers=["cerebras", "bedrock"],
        models={"cerebras": "llama3.1-8b", "bedrock": "meta.llama3-1-8b-instruct-v1:0"},
        messages=[{"role": "user", "content": "Hello"}]
    )
    print(f"Winner: {result.winner}")
```

---

## Install
From PyPI (core):
```bash
pip install unifiedai-sdk
```

Optional extras:
```bash
# AWS Bedrock support (requires boto3)
pip install "unifiedai-sdk[bedrock]"

# HTTP/2 support for httpx
pip install "unifiedai-sdk[http2]"
```

From GitHub (optional):
```bash
pip install git+https://github.com/<your-org-or-user>/<your-repo>.git#subdirectory=cerebras
```

## 🔑 Credentials Setup

### Option 1: Environment Variables (Recommended)

```bash
# Cerebras
export CEREBRAS_API_KEY="sk-..."

# AWS Bedrock
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"  # optional, defaults to us-east-1
```

### Option 2: Pass Directly in Code

**Cerebras Compat:**
```python
from unifiedai import Cerebras
client = Cerebras(api_key="sk-...")
```

**Bedrock Compat:**
```python
from unifiedai import BedrockRuntime
client = BedrockRuntime(
    region_name='us-east-1',
    aws_access_key_id='...',
    aws_secret_access_key='...'
)
```

**UnifiedAI Native (Single Provider):**
```python
from unifiedai import UnifiedAI

# Cerebras
client = UnifiedAI(
    provider="cerebras",
    credentials={"api_key": "sk-..."}
)

# Bedrock
client = UnifiedAI(
    provider="bedrock",
    credentials={
        "aws_access_key_id": "...",
        "aws_secret_access_key": "...",
        "region_name": "us-east-1"
    }
)
```

**UnifiedAI Native (Multi-Provider for Comparison):**
```python
from unifiedai import UnifiedAI

client = UnifiedAI(
    credentials_by_provider={
        "cerebras": {"api_key": "sk-..."},
        "bedrock": {
            "aws_access_key_id": "...",
            "aws_secret_access_key": "...",
            "region_name": "us-east-1"
        }
    }
)
```

**Credential Precedence:**  
Direct credentials > Environment variables > IAM roles (for Bedrock)

## 📚 Examples & Demos

### Comprehensive Demos (Recommended Starting Point)

- **`examples/cerebras_backward_compat_demo.py`** - Full Cerebras SDK compatibility demo
- **`examples/bedrock_backward_compat_demo.py`** - Full AWS Bedrock compatibility demo

Run these to see all features in action!

### Basic Examples

- **`examples/solo_chat.py`** - Simple chat with UnifiedAI
- **`examples/comparison_chat.py`** - A/B testing two providers
- **`examples/streaming.py`** - Streaming responses
- **`examples/list_models.py`** - List available models

### FastAPI Demo (Swagger UI)

```bash
cd apps/chat/backend
pip install -r requirements.txt
uvicorn backend:app --reload --port 8000
# Swagger UI: http://localhost:8000/docs
```

## Supported Models

### Cerebras
- `llama3.1-8b` - Llama 3.1 8B
- `llama3.1-70b` - Llama 3.1 70B
- `qwen-3-32b` - Qwen 3 32B

### AWS Bedrock
- `qwen.qwen3-32b-v1:0` - Qwen 3 32B
- `anthropic.claude-3-haiku-20240307-v1:0` - Claude 3 Haiku (fastest)
- `anthropic.claude-3-sonnet-20240229-v1:0` - Claude 3 Sonnet
- `anthropic.claude-3-5-sonnet-20240620-v1:0` - Claude 3.5 Sonnet
- `meta.llama3-70b-instruct-v1:0` - Llama 3 70B

**Note**: Some Bedrock models require requesting access through the AWS Bedrock console.

## Response Metrics

All responses include comprehensive metrics:
- `duration_ms`: Total SDK round-trip time
- `ttfb_ms`: Time to first byte
- `round_trip_time_s`: Total time in seconds
- `inference_time_s`: Provider-reported inference time
- `output_tokens_per_sec`: Output generation speed
- `total_tokens_per_sec`: Overall token throughput

## 📁 Project Structure

```
cerebras/
├── src/unifiedai/              # SDK implementation
│   ├── _client.py              # Sync UnifiedAI client
│   ├── _async_client.py        # Async UnifiedAI client
│   ├── _cerebras_compat.py     # Cerebras SDK compatibility layer
│   ├── _bedrock_compat.py      # AWS Bedrock compatibility layer
│   ├── adapters/               # Provider implementations
│   │   ├── base.py             # Base adapter with retries, circuit breakers
│   │   ├── cerebras.py         # Cerebras Cloud SDK adapter
│   │   └── bedrock.py          # AWS Bedrock adapter
│   ├── models/                 # Pydantic data models
│   │   ├── request.py          # ChatRequest, Message
│   │   ├── response.py         # UnifiedChatResponse, Usage, Metrics
│   │   ├── comparison.py       # ComparisonResult, ProviderResult
│   │   └── model.py            # Model, ModelList
│   ├── core/                   # Core orchestration
│   │   └── comparison.py       # Comparison mode implementation
│   ├── metrics/                # Observability
│   │   └── emitter.py          # Prometheus metrics
│   └── resilience/             # Resilience patterns
│       └── circuit_breaker.py  # Circuit breaker implementation
├── examples/                   # Usage examples & demos
│   ├── cerebras_backward_compat_demo.py  # ⭐ Cerebras compat demo
│   ├── bedrock_backward_compat_demo.py   # ⭐ Bedrock compat demo
│   ├── solo_chat.py            # Basic usage
│   ├── comparison_chat.py      # A/B testing
│   └── streaming.py            # Streaming responses
├── apps/chat/backend/          # FastAPI demo application
│   ├── backend.py              # REST API with Swagger UI
│   └── requirements.txt        # Backend dependencies
└── tests/                      # Test suite (90% coverage)
    ├── unit/                   # Unit tests
    ├── integration/            # Integration tests with real providers
    └── benchmarks/             # Performance benchmarks
```

---

## 🎯 Why UnifiedAI?

### For Teams Already Using Cerebras or Bedrock

- **Zero Migration Cost**: Change 1 line of code, everything else stays the same
- **Immediate Benefits**: Gain cross-provider capabilities without rewriting your code
- **Risk-Free**: 100% backward compatible, gradual migration path
- **Future-Proof**: Access new providers without changing your interface

### For New Projects

- **Multi-Provider from Day 1**: Don't lock yourself into a single provider
- **Built-in A/B Testing**: Compare providers with `compare()` method
- **Production-Ready**: Retries, circuit breakers, timeouts, metrics
- **OpenAI-Compatible**: Familiar API if you've used OpenAI SDK

### Key Differentiators

✅ **Three interfaces in one SDK** - Use what fits your needs  
✅ **Cross-provider access** - Cerebras models via Bedrock API (and vice versa)  
✅ **Comparison mode** - Side-by-side provider testing built-in  
✅ **Enhanced metrics** - TTFB, tokens/sec, inference time, round-trip time  
✅ **Production resilience** - Circuit breakers, retries, timeouts  
✅ **Full observability** - Structured logs, Prometheus metrics, OpenTelemetry hooks  

---

## 🚀 Getting Started

**1. Install:**
```bash
pip install unifiedai-sdk
```

**2. Choose your interface:**
- Migrating from **Cerebras SDK**? → Start with `examples/cerebras_backward_compat_demo.py`
- Migrating from **boto3 Bedrock**? → Start with `examples/bedrock_backward_compat_demo.py`
- **New project**? → Start with `examples/solo_chat.py` and `examples/comparison_chat.py`

**3. Set credentials:**
```bash
export CEREBRAS_API_KEY="sk-..."
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
```

**4. Start coding!**

---

## 📖 Documentation

- **README** (this file) - Complete usage guide
- **`examples/README.md`** - Detailed example walkthroughs
- **`apps/chat/README.md`** - FastAPI backend setup
- **Inline docstrings** - Every method has comprehensive Google-style docstrings

---

## 🤝 Contributing

Contributions welcome! The SDK follows production-grade best practices:
- ✅ 90%+ test coverage
- ✅ Strict type checking (mypy)
- ✅ Code formatting (ruff, black)
- ✅ Pre-commit hooks
- ✅ Comprehensive CI/CD

---

## License
MIT
