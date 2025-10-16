"""Pydantic models for model listing and metadata.

This module defines the schema for model objects and model list responses,
following the OpenAI API specification for models.list() endpoint.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Model(BaseModel):
    """Represents a single model object.

    Attributes:
        id: The model identifier (e.g., "llama3.1-8b", "qwen.qwen3-32b-v1:0").
        object: Always "model" for individual model objects.
        created: Unix timestamp of when the model was created/registered.
        owned_by: Organization that owns/provides the model (e.g., "cerebras", "aws").
    """

    model_config = ConfigDict(strict=True)

    id: str = Field(..., description="Model identifier")
    object: Literal["model"] = Field("model", description="Object type")
    created: int = Field(..., description="Unix timestamp")
    owned_by: str = Field(..., description="Organization owning the model")


class ModelList(BaseModel):
    """List of available models from one or more providers.

    Attributes:
        object: Always "list" for list responses.
        data: Array of Model objects.
    """

    model_config = ConfigDict(strict=True)

    object: Literal["list"] = Field("list", description="Object type for list responses")
    data: list[Model] = Field(..., description="Array of model objects")
