"""SDK configuration models (timeouts and secrets)."""

from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class TimeoutConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    connect_timeout: float = Field(5.0)
    read_timeout: float = Field(30.0)
    provider_timeout: float = Field(60.0)
    sdk_timeout: float = Field(90.0)
    comparison_timeout: float = Field(120.0)


class SDKConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    cerebras_key: SecretStr = Field(
        default_factory=lambda: SecretStr(os.getenv("CEREBRAS_API_KEY", ""))
    )
    aws_access_key_id: SecretStr = Field(
        default_factory=lambda: SecretStr(os.getenv("AWS_ACCESS_KEY_ID", ""))
    )
    aws_secret_access_key: SecretStr = Field(
        default_factory=lambda: SecretStr(os.getenv("AWS_SECRET_ACCESS_KEY", ""))
    )
    aws_session_token: SecretStr = Field(
        default_factory=lambda: SecretStr(os.getenv("AWS_SESSION_TOKEN", ""))
    )
    aws_region: str = Field(default_factory=lambda: os.getenv("AWS_REGION", "us-east-1"))

    @classmethod
    def load(cls) -> SDKConfig:
        return cls()
