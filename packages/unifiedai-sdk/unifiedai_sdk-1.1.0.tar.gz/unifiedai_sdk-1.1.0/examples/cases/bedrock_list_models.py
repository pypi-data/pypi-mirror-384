import json
import os

from unifiedai import BedrockRuntime

client = BedrockRuntime(region_name=os.getenv("AWS_REGION"))

response = client.list_foundation_models()

# Response is already a dict, should be JSON serializable
print(json.dumps(response, indent=2))
