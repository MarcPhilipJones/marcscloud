from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    dataverse_base_url: str
    dataverse_tenant_id: str
    dataverse_client_id: str
    dataverse_client_secret: str
    dataverse_api_version: str
    allow_writes: bool


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

    return Settings(
        dataverse_base_url=base_url,
        dataverse_tenant_id=tenant_id,
        dataverse_client_id=client_id,
        dataverse_client_secret=client_secret,
        dataverse_api_version=api_version,
        allow_writes=allow_writes,
    )
