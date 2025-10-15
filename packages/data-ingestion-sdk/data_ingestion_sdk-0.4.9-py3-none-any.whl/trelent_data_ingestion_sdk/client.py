from __future__ import annotations

from typing import Optional, Union
from uuid import UUID

import httpx

from .config import SDKConfig
from .models import (
    HealthzResponse,
    JobInput,
    JobStatusResponse,
    ProcessResponse,
)


class DataIngestionClient:
    def __init__(self, config: Optional[SDKConfig] = None, timeout: Optional[float] = 10.0):
        if config is None:
            config = SDKConfig.from_env()
        # Defensive checks to ensure required fields are present
        if not getattr(config, "base_url", None):
            raise ValueError("SDKConfig.base_url is required")
        if not getattr(config, "token", None):
            raise ValueError("SDKConfig.token is required")
        self._config = config
        self._client = httpx.Client(
            base_url=config.base_url,
            headers={"Content-Type": "application/json", **config.auth_header},
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "DataIngestionClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # ---- API methods ----

    def healthz(self) -> HealthzResponse:
        resp = self._client.get("/healthz")
        resp.raise_for_status()
        return HealthzResponse.model_validate(resp.json())

    def submit_job(self, payload: JobInput) -> ProcessResponse:
        resp = self._client.post("/v1/jobs", json=payload.model_dump(mode="json", by_alias=True, exclude_none=True))
        resp.raise_for_status()
        return ProcessResponse.model_validate(resp.json())

    def get_job_status(self, job_id: Union[UUID, str], *, include_markdown: bool = False, timeout: Optional[float] = None) -> JobStatusResponse:
        jid = str(job_id)
        resp = self._client.get(f"/v1/jobs/{jid}", params={"include_markdown": str(bool(include_markdown)).lower()}, timeout=timeout)
        resp.raise_for_status()
        return JobStatusResponse.model_validate(resp.json())


