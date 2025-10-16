import json
import os

from unifiedai import UnifiedAI


def _get_credentials() -> dict[str, dict[str, str]]:
    """Build credentials dict for all providers from environment variables.

    Returns:
        dict mapping provider names to their credential dicts.
    """
    return {
        "cerebras": {
            "api_key": os.getenv("CEREBRAS_API_KEY", ""),
        },
        "bedrock": {
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID", ""),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            "aws_session_token": os.getenv("AWS_SESSION_TOKEN", ""),
            "region_name": os.getenv("AWS_REGION", "us-east-1"),
        },
    }


client = UnifiedAI(credentials_by_provider=_get_credentials())

response = client.chat.completions.compare(
    messages=[{"role": "user", "content": "Write a story about a cat in 100 words"}],
    providers=["cerebras", "bedrock"],
    models={"cerebras": "qwen-3-32b", "bedrock": "qwen.qwen3-32b-v1:0"},
)

# Convert ComparisonResult to dict for JSON serialization
response_dict = response.model_dump() if hasattr(response, "model_dump") else dict(response)
print(json.dumps(response_dict, indent=2, default=str))
