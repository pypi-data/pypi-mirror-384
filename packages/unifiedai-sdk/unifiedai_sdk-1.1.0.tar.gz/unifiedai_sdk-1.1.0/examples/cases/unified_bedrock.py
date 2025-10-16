import json
import os

from unifiedai import UnifiedAI


def _get_credentials() -> dict[str, dict[str, str]]:
    return {
        "bedrock": {
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID", ""),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            "region_name": os.getenv("AWS_REGION", "us-east-1"),
        },
    }


client = UnifiedAI(credentials_by_provider=_get_credentials())

response = client.chat.completions.create(
    provider="bedrock",
    messages=[{"role": "user", "content": "What is the capital of France?"}],
    model="qwen.qwen3-32b-v1:0",
)

print(json.dumps(response.model_dump(), indent=2))
