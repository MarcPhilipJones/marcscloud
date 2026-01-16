from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv


DEFAULT_DEMO_BOOKABLE_RESOURCE_ID = "b8dddd9c-3b61-ef11-bfe2-002248a36d0e"
DEFAULT_DEMO_RESOURCE_NAME = "Alan Steiner"
DEFAULT_DEMO_JOB_NAME = "Boiler Repair (Self Service)"


@dataclass(frozen=True)
class Settings:
    dataverse_base_url: str
    dataverse_tenant_id: str
    dataverse_client_id: str
    dataverse_client_secret: str
    dataverse_api_version: str
    allow_writes: bool
    demo_bookable_resource_id: str | None
    demo_resource_name: str
    demo_job_name: str
    demo_fast: bool
    clear_demo_caches_on_start: bool


def _require(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value.strip()


def load_settings() -> Settings:
    # For local dev/demo, prefer values from a .env file when present.
    # This allows toggling behavior (e.g., DATAVERSE_ALLOW_WRITES) without
    # modifying the shell environment.
    load_dotenv(override=True)

    base_url = _require("DATAVERSE_BASE_URL").rstrip("/")
    tenant_id = _require("DATAVERSE_TENANT_ID")
    client_id = _require("DATAVERSE_CLIENT_ID")
    client_secret = _require("DATAVERSE_CLIENT_SECRET")
    api_version = os.getenv("DATAVERSE_API_VERSION", "v9.2").strip() or "v9.2"
    allow_writes = os.getenv("DATAVERSE_ALLOW_WRITES", "false").strip().lower() in {"1", "true", "yes"}

    # Optional demo convenience: constrain availability to a single Bookable Resource.
    # Set MCP_DEMO_BOOKABLE_RESOURCE_ID to a Bookable Resource GUID.
    demo_resource_id = os.getenv("MCP_DEMO_BOOKABLE_RESOURCE_ID")
    demo_resource_id = demo_resource_id.strip() if isinstance(demo_resource_id, str) and demo_resource_id.strip() else DEFAULT_DEMO_BOOKABLE_RESOURCE_ID

    demo_resource_name = os.getenv("MCP_DEMO_RESOURCE_NAME", DEFAULT_DEMO_RESOURCE_NAME).strip() or DEFAULT_DEMO_RESOURCE_NAME
    demo_job_name = os.getenv("MCP_DEMO_JOB_NAME", DEFAULT_DEMO_JOB_NAME).strip() or DEFAULT_DEMO_JOB_NAME
    demo_fast = os.getenv("MCP_DEMO_FAST", "true").strip().lower() in {"1", "true", "yes"}
    clear_demo_caches_on_start = os.getenv("MCP_CLEAR_DEMO_CACHES_ON_START", "true").strip().lower() in {"1", "true", "yes"}

    return Settings(
        dataverse_base_url=base_url,
        dataverse_tenant_id=tenant_id,
        dataverse_client_id=client_id,
        dataverse_client_secret=client_secret,
        dataverse_api_version=api_version,
        allow_writes=allow_writes,
        demo_bookable_resource_id=demo_resource_id,
        demo_resource_name=demo_resource_name,
        demo_job_name=demo_job_name,
        demo_fast=demo_fast,
        clear_demo_caches_on_start=clear_demo_caches_on_start,
    )
