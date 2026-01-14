from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from .auth import TokenProvider


def _odata_escape(value: str) -> str:
    # OData strings are single-quoted; escape single quotes by doubling them.
    return value.replace("'", "''")


def _normalize_guid(value: str) -> str:
    v = value.strip()
    if v.startswith("{") and v.endswith("}"):
        v = v[1:-1]
    return v


@dataclass
class DataverseClient:
    base_url: str
    api_version: str
    token_provider: TokenProvider

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=30.0)

    def _headers(self, *, include_annotations: bool = True) -> dict[str, str]:
        token = self.token_provider.get_access_token()
        headers: dict[str, str] = {
            "Authorization": f"Bearer {token}",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json;odata.metadata=none",
            "Content-Type": "application/json; charset=utf-8",
        }

        # Helpful for demos: includes formatted values (option set labels, etc.)
        # and lookup logical names so callers can understand polymorphic lookups.
        if include_annotations:
            headers["Prefer"] = (
                'odata.include-annotations="'
                'OData.Community.Display.V1.FormattedValue,'
                'Microsoft.Dynamics.CRM.lookuplogicalname,'
                'Microsoft.Dynamics.CRM.associatednavigationproperty'
                '"'
            )

        return headers

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/data/{self.api_version}/{path.lstrip('/')}"

    def get_contact(self, contact_id: str, select: str | None = None) -> dict[str, Any]:
        contact_id = _normalize_guid(contact_id)
        select_clause = f"?$select={select}" if select else ""
        url = self._url(f"contacts({contact_id}){select_clause}")
        with self._client() as client:
            resp = client.get(url, headers=self._headers(include_annotations=True))
        resp.raise_for_status()
        return resp.json()

    def search_contacts(self, query: str, top: int = 5) -> list[dict[str, Any]]:
        q = _odata_escape(query.strip())
        if not q:
            return []

        # Basic, demo-friendly search. Adjust field list/filters as needed.
        select = "contactid,fullname,firstname,lastname,emailaddress1,mobilephone,telephone1"
        filter_expr = (
            f"contains(fullname,'{q}')"
            f" or contains(emailaddress1,'{q}')"
            f" or contains(mobilephone,'{q}')"
            f" or contains(telephone1,'{q}')"
        )

        url = self._url(
            "contacts"
            f"?$select={select}"
            f"&$filter={filter_expr}"
            f"&$top={int(top)}"
        )
        with self._client() as client:
            resp = client.get(url, headers=self._headers(include_annotations=True))
        resp.raise_for_status()
        payload = resp.json()
        return list(payload.get("value", []))

    def update_contact(self, contact_id: str, fields: dict[str, Any]) -> None:
        contact_id = _normalize_guid(contact_id)
        url = self._url(f"contacts({contact_id})")
        with self._client() as client:
            resp = client.patch(url, headers=self._headers(include_annotations=False), json=fields)
        resp.raise_for_status()

    def get_case(self, case_id: str, select: str | None = None) -> dict[str, Any]:
        case_id = _normalize_guid(case_id)
        select_clause = f"?$select={select}" if select else ""
        url = self._url(f"incidents({case_id}){select_clause}")
        with self._client() as client:
            resp = client.get(url, headers=self._headers(include_annotations=True))
        resp.raise_for_status()
        return resp.json()

    def search_cases(self, query: str, top: int = 5) -> list[dict[str, Any]]:
        q = _odata_escape(query.strip())
        if not q:
            return []

        select = "incidentid,title,ticketnumber,createdon,statuscode,statecode,prioritycode,_customerid_value"
        filter_expr = f"contains(title,'{q}') or contains(ticketnumber,'{q}')"
        url = self._url(
            "incidents"
            f"?$select={select}"
            f"&$filter={filter_expr}"
            f"&$orderby=createdon desc"
            f"&$top={int(top)}"
        )
        with self._client() as client:
            resp = client.get(url, headers=self._headers(include_annotations=True))
        resp.raise_for_status()
        payload = resp.json()
        return list(payload.get("value", []))

    def list_cases_for_contact(self, contact_id: str, top: int = 5) -> list[dict[str, Any]]:
        contact_id = _normalize_guid(contact_id)
        top = int(top)
        if top <= 0:
            return []
        # Guardrail for demos; Dataverse supports larger pages but we avoid
        # accidental huge responses.
        if top > 500:
            top = 500
        select = (
            "incidentid,title,ticketnumber,createdon,statuscode,statecode,prioritycode,description,"
            "_customerid_value"
        )
        url = self._url(
            "incidents"
            f"?$select={select}"
            f"&$filter=_customerid_value eq {contact_id}"
            f"&$orderby=createdon desc"
            f"&$top={top}"
        )
        with self._client() as client:
            resp = client.get(url, headers=self._headers(include_annotations=True))
        resp.raise_for_status()
        payload = resp.json()
        items = list(payload.get("value", []))

        # If customerid is polymorphic, keep only cases where the lookup is a contact.
        filtered: list[dict[str, Any]] = []
        for item in items:
            logical_name = item.get("_customerid_value@Microsoft.Dynamics.CRM.lookuplogicalname")
            if logical_name and str(logical_name).lower() != "contact":
                continue
            filtered.append(item)
        return filtered

    def list_active_cases_for_contact(self, contact_id: str, top: int = 50) -> list[dict[str, Any]]:
        """List active cases for a contact (statecode=0)."""
        contact_id = _normalize_guid(contact_id)
        top = int(top)
        if top <= 0:
            return []
        if top > 500:
            top = 500

        select = (
            "incidentid,title,ticketnumber,createdon,statuscode,statecode,prioritycode,description,"
            "_customerid_value"
        )
        url = self._url(
            "incidents"
            f"?$select={select}"
            f"&$filter=_customerid_value eq {contact_id} and statecode eq 0"
            f"&$orderby=createdon desc"
            f"&$top={top}"
        )
        with self._client() as client:
            resp = client.get(url, headers=self._headers(include_annotations=True))
        resp.raise_for_status()
        payload = resp.json()
        items = list(payload.get("value", []))

        filtered: list[dict[str, Any]] = []
        for item in items:
            logical_name = item.get("_customerid_value@Microsoft.Dynamics.CRM.lookuplogicalname")
            if logical_name and str(logical_name).lower() != "contact":
                continue
            filtered.append(item)
        return filtered
