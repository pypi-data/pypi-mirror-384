"""Test response mapper classes."""

from __future__ import annotations

from typing import Any

from unifiedai.adapters.mappers import (
    BedrockResponseMapper,
    BedrockToCerebrasMapper,
    CerebrasResponseMapper,
    CerebrasToBedrockMapper,
)
from unifiedai.models.response import UnifiedChatResponse


class TestCerebrasResponseMapper:
    """Test CerebrasResponseMapper."""

    def test_map_to_unified_success(self) -> None:
        """Test successful mapping from Cerebras to unified format."""
        raw_response = {
            "id": "test-123",
            "object": "chat.completion",
            "created": 1697123456,
            "model": "llama3.1-8b",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello!"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
            "time_info": {
                "queue_time": 0.05,
                "prompt_time": 0.1,
                "completion_time": 0.4,
            },
        }

        result = CerebrasResponseMapper.map_to_unified(
            raw_response, duration_ms=550.0, started_epoch=1697123456, model="llama3.1-8b"
        )

        assert isinstance(result, UnifiedChatResponse)
        assert result.id == "test-123"
        assert result.model == "llama3.1-8b"
        assert result.choices[0].message["content"] == "Hello!"
        assert result.usage.prompt_tokens == 5
        assert result.metrics.duration_ms == 550.0
        assert result.metrics.provider_time_info is not None

    def test_map_to_unified_with_reasoning_extraction(self) -> None:
        """Test mapping with reasoning extraction."""
        raw_response = {
            "id": "test-123",
            "object": "chat.completion",
            "created": 1697123456,
            "model": "llama3.1-8b",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "<think>Internal reasoning</think>Final answer",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }

        result = CerebrasResponseMapper.map_to_unified(
            raw_response,
            duration_ms=550.0,
            started_epoch=1697123456,
            model="llama3.1-8b",
            extract_reasoning=True,
        )

        assert result.choices[0].message["content"] == "Final answer"
        assert result.provider_metadata.raw is not None
        assert result.provider_metadata.raw.get("reasoning") == "Internal reasoning"

    def test_map_to_unified_no_time_info(self) -> None:
        """Test mapping without time_info."""
        raw_response = {
            "id": "test-123",
            "object": "chat.completion",
            "created": 1697123456,
            "model": "llama3.1-8b",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello!"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }

        result = CerebrasResponseMapper.map_to_unified(
            raw_response, duration_ms=550.0, started_epoch=1697123456, model="llama3.1-8b"
        )

        assert result.metrics.provider_time_info is None


class TestBedrockResponseMapper:
    """Test BedrockResponseMapper."""

    def test_map_to_unified_success(self) -> None:
        """Test successful mapping from Bedrock to unified format."""
        raw_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Hello!"}],
                }
            },
            "stopReason": "end_turn",
            "usage": {
                "inputTokens": 12,
                "outputTokens": 10,
                "totalTokens": 22,
            },
            "metrics": {"latencyMs": 450},
        }

        result = BedrockResponseMapper.map_to_unified(
            raw_response, duration_ms=450.0, started_epoch=1697123456, model="meta.llama3-1-8b"
        )

        assert isinstance(result, UnifiedChatResponse)
        assert result.model == "meta.llama3-1-8b"
        assert result.choices[0].message["content"] == "Hello!"
        assert result.usage.prompt_tokens == 12
        assert result.usage.completion_tokens == 10
        assert result.metrics.duration_ms == 450.0

    def test_map_to_unified_no_metrics(self) -> None:
        """Test mapping without metrics field."""
        raw_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Hello!"}],
                }
            },
            "stopReason": "end_turn",
            "usage": {
                "inputTokens": 12,
                "outputTokens": 10,
                "totalTokens": 22,
            },
        }

        result = BedrockResponseMapper.map_to_unified(
            raw_response, duration_ms=450.0, started_epoch=1697123456, model="meta.llama3-1-8b"
        )

        assert result.metrics.provider_time_info is None


