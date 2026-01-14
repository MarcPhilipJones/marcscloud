from __future__ import annotations

from dataclasses import dataclass

import msal


@dataclass(frozen=True)
class TokenProvider:
    tenant_id: str
    client_id: str
    client_secret: str
    resource: str

    def get_access_token(self) -> str:
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        # For Dataverse, use the resource scope pattern: {resource}/.default
        scopes = [f"{self.resource}/.default"]

        app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=authority,
        )

        result = app.acquire_token_silent(scopes=scopes, account=None)
        if not result:
            result = app.acquire_token_for_client(scopes=scopes)

        access_token = result.get("access_token") if isinstance(result, dict) else None
        if not access_token:
            error = result.get("error") if isinstance(result, dict) else "unknown_error"
            desc = result.get("error_description") if isinstance(result, dict) else ""
            raise RuntimeError(f"Failed to acquire Dataverse token: {error} {desc}".strip())

        return access_token
