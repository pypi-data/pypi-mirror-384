import os

from unifiedai import UnifiedAI

credentials_by_provider = {
    "cerebras": {"api_key": os.getenv("CEREBRAS_API_KEY", "")},
    "bedrock": {
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID", ""),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        "region_name": os.getenv("AWS_REGION", "us-east-1"),
    },
}

client = UnifiedAI(credentials_by_provider=credentials_by_provider)
resp = client.chat.completions.compare(
    messages=[{"role": "user", "content": "write a story in 5 words"}],
    providers=["cerebras", "bedrock"],
    models={
        "cerebras": "qwen-3-32b",
        "bedrock": "qwen.qwen3-32b-v1:0",
    },
)

# Use Pydantic's model_dump_json() which handles datetime serialization
print(resp.model_dump_json(indent=2))