class TestBedrockToCerebrasMapper:
    """Test BedrockToCerebrasMapper."""

    def test_map_chat_completion(self) -> None:
        """Test mapping Bedrock response to Cerebras format."""
        bedrock_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Hello from Bedrock!"}],
                }
            },
            "stopReason": "end_turn",
            "usage": {
                "inputTokens": 12,
                "outputTokens": 15,
                "totalTokens": 27,
            },
            "metrics": {"latencyMs": 450},
        }

        result = BedrockToCerebrasMapper.map_chat_completion(bedrock_response)

        assert result["choices"][0]["message"]["content"] == "Hello from Bedrock!"
        assert result["choices"][0]["finish_reason"] == "stop"
        assert result["usage"]["prompt_tokens"] == 12
        assert result["usage"]["completion_tokens"] == 15
        assert result["time_info"] == {"latencyMs": 450}

    def test_map_chat_completion_stop_reasons(self) -> None:
        """Test stop reason mapping."""
        test_cases = [
            ("end_turn", "stop"),
            ("max_tokens", "length"),
            ("content_filtered", "content_filter"),
        ]

        for bedrock_reason, expected_cerebras_reason in test_cases:
            bedrock_response = {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": "Test"}],
                    }
                },
                "stopReason": bedrock_reason,
                "usage": {"inputTokens": 5, "outputTokens": 5, "totalTokens": 10},
            }

            result = BedrockToCerebrasMapper.map_chat_completion(bedrock_response)
            assert result["choices"][0]["finish_reason"] == expected_cerebras_reason

    def test_map_model_list(self) -> None:
        """Test mapping Bedrock model list to Cerebras format."""
        bedrock_response = {
            "modelSummaries": [
                {
                    "modelId": "meta.llama3-1-8b-instruct-v1:0",
                    "modelName": "Llama 3.1 8B Instruct",
                    "providerName": "Meta",
                },
                {
                    "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
                    "modelName": "Claude 3 Sonnet",
                    "providerName": "Anthropic",
                },
            ]
        }

        result = BedrockToCerebrasMapper.map_model_list(bedrock_response)

        assert len(result) == 2
        assert result[0]["id"] == "meta.llama3-1-8b-instruct-v1:0"
        assert result[0]["owned_by"] == "meta"
        assert result[1]["id"] == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert result[1]["owned_by"] == "anthropic"


class TestCerebrasToBedrockMapper:
    """Test CerebrasToBedrockMapper."""

    def test_map_chat_completion(self) -> None:
        """Test mapping Cerebras response to Bedrock format."""
        cerebras_response = {
            "id": "test-123",
            "object": "chat.completion",
            "created": 1697123456,
            "model": "llama3.1-8b",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello from Cerebras!"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            "time_info": {"queue_time": 0.05, "prompt_time": 0.1},
        }

        result = CerebrasToBedrockMapper.map_chat_completion(cerebras_response)

        assert result["output"]["message"]["content"][0]["text"] == "Hello from Cerebras!"
        assert result["stopReason"] == "end_turn"
        assert result["usage"]["inputTokens"] == 10
        assert result["usage"]["outputTokens"] == 20
        assert result["metrics"]["queue_time"] == 0.05

    def test_map_chat_completion_stop_reasons(self) -> None:
        """Test stop reason mapping."""
        test_cases = [
            ("stop", "end_turn"),
            ("length", "max_tokens"),
            ("content_filter", "content_filtered"),
            ("unknown", "end_turn"),  # fallback
        ]

        for cerebras_reason, expected_bedrock_reason in test_cases:
            cerebras_response = {
                "id": "test-123",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "Test"},
                        "finish_reason": cerebras_reason,
                    }
                ],
                "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10},
            }

            result = CerebrasToBedrockMapper.map_chat_completion(cerebras_response)
            assert result["stopReason"] == expected_bedrock_reason

    def test_map_model_list(self) -> None:
        """Test mapping Cerebras model list to Bedrock format."""

        class MockModel:
            def __init__(self, model_id: str) -> None:
                self.id = model_id

            def model_dump(self) -> dict[str, Any]:
                return {"id": self.id}

        class MockModelListResponse:
            def __init__(self) -> None:
                self.data = [MockModel("llama3.1-8b"), MockModel("qwen-3-32b")]

        cerebras_response = MockModelListResponse()
        result = CerebrasToBedrockMapper.map_model_list(cerebras_response)

        assert len(result["modelSummaries"]) == 2
        assert result["modelSummaries"][0]["modelId"] == "cerebras.llama3.1-8b"
        assert result["modelSummaries"][0]["providerName"] == "Cerebras"
        assert result["modelSummaries"][1]["modelId"] == "cerebras.qwen-3-32b"
