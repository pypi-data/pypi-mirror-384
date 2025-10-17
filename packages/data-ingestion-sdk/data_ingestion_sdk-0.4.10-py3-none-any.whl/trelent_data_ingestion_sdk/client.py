from __future__ import annotations

from typing import Optional, Union
from uuid import UUID

import requests

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
        self._client = requests.Session()
        self._client.headers.update({"Content-Type": "application/json", **config.auth_header})
        self._timeout = timeout

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "DataIngestionClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # ---- API methods ----

    def _url(self, path: str) -> str:
        # Join base URL with a path that may or may not start with "/"
        if not path.startswith("/"):
            path = "/" + path
        return f"{self._config.base_url}{path}"

    def healthz(self) -> HealthzResponse:
        resp = self._client.get(self._url("/healthz"), timeout=self._timeout)
        resp.raise_for_status()
        return HealthzResponse.model_validate(resp.json())

    def submit_job(self, payload: JobInput) -> ProcessResponse:
        resp = self._client.post(
            self._url("/v1/jobs"),
            json=payload.model_dump(mode="json", by_alias=True, exclude_none=True),
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return ProcessResponse.model_validate(resp.json())

    def get_job_status(self, job_id: Union[UUID, str], *, include_markdown: bool = False, timeout: Optional[float] = None) -> JobStatusResponse:
        jid = str(job_id)
        resp = self._client.get(
            self._url(f"/v1/jobs/{jid}"),
            params={"include_markdown": str(bool(include_markdown)).lower()},
            timeout=self._timeout if timeout is None else timeout,
        )
        resp.raise_for_status()
        return JobStatusResponse.model_validate(resp.json())


