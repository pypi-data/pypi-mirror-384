#  Test Bedrock UnifiedAI

import json

from unifiedai import UnifiedAI

client = UnifiedAI(provider="bedrock")
resp = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello"}],
    model="qwen.qwen3-32b-v1:0",
)
print(json.dumps(resp.model_dump(), indent=2))
