"""Dataverse Web API client with OAuth2 authentication."""

import os
from typing import Any

import httpx
from dotenv import load_dotenv


class DataverseClient:
    """Client for interacting with Dataverse Web API."""

    def __init__(
        self,
        dataverse_url: str | None = None,
        tenant_id: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        load_dotenv()
        
        self.dataverse_url = (dataverse_url or os.getenv("DATAVERSE_URL", "")).rstrip("/")
        self.tenant_id = tenant_id or os.getenv("AZURE_TENANT_ID", "")
        self.client_id = client_id or os.getenv("AZURE_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("AZURE_CLIENT_SECRET", "")
        
        self._token: str | None = None

    @property
    def api_base(self) -> str:
        """Get the base API URL."""
        return f"{self.dataverse_url}/api/data/v9.2"

    def _get_token(self) -> str:
        """Acquire access token for Dataverse via OAuth2 client credentials."""
        if self._token:
            return self._token
            
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        response = httpx.post(token_url, data={
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": f"{self.dataverse_url}/.default",
        }, timeout=30.0)
        
        result = response.json()
        
        if "access_token" not in result:
            error = result.get("error_description", "Unknown authentication error")
            raise RuntimeError(f"Failed to acquire token: {error}")
        
        self._token = result["access_token"]
        return self._token

    def _get_headers(self) -> dict[str, str]:
        """Get standard headers for API requests."""
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Prefer": "odata.include-annotations=*",
        }

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make GET request to Dataverse API."""
        url = f"{self.api_base}/{endpoint}"
        response = httpx.get(url, headers=self._get_headers(), params=params, timeout=30.0)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Make POST request to Dataverse API."""
        url = f"{self.api_base}/{endpoint}"
        response = httpx.post(url, headers=self._get_headers(), json=data, timeout=30.0)
        
        if response.status_code >= 400:
            error_body = response.text
            raise RuntimeError(f"POST {endpoint} failed ({response.status_code}): {error_body}")
        
        # Return location header for created entity
        if response.status_code == 204:
            location = response.headers.get("OData-EntityId", "")
            return {"@odata.id": location}
        return response.json() if response.content else None

    def patch(self, endpoint: str, data: dict[str, Any]) -> None:
        """Make PATCH request to Dataverse API."""
        url = f"{self.api_base}/{endpoint}"
        response = httpx.patch(url, headers=self._get_headers(), json=data, timeout=30.0)
        response.raise_for_status()

    def delete(self, endpoint: str) -> None:
        """Make DELETE request to Dataverse API."""
        url = f"{self.api_base}/{endpoint}"
        response = httpx.delete(url, headers=self._get_headers(), timeout=30.0)
        response.raise_for_status()
