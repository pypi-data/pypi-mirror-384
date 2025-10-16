import json
import os

from unifiedai import BedrockRuntime

# Initialize Bedrock client with Cerebras credentials
client = BedrockRuntime(
    region_name="us-east-1",
    cerebras_api_key=os.getenv("CEREBRAS_API_KEY"),
)

# Call Cerebras model through Bedrock-compatible interface
response = client.converse(
    modelId="cerebras.qwen-3-32b",  # cerebras. prefix routes to Cerebras
    messages=[{"role": "user", "content": [{"text": "Write a story about a dog in 100 words"}]}],
    inferenceConfig={"temperature": 0.7, "maxTokens": 200},
)

print(json.dumps(response, indent=2))
