import json
import os

from unifiedai import Cerebras

client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))

response = client.chat.completions.create(
    model="bedrock.qwen.qwen3-32b-v1:0",
    messages=[{"role": "user", "content": "Write a story about a cat in 100 words"}],
)

# Convert to dict for JSON serialization
response_dict = response.model_dump() if hasattr(response, "model_dump") else dict(response)
print(json.dumps(response_dict, indent=2))
