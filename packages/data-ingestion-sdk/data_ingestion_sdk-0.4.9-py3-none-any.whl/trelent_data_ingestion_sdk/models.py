from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class S3Prefix(BaseModel):
    prefix: str = Field(..., description="The prefix to list the objects from")
    recursive: bool = Field(..., description="Whether to recursively list the objects in the prefix")
# NOTE: These are intentionally duplicated from our internal connectors package
# to avoid a runtime dependency on a generically named third-party package when
# this SDK is installed from PyPI.
class S3CreateInput(BaseModel):
    type: Literal["s3"]
    bucket_name: str = Field(..., description="The name of the bucket to connect to")
    prefixes: list[str | S3Prefix] = Field(..., description="The keys of the objects to connect to")

class UrlCreateInput(BaseModel):
    type: Literal["url"]
    urls: list[str] = Field(..., description="The URLs to connect to")


# ---- Connector inputs (mirrors API schema) ----

class Connector(BaseModel):
    pass

class S3Connector(Connector, S3CreateInput):
    type: Literal["s3"]


class UrlConnector(Connector, UrlCreateInput):
    type: Literal["url"]

Connector = Annotated[
    Union[S3Connector, UrlConnector],
    Field(discriminator="type"),
]


# ---- Output definitions (mirrors API schema) ----


class BucketOutput(BaseModel):
    type: Literal["bucket"]
    bucket_name: str
    prefix: str


class S3SignedUrlOutput(BaseModel):
    type: Literal["s3-signed-url"]
    expires_minutes: int = 1440


Output = Annotated[
    Union[BucketOutput, S3SignedUrlOutput],
    Field(discriminator="type"),
]


class JobInput(BaseModel):
    connector: Connector
    output: Output
    force_error: Optional[bool] = False


# ---- Responses (mirrors API schema) ----


class WorkflowSummary(BaseModel):
    type: str
    namespace: str
    uid: str
    name: Optional[str] = None
    generate_name: Optional[str] = None
    submitted: bool


class ProcessResponse(BaseModel):
    job_id: UUID


class JobStatus(str, Enum):
    Queued = "queued"
    Running = "running"
    Completed = "completed"

class JobStatusItem(BaseModel):
    uid: str
    phase: JobStatus
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class BucketDelivery(BaseModel):
    type: Literal["bucket"]
    bucket_name: str
    object_key: str


class S3PresignedUrlDelivery(BaseModel):
    type: Literal["presigned-url"]
    url: HttpUrl
    expiry: int


DeliveryPointer = Annotated[
    Union[BucketDelivery, S3PresignedUrlDelivery],
    Field(discriminator="type"),
]


class DeliveryItem(BaseModel):
    images: Dict[str, DeliveryPointer]
    markdown_delivery: DeliveryPointer
    markdown: Optional[str] = None


class JobStatusResponse(BaseModel):
    job_id: UUID
    status: JobStatus
    batches: List[JobStatusItem]
    delivery: Optional[Dict[str, DeliveryItem]] = None
    errors: Optional[Dict[str, Dict[str, Any]]] = None

    model_config = ConfigDict(extra="allow")


class HealthzResponse(BaseModel):
    status: str


