import json
import os

from unifiedai import UnifiedAI


def _get_credentials() -> dict[str, dict[str, str]]:
    return {
        "cerebras": {
            "api_key": os.getenv("CEREBRAS_API_KEY", ""),
        },
    }


client = UnifiedAI(credentials_by_provider=_get_credentials())

response = client.chat.completions.create(
    provider="cerebras",
    model="qwen-3-32b",
    messages=[{"role": "user", "content": "What is the capital of France?"}],
)

print(json.dumps(response.model_dump(), indent=2))
