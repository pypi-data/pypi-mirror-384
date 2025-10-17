from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SDKConfig(BaseModel):
    """Configuration for the Data Ingestion SDK.

    You must provide a full base_url and a bearer token. If either is missing,
    an error will be raised.
    """

    base_url: str = Field(..., description="Base URL of the API, e.g. https://api.example.com")
    token: str = Field(..., description="Bearer token for Authorization header")

    @field_validator("base_url")
    @classmethod
    def _validate_base_url(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("base_url is required")
        return _normalize_base_url(str(v))

    @field_validator("token")
    @classmethod
    def _validate_token(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("token is required")
        return str(v).strip()

    @classmethod
    def from_env(cls) -> "SDKConfig":
        """Load configuration from environment variables.

        Recognized variables:
        - DATA_INGESTION_API_URL or DATA_INGESTION_API_BASE_URL
        - DATA_INGESTION_API_HOST (default: localhost)
        - DATA_INGESTION_API_PORT (default: 8000)
        - DATA_INGESTION_API_SCHEME (default: http)
        - DATA_INGESTION_API_TOKEN
        """

        url = (
            os.environ.get("DATA_INGESTION_API_URL")
            or os.environ.get("DATA_INGESTION_API_BASE_URL")
        )
        if not url or not str(url).strip():
            raise ValueError("DATA_INGESTION_API_URL (or DATA_INGESTION_API_BASE_URL) must be set")

        token = os.environ.get("DATA_INGESTION_API_TOKEN")
        if not token or not str(token).strip():
            raise ValueError("DATA_INGESTION_API_TOKEN must be set")

        return cls(base_url=_normalize_base_url(str(url)), token=str(token).strip())

    @property
    def auth_header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


def _normalize_base_url(url: str) -> str:
    # Strip trailing slashes for consistent joining
    return url.rstrip("/")


