import json

import boto3

# Create bedrock-runtime client for Converse API
client = boto3.client("bedrock-runtime", region_name="us-east-1")

# Use Converse API (unified interface across models)
response = client.converse(
    modelId="qwen.qwen3-32b-v1:0",
    messages=[{"role": "user", "content": [{"text": "What is the capital of France?"}]}],
)

print(json.dumps(response, indent=2, default=str))
