## Data Ingestion Python SDK

### Overview
- **Endpoints**: `GET /healthz`, `POST /jobs`, `GET /jobs/{id}`
- **Models**: All requests/responses are strict Pydantic models
- **Auth**: Bearer token required
- **Python**: 3.11+

### Install
- From PyPI (once published):
```
uv pip install data-ingestion-sdk
```
- From source (editable):
```
uv pip install -e ./sdk/python
```

### Configuration
Provide a base URL and bearer token via env or explicitly.
- Required env vars for `SDKConfig.from_env()`:
  - `DATA_INGESTION_API_URL` (or `DATA_INGESTION_API_BASE_URL`)
  - `DATA_INGESTION_API_TOKEN`

```python
from trelent_data_ingestion_sdk import SDKConfig

# From env (raises if missing)
cfg = SDKConfig.from_env()

# Or explicit
# cfg = SDKConfig(base_url="https://api.example.com", token="<bearer>")
```

### Quickstart
```python
from trelent_data_ingestion_sdk import (
    SDKConfig, DataIngestionClient,
    S3KeysConnector, S3PrefixConnector, UrlConnector,
    BucketOutput, S3SignedUrlOutput, JobInput,
)

cfg = SDKConfig.from_env()

with DataIngestionClient(cfg) as client:
    # Health check
    print(client.healthz())

    # Submit a job using S3 keys
    job = JobInput(
        connector=S3KeysConnector(type="s3", bucket_name="my-bucket", object_keys=["docs/a.pdf", "vids/b.mp4"]),
        output=S3SignedUrlOutput(type="s3-signed-url", expires_minutes=60),
    )
    resp = client.submit_job(job)
    print("submitted:", resp.job_id)

    # Poll status (optionally include markdown bodies)
    status = client.get_job_status(resp.job_id, exclude_markdown=False)
    print(status.status)
```

### Connectors
- `S3KeysConnector` (`type="s3"`): `bucket_name`, `object_keys: list[str]`
- `S3PrefixConnector` (`type="s3_prefix"`): `bucket_name`, `prefix`
- `UrlConnector` (`type="url"`): `urls: list[str]`

### Outputs
- `S3SignedUrlOutput`: `type="s3-signed-url"`, `expires_minutes`
- `BucketOutput`: `type="bucket"`, `bucket_name`, `prefix`

### API Methods
- `client.healthz() -> HealthzResponse`
- `client.submit_job(JobInput) -> ProcessResponse`
- `client.get_job_status(job_id, exclude_markdown=False) -> JobStatusResponse`

### Delivery payloads
- When status is Completed, `JobStatusResponse.delivery` maps input identifiers to one of:

Signed URLs
```json
{
  "docs/a.pdf": {
    "images": {"<nanoid>": "https://signed.example/img1"},
    "markdown_delivery": "https://signed.example/a.md",
    "markdown": "# Document..."
  }
}
```

Bucket pointers
```json
{
  "docs/a.pdf": {
    "images": {"<nanoid>": {"bucket": "my-bucket", "key": "images/img1.png"}},
    "markdown_delivery": {"bucket": "my-bucket", "key": "converted/a.md"},
    "markdown": "# Document..."
  }
}
```

### Error handling
- Config validation: `ValueError` if missing `base_url` or `token`
- HTTP errors: `httpx.HTTPStatusError` on non-2xx responses
- Parsing: `pydantic.ValidationError` on invalid payloads

### Development
- Build locally:
```
uv build --directory sdk/python
```
- Bump version, e.g. patch:
```
uv version --bump patch --directory sdk/python --no-sync
```
- Publish via the repo’s GitHub Action (PyPI Trusted Publisher), which builds with `uv` and uploads artifacts.

