"""Example: Using Bedrock compatibility layer.

This example demonstrates how to use the Bedrock-compatible interface,
which provides a boto3-style API while adding support for Cerebras models.
"""

from __future__ import annotations

import os

from unifiedai import BedrockRuntime


def bedrock_example() -> None:
    """Using Bedrock models with Bedrock-compatible API."""
    print("=" * 80)
    print("Bedrock Compatibility Layer - AWS Models")
    print("=" * 80)

    if not os.getenv("AWS_ACCESS_KEY_ID"):
        print("\nSkipped (AWS credentials not configured)")
        return

    # Initialize client (similar to boto3.client('bedrock-runtime'))
    client = BedrockRuntime(region_name="us-east-1")

    # Example 1: Use AWS Bedrock model
    print("\n1. Using AWS Bedrock model:")
    response = client.converse(
        modelId="qwen.qwen3-32b-v1:0",
        messages=[{"role": "user", "content": [{"text": "What is 2+2?"}]}],
        inferenceConfig={"temperature": 0.7, "maxTokens": 100},
    )
    print(f"   Model: {response['output']['message']}")
    print(f"   Response: {response['output']['message']['content'][0]['text']}")
    print(f"   Tokens: {response['usage']['totalTokens']}")
    print(f"   Latency: {response['metrics']['latencyMs']:.2f}ms")


def cerebras_example() -> None:
    """Using Cerebras models with Bedrock-compatible API."""
    print("\n" + "=" * 80)
    print("Bedrock Compatibility Layer - Cerebras Models")
    print("=" * 80)

    if not os.getenv("CEREBRAS_API_KEY"):
        print("\nSkipped (Cerebras API key not configured)")
        return

    # Initialize client with Cerebras key
    client = BedrockRuntime(region_name="us-east-1", cerebras_api_key=os.getenv("CEREBRAS_API_KEY"))

    # Example 1: Use Cerebras model with Bedrock API
    print("\n1. Using Cerebras model with Bedrock-style API:")
    response = client.converse(
        modelId="cerebras.qwen-3-32b",  # ← Cerebras model!
        messages=[{"role": "user", "content": [{"text": "What is 2+2?"}]}],
        inferenceConfig={"temperature": 0.7, "maxTokens": 100},
    )
    print("   Model: cerebras.qwen-3-32b")
    print(f"   Response: {response['output']['message']['content'][0]['text']}")
    print(f"   Tokens: {response['usage']['totalTokens']}")
    print(f"   Latency: {response['metrics']['latencyMs']:.2f}ms")

    # Example 2: Alternative Cerebras model ID format
    print("\n2. Using alternative model ID format:")
    response = client.converse(
        modelId="cerebras/qwen-3-32b",  # ← Also works!
        messages=[{"role": "user", "content": [{"text": "Write a short poem"}]}],
        inferenceConfig={"temperature": 0.8, "maxTokens": 50},
    )
    print(f"   Response:\n{response['output']['message']['content'][0]['text']}")


def migration_guide() -> None:
    """Show migration from boto3 to UnifiedAI."""
    print("\n" + "=" * 80)
    print("Migration Guide: boto3 Bedrock → UnifiedAI")
    print("=" * 80)

    print(
        """
OLD CODE (boto3 Bedrock):
-------------------------
import boto3

client = boto3.client('bedrock-runtime', region_name='us-east-1')
response = client.converse(
    modelId='anthropic.claude-3-haiku-20240307-v1:0',
    messages=[
        {
            "role": "user",
            "content": [{"text": "Hello"}]
        }
    ]
)


NEW CODE (UnifiedAI):
---------------------
from unifiedai import BedrockRuntime  # ← Change import

client = BedrockRuntime(region_name='us-east-1')  # ← Similar initialization
response = client.converse(
    modelId='anthropic.claude-3-haiku-20240307-v1:0',
    messages=[
        {
            "role": "user",
            "content": [{"text": "Hello"}]
        }
    ]
)

# Everything else works exactly the same!
# Plus, you now have access to Cerebras models:
response = client.converse(
    modelId='cerebras.llama3.1-8b',  # ← Cerebras model!
    messages=[
        {
            "role": "user",
            "content": [{"text": "Hello"}]
        }
    ]
)
"""
    )


def main() -> None:
    """Run all examples."""
    # Bedrock examples
    bedrock_example()

    # Cerebras examples
    cerebras_example()

    # Migration guide
    migration_guide()

    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
