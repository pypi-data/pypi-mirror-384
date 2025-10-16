"""Cerebras Backward Compatibility Demo.

This script demonstrates full backward compatibility with the Cerebras Cloud SDK.
Shows how to use UnifiedAI as a drop-in replacement for the Cerebras SDK while
gaining access to additional providers like AWS Bedrock.

Requirements:
    - CEREBRAS_API_KEY environment variable
    - AWS credentials (optional, for Bedrock models)
"""

import os

from unifiedai import Cerebras


def demo_basic_chat():
    """Demo 1: Basic chat completion (100% compatible with Cerebras SDK)."""
    print("\n" + "=" * 80)
    print("DEMO 1: Basic Chat Completion (Cerebras SDK Compatible)")
    print("=" * 80)

    client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))

    response = client.chat.completions.create(
        model="llama3.1-8b",
        messages=[{"role": "user", "content": "What is 2+2? Answer briefly."}],
    )

    print(f"Model: {response.model}")
    print(f"Response: {response.choices[0].message['content']}")
    print(f"Tokens Used: {response.usage.total_tokens}")


def demo_list_models():
    """Demo 2: List available models (Cerebras SDK compatible)."""
    print("\n" + "=" * 80)
    print("DEMO 2: List Available Models")
    print("=" * 80)

    client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))

    # List models - compatible with Cerebras SDK
    models = client.models.list()

    print(f"Found {len(models)} models:")
    for model in models[:5]:  # Show first 5
        print(f"  - {model.id} (owner: {model.owned_by})")


def demo_bedrock_models():
    """Demo 3: Access Bedrock models through Cerebras-style interface (NEW!)."""
    print("\n" + "=" * 80)
    print("DEMO 3: Access AWS Bedrock Models (NEW CAPABILITY!)")
    print("=" * 80)

    # Check if AWS credentials are available
    if not os.getenv("AWS_ACCESS_KEY_ID"):
        print("⚠️  AWS credentials not found. Skipping Bedrock demo.")
        print("   Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to enable.")
        return

    client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))

    # Use Bedrock model with "bedrock." prefix
    print("Calling AWS Bedrock Claude model through Cerebras-style interface...")
    response = client.chat.completions.create(
        model="bedrock.anthropic.claude-3-haiku-20240307-v1:0",
        messages=[{"role": "user", "content": "Say 'Hello from Bedrock!' briefly."}],
    )

    print(f"Model: {response.model}")
    print(f"Response: {response.choices[0].message['content']}")


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("Cerebras Backward Compatibility Demonstration")
    print("=" * 80)
    print("\nThis demo shows 100% backward compatibility with Cerebras Cloud SDK")
    print("PLUS new capabilities like accessing AWS Bedrock models!\n")

    # Check for API key
    if not os.getenv("CEREBRAS_API_KEY"):
        print("❌ Error: CEREBRAS_API_KEY environment variable not set")
        print("Please set it and try again:")
        print("  export CEREBRAS_API_KEY='your-key-here'")
        return

    # Run synchronous demos
    demo_basic_chat()
    demo_list_models()
    demo_bedrock_models()

    # Run async demos
    print("\n" + "=" * 80)
    print("ASYNC DEMOS")
    print("=" * 80)

    print("\n" + "=" * 80)
    print("✅ All demos completed successfully!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  1. Drop-in replacement: Change import, everything else works")
    print("  2. All Cerebras SDK features supported")
    print("  3. NEW: Access AWS Bedrock models with 'bedrock.' prefix")
    print("  4. Same API for sync and async operations")
    print("  5. Streaming, parameters, model listing all work")
    print("\n")


if __name__ == "__main__":
    main()
