"""Test Bedrock SDK compatibility layer."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from unifiedai import BedrockRuntime


class TestBedrockCompatRuntime:
    """Test BedrockRuntime compatibility client."""

    def test_bedrock_runtime_initialization(self) -> None:
        """Test BedrockRuntime client initialization."""
        client = BedrockRuntime(region_name="us-east-1")
        assert client._bedrock_credentials["region_name"] == "us-east-1"

    def test_bedrock_runtime_with_credentials(self) -> None:
        """Test BedrockRuntime with explicit credentials."""
        client = BedrockRuntime(
            region_name="us-west-2",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
        )
        assert client._bedrock_credentials["region_name"] == "us-west-2"
        assert client._bedrock_credentials["aws_access_key_id"] == "test-key"

    def test_bedrock_converse(self) -> None:
        """Test converse with Bedrock model."""
        with patch("unifiedai._bedrock_compat.get_adapter") as mock_get_adapter:
            mock_adapter = AsyncMock()
            bedrock_response = {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": "Hello from Bedrock!"}],
                    }
                },
                "stopReason": "end_turn",
                "usage": {"inputTokens": 5, "outputTokens": 10, "totalTokens": 15},
            }
            mock_adapter.invoke_raw.return_value = bedrock_response
            mock_adapter.provider_name = "bedrock"
            mock_get_adapter.return_value = mock_adapter

            client = BedrockRuntime(region_name="us-east-1")
            response = client.converse(
                modelId="meta.llama3-1-8b-instruct-v1:0",
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": "Hello"}],
                    }
                ],
            )

            assert response["output"]["message"]["content"][0]["text"] == "Hello from Bedrock!"

    def test_bedrock_list_foundation_models(self) -> None:
        """Test listing foundation models."""
        with patch("unifiedai._bedrock_compat.get_adapter") as mock_get_adapter:
            mock_adapter = AsyncMock()
            bedrock_response = {
                "modelSummaries": [
                    {
                        "modelId": "meta.llama3-1-8b-instruct-v1:0",
                        "modelName": "Llama 3.1 8B",
                        "providerName": "Meta",
                    },
                ]
            }
            mock_adapter.list_models_raw.return_value = bedrock_response
            mock_get_adapter.return_value = mock_adapter

            client = BedrockRuntime(region_name="us-east-1")
            response = client.list_foundation_models()

            assert "modelSummaries" in response
            assert len(response["modelSummaries"]) == 1

    def test_bedrock_list_foundation_models_with_filter(self) -> None:
        """Test listing models with provider filter."""
        with patch("unifiedai._bedrock_compat.get_adapter") as mock_get_adapter:
            mock_adapter = AsyncMock()
            bedrock_response = {
                "modelSummaries": [
                    {
                        "modelId": "meta.llama3-1-8b-instruct-v1:0",
                        "modelName": "Llama 3.1 8B",
                        "providerName": "Meta",
                    },
                    {
                        "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
                        "modelName": "Claude 3 Sonnet",
                        "providerName": "Anthropic",
                    },
                ]
            }
            mock_adapter.list_models_raw.return_value = bedrock_response
            mock_get_adapter.return_value = mock_adapter

            client = BedrockRuntime(region_name="us-east-1")
            response = client.list_foundation_models(byProvider="Meta")

            assert "modelSummaries" in response
            # Should only include Meta models
            for model in response["modelSummaries"]:
                assert model["providerName"] == "Meta"
