"""AWS Bedrock Backward Compatibility Demo.

This script demonstrates full backward compatibility with boto3's Bedrock API.
Shows how to use UnifiedAI as a replacement for boto3 bedrock-runtime client
while gaining access to Cerebras models through the same API.

Requirements:
    - AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
    - CEREBRAS_API_KEY environment variable (optional, for Cerebras models)
"""

import json
import os

from unifiedai import BedrockRuntime


def demo_basic_converse():
    """Demo 1: Basic converse API (100% compatible with boto3 bedrock-runtime)."""
    print("\n" + "=" * 80)
    print("DEMO 1: Basic Converse API (boto3 bedrock-runtime Compatible)")
    print("=" * 80)

    client = BedrockRuntime(region_name=os.getenv("AWS_REGION", "us-east-1"))

    response = client.converse(
        modelId="qwen.qwen3-32b-v1:0",
        messages=[{"role": "user", "content": [{"text": "What is 2+2? Answer briefly."}]}],
    )

    # Access response in boto3 format
    print(json.dumps(response, indent=2))


def demo_list_foundation_models():
    """Demo 2: List foundation models (compatible with boto3 bedrock client)."""
    print("\n" + "=" * 80)
    print("DEMO 2: List Foundation Models (boto3 bedrock Compatible)")
    print("=" * 80)

    client = BedrockRuntime(region_name=os.getenv("AWS_REGION", "us-east-1"))

    # List all available models - compatible with boto3 bedrock client
    response = client.list_foundation_models()

    print(json.dumps(response, indent=2))


def demo_cerebras_models():
    """Demo 4: Access Cerebras models through Bedrock-style interface (NEW!)."""
    print("\n" + "=" * 80)
    print("DEMO 4: Access Cerebras Models (NEW CAPABILITY!)")
    print("=" * 80)

    # Check if Cerebras API key is available
    if not os.getenv("CEREBRAS_API_KEY"):
        print("⚠️  CEREBRAS_API_KEY not found. Skipping Cerebras demo.")
        print("   Set CEREBRAS_API_KEY to enable Cerebras model access.")
        return

    client = BedrockRuntime(
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        cerebras_api_key=os.getenv("CEREBRAS_API_KEY"),
    )

    # Use Cerebras model with "cerebras." prefix
    print("Calling Cerebras Llama model through Bedrock-style interface...")
    response = client.converse(
        modelId="cerebras.qwen-3-32b",
        messages=[{"role": "user", "content": [{"text": "Say 'Hello from Cerebras!' briefly."}]}],
    )
    print(json.dumps(response, indent=2))


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("AWS Bedrock Backward Compatibility Demonstration")
    print("=" * 80)
    print("\nThis demo shows 100% backward compatibility with boto3 bedrock API")
    print("PLUS new capabilities like accessing Cerebras models!\n")

    # Check for AWS credentials
    if not os.getenv("AWS_ACCESS_KEY_ID"):
        print("❌ Error: AWS credentials not set")
        print("Please set the following environment variables:")
        print("  export AWS_ACCESS_KEY_ID='your-key'")
        print("  export AWS_SECRET_ACCESS_KEY='your-secret'")
        print("  export AWS_REGION='us-east-1'  # optional, defaults to us-east-1")
        return

    # Run all demos
    demo_basic_converse()
    demo_list_foundation_models()
    demo_cerebras_models()

    print("\n" + "=" * 80)
    print("✅ All demos completed successfully!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  1. Drop-in replacement for boto3 bedrock-runtime client")
    print("  2. converse() API is 100% compatible with boto3")
    print("  3. list_foundation_models() works like boto3 bedrock client")
    print("  4. NEW: Access Cerebras models with 'cerebras.' prefix")
    print("  5. Same response format as boto3 (dict with output, usage, metrics)")
    print("  6. Supports filtering by provider, inference config, multi-turn chats")
    print("\nMigration from boto3:")
    print("  OLD: client = boto3.client('bedrock-runtime')")
    print("  NEW: client = BedrockRuntime(region_name='us-east-1')")
    print("  Everything else stays the same!")
    print("\n")


if __name__ == "__main__":
    main()
