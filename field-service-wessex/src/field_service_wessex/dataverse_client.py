"""Dataverse Web API client with OAuth2 authentication.

Reused pattern from field-service-mikeo. Loads credentials from
mcp-dataverse-server/.env by default.
"""

import os
import re
from typing import Any

import httpx
from dotenv import load_dotenv

# Resolve workspace root and load .env from mcp-dataverse-server
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
_MCP_ENV = os.path.join(_PROJECT_ROOT, "mcp-dataverse-server", ".env")

if os.path.exists(_MCP_ENV):
    load_dotenv(_MCP_ENV)
else:
    load_dotenv()


class DataverseClient:
    """Client for interacting with Dataverse Web API."""

    def __init__(self) -> None:
        self.base_url = os.getenv("DATAVERSE_BASE_URL", "").rstrip("/")
        self.tenant_id = os.getenv("DATAVERSE_TENANT_ID", "")
        self.client_id = os.getenv("DATAVERSE_CLIENT_ID", "")
        self.client_secret = os.getenv("DATAVERSE_CLIENT_SECRET", "")
        self._token: str | None = None

    @property
    def api_url(self) -> str:
        return f"{self.base_url}/api/data/v9.2"

    def _get_token(self) -> str:
        if self._token:
            return self._token
        response = httpx.post(
            f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "resource": self.base_url,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        result = response.json()
        if "access_token" not in result:
            raise RuntimeError(
                f"Auth failed: {result.get('error_description', 'Unknown')}"
            )
        self._token = result["access_token"]
        return self._token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "Prefer": "odata.include-annotations=*",
        }

    def get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self.api_url}/{endpoint}"
        resp = httpx.get(url, headers=self._headers(), params=params, timeout=30.0)
        resp.raise_for_status()
        return resp.json()

    def post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any] | None:
        url = f"{self.api_url}/{endpoint}"
        resp = httpx.post(url, headers=self._headers(), json=data, timeout=60.0)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"POST {endpoint} failed ({resp.status_code}): {resp.text[:500]}"
            )
        if resp.status_code == 204:
            location = resp.headers.get("OData-EntityId", "")
            return {"@odata.id": location}
        return resp.json() if resp.content else None

    def patch(self, endpoint: str, data: dict[str, Any]) -> None:
        url = f"{self.api_url}/{endpoint}"
        resp = httpx.patch(url, headers=self._headers(), json=data, timeout=30.0)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"PATCH {endpoint} failed ({resp.status_code}): {resp.text[:500]}"
            )

    def post_ref(self, endpoint: str, ref_url: str) -> bool:
        """POST a $ref association (many-to-many relationship)."""
        url = f"{self.api_url}/{endpoint}"
        payload = {"@odata.id": f"{self.api_url}/{ref_url}"}
        resp = httpx.post(url, headers=self._headers(), json=payload, timeout=30.0)
        return resp.status_code in (200, 201, 204)


def extract_guid(odata_id: str) -> str:
    """Extract GUID from an OData-EntityId header value."""
    match = re.search(r"\(([a-f0-9-]+)\)", odata_id)
    if match:
        return match.group(1)
    raise ValueError(f"Cannot extract GUID from: {odata_id}")
