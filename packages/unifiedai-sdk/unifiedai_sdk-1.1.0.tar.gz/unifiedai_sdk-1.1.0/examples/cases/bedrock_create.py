import json
import os

import boto3

from unifiedai import BedrockRuntime

client = BedrockRuntime(region_name=os.getenv("AWS_REGION"))

bedrock_client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION"))


response = client.converse(
    modelId="qwen.qwen3-32b-v1:0",
    messages=[{"role": "user", "content": "Write a story about a cat in 100 words"}],
)

print(json.dumps(response, indent=2))
