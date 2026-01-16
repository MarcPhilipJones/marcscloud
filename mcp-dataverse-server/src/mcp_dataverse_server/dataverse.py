from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timedelta, timezone
import re
import json
import logging
import time
from zoneinfo import ZoneInfo

import httpx
from .config import DEFAULT_DEMO_JOB_NAME

from .auth import TokenProvider


logger = logging.getLogger(__name__)


def _odata_escape(value: str) -> str:
    # OData strings are single-quoted; escape single quotes by doubling them.
    return value.replace("'", "''")


def _normalize_guid(value: str) -> str:
    v = value.strip()
    if v.startswith("{") and v.endswith("}"):
        v = v[1:-1]
    return v


def _extract_guid_from_odata_entity_id(entity_id_url: str) -> str | None:
    # Example: https://org.crm.dynamics.com/api/data/v9.2/contacts(<guid>)
    match = re.search(r"\(([0-9a-fA-F-]{36})\)", entity_id_url)
    return match.group(1) if match else None


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_iso_datetime(value: str) -> datetime:
    # Dataverse and UFX commonly emit Z-terminated timestamps.
    v = (value or "").strip()
    if not v:
        raise ValueError("Empty datetime string")
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _normalize_priority(value: str | None) -> str:
    v = (value or "").strip().lower()
    if v in {"1", "high", "urgent", "priority", "p1"}:
        return "high"
    return "normal"


@dataclass
class DataverseClient:
    base_url: str
    api_version: str
    token_provider: TokenProvider

    _work_order_priority_cache: dict[str, str | None] = field(default_factory=dict, init=False, repr=False)
    _action_name_cache: set[str] | None = field(default=None, init=False, repr=False)
    _action_probe_cache: dict[str, bool] = field(default_factory=dict, init=False, repr=False)
    _relationship_nav_cache: dict[str, str | None] = field(default_factory=dict, init=False, repr=False)
    _relationship_attr_cache: dict[str, str | None] = field(default_factory=dict, init=False, repr=False)
    _characteristic_id_cache: dict[str, str | None] = field(default_factory=dict, init=False, repr=False)

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

    def _get(self, path: str, *, include_annotations: bool = True) -> dict[str, Any]:
        url = self._url(path)
        with self._client() as client:
            resp = client.get(url, headers=self._headers(include_annotations=include_annotations))
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            body = (resp.text or "").strip()
            raise RuntimeError(f"Dataverse GET {url} failed: HTTP {resp.status_code}. {body}") from e
        return resp.json()

    def _get_text(self, path: str) -> str:
        url = self._url(path)
        # $metadata is XML; requesting JSON yields 415 in many orgs.
        headers = self._headers(include_annotations=False)
        if path.strip().startswith("$metadata"):
            headers["Accept"] = "application/xml"
            headers.pop("Content-Type", None)
        with self._client() as client:
            resp = client.get(url, headers=headers)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            body = (resp.text or "").strip()
            raise RuntimeError(f"Dataverse GET {url} failed: HTTP {resp.status_code}. {body}") from e
        return resp.text

    def try_get_booking_confirmation(self, booking_id: str) -> dict[str, Any] | None:
        """Best-effort lookup of a Bookable Resource Booking and its assigned resource."""
        bid = (booking_id or "").strip()
        if not bid:
            return None
        bid = _normalize_guid(bid)

        def _find_first_guid_value(d: dict[str, Any], key_contains: str) -> str | None:
            for k, v in d.items():
                if isinstance(k, str) and key_contains.lower() in k.lower() and isinstance(v, str) and re.fullmatch(r"[0-9a-fA-F-]{36}", v.strip()):
                    return v.strip()
            return None

        try:
            booking = self._get(
                "bookableresourcebookings(" + bid + ")?$select=bookableresourcebookingid,starttime,endtime,_resourceid_value",
                include_annotations=True,
            )
        except Exception:
            return None

        if not isinstance(booking, dict):
            return None

        resource_id = None
        if isinstance(booking.get("_resourceid_value"), str):
            resource_id = booking.get("_resourceid_value")
        if not resource_id:
            resource_id = _find_first_guid_value(booking, "_resourceid_value")

        resource: dict[str, Any] | None = None
        if resource_id:
            try:
                r = self._get(
                    "bookableresources(" + _normalize_guid(resource_id) + ")?$select=bookableresourceid,name",
                    include_annotations=True,
                )
                if isinstance(r, dict):
                    resource = {
                        "id": str(r.get("bookableresourceid") or resource_id),
                        "name": r.get("name"),
                    }
            except Exception:
                resource = {"id": str(resource_id), "name": None}

        return {
            "id": str(booking.get("bookableresourcebookingid") or bid),
            "start": booking.get("starttime"),
            "end": booking.get("endtime"),
            "resource": resource,
        }

    def _post(self, path: str, *, payload: dict[str, Any], include_annotations: bool = True) -> httpx.Response:
        url = self._url(path)
        with self._client() as client:
            resp = client.post(url, headers=self._headers(include_annotations=include_annotations), json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            body = (resp.text or "").strip()
            raise RuntimeError(f"Dataverse POST {url} failed: HTTP {resp.status_code}. {body}") from e
        return resp

    def _post_raw(self, path: str, *, payload: dict[str, Any], include_annotations: bool = True) -> httpx.Response:
        """POST without raising for non-2xx (used for capability probing)."""
        url = self._url(path)
        with self._client() as client:
            return client.post(url, headers=self._headers(include_annotations=include_annotations), json=payload)

    def probe_unbound_action_exists(self, action_name: str) -> bool:
        """Best-effort, low-cost probe for whether an unbound action exists.

        Preferred approach: parse action names from `GET $metadata` (cached).

        Fallback approach: POST /<actionName> with an empty payload and interpret HTTP 404
        as "missing". Other status codes (401/403/400/500) are treated as "exists" because
        the route is present, even if the caller lacks permissions or the payload is invalid.
        """
        name = (action_name or "").strip()
        if not name:
            return False
        if name in self._action_probe_cache:
            return bool(self._action_probe_cache[name])

        # First try metadata-based discovery (avoids generating noisy 4xx logs).
        try:
            names = self.try_list_action_names()
            if names:
                exists = name in names
                self._action_probe_cache[name] = exists
                return exists
        except Exception:
            # Fall back to POST-based probing.
            pass

        try:
            resp = self._post_raw(name, payload={}, include_annotations=False)
            exists = resp.status_code != 404
        except Exception:
            # If we can't probe (network, auth, etc.), don't assume capability.
            exists = False

        self._action_probe_cache[name] = exists
        return exists

    def create_record(self, entity_set: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a Dataverse record and return {"id": <guid>, "entity_set": <...>}.

        Dataverse often returns 204 + OData-EntityId header rather than a JSON body.
        """
        resp = self._post(entity_set, payload=payload, include_annotations=False)
        entity_id = resp.headers.get("OData-EntityId") or resp.headers.get("Location")
        record_id = _extract_guid_from_odata_entity_id(entity_id) if entity_id else None
        if not record_id:
            # Some endpoints may return JSON; try parsing conservatively.
            try:
                body = resp.json()
            except Exception:
                body = {}
            record_id = body.get(f"{entity_set.rstrip('s')}id") or body.get("id")
        if not record_id:
            raise RuntimeError(f"Create {entity_set} succeeded but no record id was returned.")
        return {"entity_set": entity_set, "id": str(record_id)}

    def update_record(self, entity_set: str, record_id: str, fields: dict[str, Any]) -> None:
        """PATCH a Dataverse record.

        Note: many endpoints return 204 No Content on success.
        """
        rid = _normalize_guid(record_id)
        url = self._url(f"{entity_set}({rid})")
        with self._client() as client:
            resp = client.patch(url, headers=self._headers(include_annotations=False), json=fields)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            body = (resp.text or "").strip()
            raise RuntimeError(f"Dataverse PATCH {url} failed: HTTP {resp.status_code}. {body}") from e

    def execute_unbound_action(self, action_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute an unbound Dataverse action (POST /<actionName>)."""
        resp = self._post(action_name, payload=payload, include_annotations=True)
        # Many actions return JSON; some return empty.
        try:
            return resp.json()
        except Exception:
            return {}

    def try_list_action_names(self) -> set[str]:
        """Best-effort list of action names available in this org.

        Used for capability probing. Cached for process lifetime.
        """
        if self._action_name_cache is not None:
            return set(self._action_name_cache)
        try:
            xml = self._get_text("$metadata")
            # Actions are declared like: <Action Name="msdyn_FpsAction" ...>
            names = set(re.findall(r"<Action\s+Name=\"([^\"]+)\"", xml))
            self._action_name_cache = names
            return set(names)
        except Exception:
            self._action_name_cache = set()
            return set()

    def try_get_many_to_one_nav_property(
        self,
        *,
        referencing_entity_logical_name: str,
        referenced_entity_logical_name: str,
    ) -> str | None:
        """Find the navigation property name used for @odata.bind.

        Dataverse organizations can customize schema such that the navigation property
        for a lookup is not what you'd expect. This method queries the metadata API
        (EntityDefinitions) and returns the referencing navigation property name.

        Example usage:
        - referencing: msdyn_resourcerequirement
        - referenced:  msdyn_workorder
        """

        refing = (referencing_entity_logical_name or "").strip().lower()
        refed = (referenced_entity_logical_name or "").strip().lower()
        if not refing or not refed:
            return None

        cache_key = f"{refing}->{refed}"
        if cache_key in self._relationship_nav_cache:
            return self._relationship_nav_cache[cache_key]

        try:
            # ManyToOneRelationships has: ReferencedEntity, ReferencingEntityNavigationPropertyName, ReferencingAttribute
            path = (
                "EntityDefinitions(LogicalName='"
                + refing
                + "')/ManyToOneRelationships?$select=ReferencedEntity,ReferencingEntityNavigationPropertyName,ReferencingAttribute"
                + "&$filter=ReferencedEntity eq '"
                + refed
                + "'"
            )
            resp = self._get(path, include_annotations=False)
            items = list(resp.get("value", [])) if isinstance(resp, dict) else []
            nav: str | None = None
            for it in items:
                if not isinstance(it, dict):
                    continue
                nav_name = it.get("ReferencingEntityNavigationPropertyName")
                if isinstance(nav_name, str) and nav_name.strip():
                    nav = nav_name.strip()
                    break
            nav = str(nav) if nav else None
            self._relationship_nav_cache[cache_key] = nav
            return nav
        except Exception:
            self._relationship_nav_cache[cache_key] = None
            return None

    def try_get_many_to_one_nav_property_for_attribute(
        self,
        *,
        referencing_entity_logical_name: str,
        referencing_attribute_logical_name: str,
    ) -> str | None:
        """Find the navigation property name for a specific lookup attribute.

        Why this exists:
        Some tables have multiple lookups to the same referenced entity.
        Querying by referenced entity alone (try_get_many_to_one_nav_property)
        can return the wrong relationship (e.g., a different lookup).

        This method pins the relationship by ReferencingAttribute, which is what
        we need when creating records via @odata.bind.
        """

        refing = (referencing_entity_logical_name or "").strip().lower()
        attr = (referencing_attribute_logical_name or "").strip().lower()
        if not refing or not attr:
            return None

        cache_key = f"{refing}.attr:{attr}"
        if cache_key in self._relationship_nav_cache:
            return self._relationship_nav_cache[cache_key]

        try:
            path = (
                "EntityDefinitions(LogicalName='"
                + refing
                + "')/ManyToOneRelationships?$select=ReferencingEntityNavigationPropertyName,ReferencingAttribute"
                + "&$filter=ReferencingAttribute eq '"
                + attr
                + "'"
            )
            resp = self._get(path, include_annotations=False)
            items = list(resp.get("value", [])) if isinstance(resp, dict) else []
            nav: str | None = None
            for it in items:
                if not isinstance(it, dict):
                    continue
                nav_name = it.get("ReferencingEntityNavigationPropertyName")
                if isinstance(nav_name, str) and nav_name.strip():
                    nav = nav_name.strip()
                    break
            nav = str(nav) if nav else None
            self._relationship_nav_cache[cache_key] = nav
            return nav
        except Exception:
            self._relationship_nav_cache[cache_key] = None
            return None

    def try_get_many_to_one_referencing_attribute(
        self,
        *,
        referencing_entity_logical_name: str,
        referenced_entity_logical_name: str,
    ) -> str | None:
        """Find the referencing attribute logical name used for a lookup.

        Useful for building OData filters like `_<lookupattribute>_value eq <guid>`.
        """
        refing = (referencing_entity_logical_name or "").strip().lower()
        refed = (referenced_entity_logical_name or "").strip().lower()
        if not refing or not refed:
            return None

        cache_key = f"{refing}->{refed}"
        if cache_key in self._relationship_attr_cache:
            return self._relationship_attr_cache[cache_key]

        try:
            path = (
                "EntityDefinitions(LogicalName='"
                + refing
                + "')/ManyToOneRelationships?$select=ReferencedEntity,ReferencingAttribute"
                + "&$filter=ReferencedEntity eq '"
                + refed
                + "'"
            )
            resp = self._get(path, include_annotations=False)
            items = list(resp.get("value", [])) if isinstance(resp, dict) else []
            attr: str | None = None
            for it in items:
                if not isinstance(it, dict):
                    continue
                if str(it.get("ReferencedEntity", "")).strip().lower() != refed:
                    continue
                attr = it.get("ReferencingAttribute")
                if attr:
                    break
            attr = str(attr) if attr else None
            self._relationship_attr_cache[cache_key] = attr
            return attr
        except Exception:
            self._relationship_attr_cache[cache_key] = None
            return None

    def list_resource_requirements_for_work_order(self, work_order_id: str, top: int = 10) -> list[dict[str, Any]]:
        """List resource requirements linked to a work order.

        Work Order creation can auto-create a requirement in many orgs.
        """
        work_order_id = _normalize_guid(work_order_id)
        top = int(top)
        if top <= 0:
            return []
        if top > 50:
            top = 50

        discovered_attr = self.try_get_many_to_one_referencing_attribute(
            referencing_entity_logical_name="msdyn_resourcerequirement",
            referenced_entity_logical_name="msdyn_workorder",
        )

        candidates: list[str] = []
        if discovered_attr:
            candidates.append(discovered_attr)
        candidates.extend(["msdyn_workorder", "msdyn_workorderid"])

        seen: set[str] = set()
        lookup_attrs: list[str] = []
        for c in candidates:
            c = (c or "").strip()
            if not c:
                continue
            if c.lower() in seen:
                continue
            seen.add(c.lower())
            lookup_attrs.append(c)

        select = "msdyn_resourcerequirementid,msdyn_name,createdon,statecode,statuscode,msdyn_fromdate,msdyn_todate,msdyn_duration"

        for attr in lookup_attrs:
            try:
                filter_expr = f"_{attr}_value eq {work_order_id}"
                resp = self._get(
                    "msdyn_resourcerequirements"
                    f"?$select={select}"
                    f"&$filter={filter_expr}"
                    f"&$orderby=createdon asc"
                    f"&$top={top}",
                    include_annotations=True,
                )
                items = list(resp.get("value", [])) if isinstance(resp, dict) else []
                if items:
                    return items
            except Exception:
                continue

        return []

    def wait_for_work_order_resource_requirements(
        self,
        *,
        work_order_id: str,
        timeout_seconds: float = 20.0,
        poll_interval_seconds: float = 1.0,
        top: int = 10,
    ) -> list[dict[str, Any]]:
        """Poll until at least one requirement exists for a work order."""
        deadline = time.monotonic() + max(0.0, float(timeout_seconds))
        while True:
            items = self.list_resource_requirements_for_work_order(work_order_id, top=int(top))
            if items:
                return items
            if time.monotonic() >= deadline:
                return []
            time.sleep(max(0.1, float(poll_interval_seconds)))

    def attach_requirement_characteristics(self, *, requirement_id: str, characteristic_ids: list[str]) -> None:
        requirement_id = _normalize_guid(requirement_id)
        if not characteristic_ids:
            return

        discovered_req_nav: str | None = None
        discovered_char_nav: str | None = None
        for logical in ["msdyn_requirementcharacteristic", "msdyn_requirementcharacteristics"]:
            if not discovered_req_nav:
                discovered_req_nav = self.try_get_many_to_one_nav_property(
                    referencing_entity_logical_name=logical,
                    referenced_entity_logical_name="msdyn_resourcerequirement",
                )
            if not discovered_char_nav:
                discovered_char_nav = self.try_get_many_to_one_nav_property(
                    referencing_entity_logical_name=logical,
                    referenced_entity_logical_name="characteristic",
                )
            if discovered_req_nav and discovered_char_nav:
                break

        requirement_bind_candidates: list[str] = []
        if discovered_req_nav:
            requirement_bind_candidates.append(f"{discovered_req_nav}@odata.bind")
        requirement_bind_candidates.extend(
            [
                "msdyn_ResourceRequirement@odata.bind",
                "msdyn_resourcerequirement@odata.bind",
            ]
        )

        characteristic_bind_candidates: list[str] = []
        if discovered_char_nav:
            characteristic_bind_candidates.append(f"{discovered_char_nav}@odata.bind")
        characteristic_bind_candidates.extend(
            [
                "msdyn_characteristicid@odata.bind",
                "msdyn_characteristic@odata.bind",
                "characteristicid@odata.bind",
            ]
        )

        created = 0
        last_error: str | None = None
        for cid in characteristic_ids:
            try:
                req_bind = f"/msdyn_resourcerequirements({requirement_id})"
                char_bind = f"/characteristics({_normalize_guid(str(cid))})"

                attached = False
                attach_error: str | None = None
                last_keys: tuple[str, str] | None = None
                for req_key in requirement_bind_candidates:
                    for char_key in characteristic_bind_candidates:
                        payload = {
                            req_key: req_bind,
                            char_key: char_bind,
                        }
                        try:
                            self.create_record("msdyn_requirementcharacteristics", payload)
                            created += 1
                            attached = True
                            break
                        except Exception as e:
                            attach_error = str(e)
                            last_keys = (req_key, char_key)
                    if attached:
                        break

                if not attached:
                    keys_txt = f" (last_keys={last_keys[0]} + {last_keys[1]})" if last_keys else ""
                    logger.warning(
                        "Failed to attach requirement characteristic. requirement=%s characteristic=%s%s",
                        requirement_id,
                        str(cid),
                        keys_txt,
                    )
                    raise RuntimeError((attach_error or "Failed to attach requirement characteristic") + keys_txt)
            except Exception as e:
                last_error = str(e)

        if created == 0:
            raise RuntimeError(last_error or "Failed to attach requirement characteristics")

    def parse_preferred_local_start_to_utc(self, preferred_start_local: str) -> datetime:
        """Parse a preferred local start time into UTC.

        Accepts:
        - ISO datetime strings (with or without timezone)
        - "HH:MM" (assumed today in Europe/London)
        """
        raw = (preferred_start_local or "").strip()
        if not raw:
            raise ValueError("preferred_start_local is required")

        try:
            tz = ZoneInfo("Europe/London")
        except Exception:
            tz = timezone.utc

        # HH:MM
        m = re.fullmatch(r"(\d{1,2}):(\d{2})", raw)
        if m:
            hh = int(m.group(1))
            mm = int(m.group(2))
            now_local = datetime.now(tz)
            local_dt = datetime.combine(now_local.date(), datetime.min.time(), tzinfo=tz).replace(hour=hh, minute=mm, second=0)
            return local_dt.astimezone(timezone.utc)

        # ISO datetime
        # If it ends with Z or has offset, parse as is; otherwise treat as local.
        v = raw
        if v.endswith("Z") or re.search(r"[+-]\d{2}:\d{2}$", v):
            return _parse_iso_datetime(v)

        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        return dt.astimezone(timezone.utc)

    def create_case_for_contact(
        self,
        *,
        contact_id: str,
        title: str,
        description: str,
        priority: str = "normal",
        origin: str = "web",
    ) -> str:
        priority = _normalize_priority(priority)
        contact_id = _normalize_guid(contact_id)
        origin_code = 3 if (origin or "").strip().lower() == "web" else 3

        payload: dict[str, Any] = {
            "title": title,
            "description": description,
            "customerid_contact@odata.bind": f"/contacts({contact_id})",
            "caseorigincode": origin_code,
            "prioritycode": 1 if priority == "high" else 2,
        }
        case = self.create_record("incidents", payload)
        return str(case["id"])

    def create_boiler_repair_work_order(
        self,
        *,
        case_id: str | None,
        priority: str = "normal",
    ) -> str:
        priority = _normalize_priority(priority)

        primary_incident_type_id = "c1033273-2669-ef11-bfe2-000d3a68576d"
        work_order_type_id = "e5ccb33e-17bd-ea11-a812-000d3a1b14a2"
        price_list_id = "b9b533c4-2769-ef11-bfe2-000d3a68576d"
        currency_id = "44ed73b4-2769-ef11-bfe2-000d3a68576d"
        service_account_id = "f0622224-3e61-ef11-bfe2-002248a36d0e"

        work_order_payload: dict[str, Any] = {
            "msdyn_primaryincidentdescription": "No Heating Household (Boiler Problems)",
            "msdyn_primaryincidentestimatedduration": 120,
            "msdyn_totalestimatedduration": 120,
            "msdyn_instructions": "Slow to answer the door. Please allow for this as hard of hearing and mobility issues. Call mobile upon arrival.",
            "msdyn_worklocation": 690970000,
            "msdyn_address1": "1 Ashleigh Road",
            "msdyn_city": "Birmingham",
            "msdyn_postalcode": "B91 1AE",
            "msdyn_latitude": 52.41882,
            "msdyn_longitude": -1.78605,
            "msdyn_primaryincidenttype@odata.bind": f"/msdyn_incidenttypes({primary_incident_type_id})",
            "msdyn_workordertype@odata.bind": f"/msdyn_workordertypes({work_order_type_id})",
            "msdyn_pricelist@odata.bind": f"/pricelevels({price_list_id})",
            "transactioncurrencyid@odata.bind": f"/transactioncurrencies({currency_id})",
            "msdyn_serviceaccount@odata.bind": f"/accounts({service_account_id})",
            "msdyn_billingaccount@odata.bind": f"/accounts({service_account_id})",
        }

        if case_id:
            case_id = _normalize_guid(case_id)
            work_order_payload["msdyn_servicerequest@odata.bind"] = f"/incidents({case_id})"

        # Priority: try to bind "Normal" by name, else omit.
        if priority == "high":
            work_order_payload["msdyn_priority@odata.bind"] = "/msdyn_priorities(d954a64a-dff5-ed11-8e4b-002248a6ca1f)"
        else:
            normal_id = self.try_get_work_order_priority_id("Normal")
            if normal_id:
                work_order_payload["msdyn_priority@odata.bind"] = f"/msdyn_priorities({normal_id})"

        wo = self.create_record("msdyn_workorders", work_order_payload)
        return str(wo["id"])

    def create_resource_requirement_for_work_order(
        self,
        *,
        work_order_id: str,
        window_start_utc: datetime,
        window_end_utc: datetime,
        duration_minutes: int,
        organizational_unit_id: str | None = None,
        territory_id: str | None = None,
        role_id: str | None = None,
        characteristic_ids: list[str] | None = None,
    ) -> str:
        work_order_id = _normalize_guid(work_order_id)
        duration_minutes = int(duration_minutes)

        base_payload: dict[str, Any] = {
            "msdyn_name": DEFAULT_DEMO_JOB_NAME,
            "msdyn_fromdate": _iso(window_start_utc),
            "msdyn_todate": _iso(window_end_utc),
            "msdyn_duration": duration_minutes,
        }

        # Dataverse environments can differ in the navigation-property name for the WO lookup.
        # Prefer the real navigation property name from EntityDefinitions, then fall back.
        discovered_nav = self.try_get_many_to_one_nav_property(
            referencing_entity_logical_name="msdyn_resourcerequirement",
            referenced_entity_logical_name="msdyn_workorder",
        )

        workorder_bind_candidates: list[tuple[str, str]] = []
        if discovered_nav:
            workorder_bind_candidates.append((f"{discovered_nav}@odata.bind", f"/msdyn_workorders({work_order_id})"))

        workorder_bind_candidates.extend(
            [
                ("msdyn_workorderid@odata.bind", f"/msdyn_workorders({work_order_id})"),
                ("msdyn_workorder@odata.bind", f"/msdyn_workorders({work_order_id})"),
            ]
        )

        payload: dict[str, Any] = dict(base_payload)

        # Optional scheduling constraints (best-effort; these may vary by org customization).
        if organizational_unit_id:
            payload["msdyn_organizationalunit@odata.bind"] = f"/msdyn_organizationalunits({_normalize_guid(organizational_unit_id)})"
        if territory_id:
            payload["msdyn_territory@odata.bind"] = f"/territories({_normalize_guid(territory_id)})"
        if role_id:
            payload["msdyn_role@odata.bind"] = f"/bookableresourcecategories({_normalize_guid(role_id)})"

        rr: dict[str, Any] | None = None
        last_error: str | None = None
        for key, bind_value in workorder_bind_candidates:
            attempt = dict(payload)
            attempt.pop("msdyn_workorder@odata.bind", None)
            attempt.pop("msdyn_workorderid@odata.bind", None)
            attempt[key] = bind_value
            try:
                rr = self.create_record("msdyn_resourcerequirements", attempt)
                break
            except Exception as e:
                last_error = str(e)
                continue

        if rr is None:
            raise RuntimeError(last_error or "Failed to create msdyn_resourcerequirement")

        requirement_id = str(rr["id"])

        # Do not attach/create requirement characteristics here.
        # Many orgs auto-populate requirement characteristics via Work Order automation.
        # This also avoids msdyn_requirementcharacteristics POST failures during booking.

        return requirement_id

    def try_get_characteristic_id_by_name(self, name: str) -> str | None:
        """Best-effort lookup of a Field Service characteristic (skill) by exact name.

        Returns the characteristic GUID, or None if not found / inaccessible.
        """
        key = (name or "").strip()
        if not key:
            return None
        if key.lower() in self._characteristic_id_cache:
            return self._characteristic_id_cache[key.lower()]

        try:
            q = _odata_escape(key)
            resp = self._get(
                "characteristics?$select=characteristicid,name&$filter=name eq '" + q + "'&$top=1",
                include_annotations=False,
            )
            items = list(resp.get("value", [])) if isinstance(resp, dict) else []
            cid = None
            if items and isinstance(items[0], dict):
                cid = items[0].get("characteristicid")
            cid_str = str(cid) if cid else None
            self._characteristic_id_cache[key.lower()] = cid_str
            return cid_str
        except Exception:
            self._characteristic_id_cache[key.lower()] = None
            return None

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

    def update_case(self, case_id: str, fields: dict[str, Any]) -> None:
        case_id = _normalize_guid(case_id)
        url = self._url(f"incidents({case_id})")
        with self._client() as client:
            resp = client.patch(url, headers=self._headers(include_annotations=False), json=fields)
        resp.raise_for_status()

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

    def get_work_order(self, work_order_id: str, select: str | None = None) -> dict[str, Any]:
        work_order_id = _normalize_guid(work_order_id)
        select_clause = f"?$select={select}" if select else ""
        url = self._url(f"msdyn_workorders({work_order_id}){select_clause}")
        with self._client() as client:
            resp = client.get(url, headers=self._headers(include_annotations=True))
        resp.raise_for_status()
        return resp.json()

    def search_work_orders(self, query: str, top: int = 5) -> list[dict[str, Any]]:
        q = _odata_escape(query.strip())
        if not q:
            return []

        # Note: attributes vary by FS version/customizations; keep this flexible.
        select = (
            "msdyn_workorderid,msdyn_name,msdyn_workordernumber,createdon,statecode,statuscode,"
            "_msdyn_serviceaccount_value,_msdyn_primaryincident_value"
        )
        filter_expr = f"contains(msdyn_name,'{q}') or contains(msdyn_workordernumber,'{q}')"
        url = self._url(
            "msdyn_workorders"
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

    def update_work_order(self, work_order_id: str, fields: dict[str, Any]) -> None:
        work_order_id = _normalize_guid(work_order_id)
        url = self._url(f"msdyn_workorders({work_order_id})")
        with self._client() as client:
            resp = client.patch(url, headers=self._headers(include_annotations=False), json=fields)
        resp.raise_for_status()

    # ----------------------------
    # Field Service demo helpers
    # ----------------------------

    def get_bookable_resources(self, top: int = 10) -> list[dict[str, Any]]:
        top = int(top)
        if top <= 0:
            return []
        if top > 50:
            top = 50
        payload = self._get(
            "bookableresources?$select=bookableresourceid,name&$orderby=name asc&$top=" + str(top),
            include_annotations=True,
        )
        return list(payload.get("value", []))

    def get_booking_status_id(self, name: str = "Scheduled") -> str:
        n = _odata_escape(name)
        payload = self._get(
            "bookingstatuses?$select=bookingstatusid,name&$filter=name eq '" + n + "'&$top=1",
            include_annotations=True,
        )
        items = list(payload.get("value", []))
        if not items:
            raise RuntimeError(f"No booking status found with name: {name}")
        bookingstatusid = items[0].get("bookingstatusid")
        if not bookingstatusid:
            raise RuntimeError("bookingstatuses query returned no bookingstatusid")
        return str(bookingstatusid)

    def try_get_work_order_priority_id(self, name: str) -> str | None:
        """Best-effort lookup of Field Service work order priority (msdyn_priority).

        Returns the GUID (msdyn_priorityid) or None if not found.
        """
        n = _odata_escape(name.strip())
        if not n:
            return None

        if n in self._work_order_priority_cache:
            return self._work_order_priority_cache[n]

        try:
            payload = self._get(
                "msdyn_priorities?$select=msdyn_priorityid,name&$filter=name eq '" + n + "'&$top=1",
                include_annotations=True,
            )
            items = list(payload.get("value", []))
            if not items:
                self._work_order_priority_cache[n] = None
                return None
            pid = items[0].get("msdyn_priorityid")
            value = str(pid) if pid else None
            self._work_order_priority_cache[n] = value
            return value
        except Exception:
            self._work_order_priority_cache[n] = None
            return None

    def create_bookable_resource_booking(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a Bookable Resource Booking record.

        Dataverse environments can differ in the navigation-property names used for
        lookups on this table.
        - Many orgs use `BookingStatus@odata.bind` (per metadata), while others expose lowercase variants.
        - Many orgs use `Resource@odata.bind` (per metadata), while others expose lowercase variants.

        This helper retries across common schema variants.
        """

        booking_keys = [
            "BookingStatus@odata.bind",
            "BookingStatusId@odata.bind",
            "bookingstatus@odata.bind",
            "bookingStatus@odata.bind",
            "bookingstatusid@odata.bind",
            "bookingStatusId@odata.bind",
        ]

        resource_keys = [
            "Resource@odata.bind",
            "ResourceId@odata.bind",
            "resource@odata.bind",
            "resourceId@odata.bind",
            "resourceid@odata.bind",
        ]

        def _extract_bind_value(p: dict[str, Any], keys: list[str]) -> str | None:
            for k in keys:
                v = p.get(k)
                if isinstance(v, str) and v.strip():
                    return v.strip()
            return None

        def _variant_payload(
            base: dict[str, Any],
            *,
            bookingstatus_key: str,
            resource_key: str,
        ) -> dict[str, Any]:
            p = dict(base)

            booking_bind = _extract_bind_value(
                p,
                booking_keys,
            )
            if booking_bind is not None:
                for k in booking_keys:
                    p.pop(k, None)
                p[bookingstatus_key] = booking_bind

            resource_bind = _extract_bind_value(
                p,
                resource_keys,
            )
            if resource_bind is not None:
                for k in resource_keys:
                    p.pop(k, None)
                p[resource_key] = resource_bind

            return p

        attempted: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        for booking_key in booking_keys:
            for resource_key in resource_keys:
                attempt_payload = _variant_payload(payload, bookingstatus_key=booking_key, resource_key=resource_key)
                attempted.append({"bookingstatus_key": booking_key, "resource_key": resource_key})
                logger.info("Creating booking attempt (statusKey=%s, resourceKey=%s)", booking_key, resource_key)
                try:
                    return self.create_record("bookableresourcebookings", attempt_payload)
                except Exception as e:
                    msg = str(e)
                    errors.append({"bookingstatus_key": booking_key, "resource_key": resource_key, "error": msg[:1500]})
                    logger.warning("Booking attempt failed: %s", msg[:800])
                    continue

        raise RuntimeError(
            "Booking creation failed for all attempted schema variants. "
            + json.dumps({"attempted": attempted, "errors": errors}, ensure_ascii=False)
        )

    def create_booking_for_requirement(
        self,
        *,
        slot_id: str,
        requirement_id: str,
        work_order_id: str | None = None,
        booking_status_name: str = "Scheduled",
        name: str = "Customer booking (MCP)",
    ) -> dict[str, Any]:
        """Create a single Bookable Resource Booking for an existing Resource Requirement.

        This uses the Dataverse table/entity set `bookableresourcebookings` via POST.

        `slot_id` format: <resourceId>|<startIso>|<endIso>
        """

        requirement_id = _normalize_guid(requirement_id)
        work_order_id = _normalize_guid(work_order_id) if work_order_id else None

        try:
            resource_id, start, end = (slot_id or "").split("|", 2)
        except ValueError as e:
            raise RuntimeError("Invalid slot_id. Expected format: <resourceId>|<start>|<end>") from e

        resource_id = (resource_id or "").strip()
        if not resource_id or resource_id == "unknown":
            raise RuntimeError("slot_id is missing a concrete resource id; cannot create bookableresourcebooking directly")

        booking_status_id = self.get_booking_status_id(name=booking_status_name)

        try:
            duration = int((_parse_iso_datetime(end) - _parse_iso_datetime(start)).total_seconds() // 60)
        except Exception:
            duration = 0
        if duration <= 0:
            raise RuntimeError("Invalid start/end in slot_id; duration must be > 0 minutes")

        # Use metadata-backed navigation-property names when possible.
        # IMPORTANT: discover the nav properties for the specific lookup attributes.
        # This table has multiple relationships to bookableresource; discovering by
        # referenced entity alone can return the wrong relationship (e.g. msdyn_resourcegroup).
        discovered_bookingstatus_nav = self.try_get_many_to_one_nav_property_for_attribute(
            referencing_entity_logical_name="bookableresourcebooking",
            referencing_attribute_logical_name="bookingstatus",
        )
        discovered_resource_nav = self.try_get_many_to_one_nav_property_for_attribute(
            referencing_entity_logical_name="bookableresourcebooking",
            referencing_attribute_logical_name="resource",
        )

        payload: dict[str, Any] = {
            "starttime": start,
            "endtime": end,
            "duration": duration,
            "name": name,
        }

        # These keys are normalized by create_bookable_resource_booking() across org variants.
        status_key = f"{discovered_bookingstatus_nav}@odata.bind" if discovered_bookingstatus_nav else "BookingStatus@odata.bind"
        resource_key = f"{discovered_resource_nav}@odata.bind" if discovered_resource_nav else "Resource@odata.bind"
        payload[status_key] = f"/bookingstatuses({booking_status_id})"
        payload[resource_key] = f"/bookableresources({_normalize_guid(resource_id)})"

        # Link to Work Order when caller has it (best-effort; orgs can differ).
        if work_order_id:
            discovered_wo_nav = self.try_get_many_to_one_nav_property_for_attribute(
                referencing_entity_logical_name="bookableresourcebooking",
                referencing_attribute_logical_name="msdyn_workorder",
            )
            if discovered_wo_nav:
                payload[f"{discovered_wo_nav}@odata.bind"] = f"/msdyn_workorders({work_order_id})"

        # Environments can differ in the navigation-property name for the requirement lookup.
        discovered_req_nav = self.try_get_many_to_one_nav_property_for_attribute(
            referencing_entity_logical_name="bookableresourcebooking",
            referencing_attribute_logical_name="msdyn_resourcerequirement",
        )
        requirement_bind = f"/msdyn_resourcerequirements({requirement_id})"

        requirement_bind_candidates: list[str] = []
        if discovered_req_nav:
            requirement_bind_candidates.append(f"{discovered_req_nav}@odata.bind")
        requirement_bind_candidates.extend(
            [
                "msdyn_ResourceRequirement@odata.bind",
            ]
        )

        last_error: str | None = None
        for req_key in requirement_bind_candidates:
            attempt = dict(payload)
            attempt.pop("msdyn_ResourceRequirement@odata.bind", None)
            if discovered_req_nav:
                attempt.pop(f"{discovered_req_nav}@odata.bind", None)
            attempt[req_key] = requirement_bind
            try:
                booking = self.create_bookable_resource_booking(attempt)
                return {
                    "status": "ok",
                    "booking": booking,
                    "requirement": {"id": requirement_id},
                    "work_order": ({"id": work_order_id} if work_order_id else None),
                    "selected_slot": {"slot_id": slot_id, "resource_id": resource_id, "start": start, "end": end},
                }
            except Exception as e:
                last_error = str(e)
                continue

        raise RuntimeError(last_error or "Failed to create booking for requirement")

    def search_field_service_availability(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
        duration_minutes: int,
        requirement_id: str | None = None,
        max_time_slots: int = 8,
        max_resources: int = 5,
        only_bookable_resource_id: str | None = None,
        latitude: float = 52.41882,
        longitude: float = -1.78605,
        work_location: int = 690970000,
    ) -> dict[str, Any]:
        """Search Field Service availability.

        Preferred when a requirement is provided (supported scheduling model):
        - `msdyn_SearchResourceAvailabilityV2` (if exposed in this org)
        - `msdyn_SearchResourceAvailability` (legacy requirement-based)

        Preferred when no requirement is provided (supported self-scheduling):
        - `msdyn_SearchResourceAvailabilityForRequirementGroup` (Option B)

        Fallback (demo reliability / matches UI): Schedule Board UFX pipeline via `msdyn_FpsAction` (job type 403).

        Returns a normalized result with `slots` whose `slot_id` format is:
        `<resourceId>|<startIso>|<endIso>` (compatible with booking helper).
        """

        start_iso = _iso(start_utc)
        end_iso = _iso(end_utc)
        duration_minutes = int(duration_minutes)
        max_time_slots = int(max_time_slots)
        max_resources = int(max_resources)

        only_resource_norm: str | None = None
        if isinstance(only_bookable_resource_id, str) and only_bookable_resource_id.strip():
            try:
                only_resource_norm = _normalize_guid(only_bookable_resource_id)
            except Exception:
                only_resource_norm = only_bookable_resource_id.strip()

        action_errors: dict[str, Any] = {}

        def _looks_like_placeholder_entities(items: list[Any]) -> bool:
            # In this org we saw navigation collections come back as a list of
            # {"@odata.type":"#Microsoft.Dynamics.CRM.organization"}.
            if not items:
                return False
            placeholder_count = 0
            for it in items:
                if not isinstance(it, dict):
                    continue
                keys = set(it.keys())
                if keys == {"@odata.type"} and str(it.get("@odata.type")).endswith(".organization"):
                    placeholder_count += 1
            return placeholder_count == len(items)

        def _normalize_time_slots(raw_response: dict[str, Any]) -> list[dict[str, Any]]:
            time_slots = (
                raw_response.get("TimeSlots")
                or raw_response.get("timeSlots")
                or raw_response.get("Timeslots")
                or raw_response.get("timeslots")
            )
            if not isinstance(time_slots, list) or _looks_like_placeholder_entities(time_slots):
                return []

            slots: list[dict[str, Any]] = []
            for ts in time_slots:
                if not isinstance(ts, dict):
                    continue

                start = ts.get("Start") or ts.get("start") or ts.get("StartTime") or ts.get("startTime") or ts.get("StartDate")
                end = ts.get("End") or ts.get("end") or ts.get("EndTime") or ts.get("endTime") or ts.get("EndDate")

                resource = ts.get("Resource") or ts.get("resource") or ts.get("BookableResource") or ts.get("bookableResource")
                resource_id = None
                resource_name = None

                if isinstance(resource, dict):
                    resource_id = resource.get("Id") or resource.get("id") or resource.get("bookableresourceid")
                    resource_name = resource.get("Name") or resource.get("name")
                elif isinstance(resource, str):
                    resource_id = resource

                # Some shapes include top-level ResourceId.
                resource_id = resource_id or ts.get("ResourceId") or ts.get("resourceId")

                if only_resource_norm:
                    if not resource_id:
                        continue
                    try:
                        if _normalize_guid(str(resource_id)) != only_resource_norm:
                            continue
                    except Exception:
                        if str(resource_id).strip().lower() != str(only_resource_norm).strip().lower():
                            continue

                if not start or not end:
                    continue

                slot_id = f"{resource_id or 'unknown'}|{start}|{end}"
                slots.append(
                    {
                        "slot_id": slot_id,
                        "start": start,
                        "end": end,
                        "resource_id": resource_id,
                        "resource_name": resource_name,
                        "raw": ts,
                    }
                )

            try:
                slots.sort(key=lambda s: _parse_iso_datetime(str(s.get("start"))))
            except Exception:
                pass
            if max_time_slots > 0:
                slots = slots[:max_time_slots]
            return slots

        def _try_get_schedule_board_setting_id() -> str | None:
            try:
                sb = self._get(
                    "msdyn_scheduleboardsettinges?$select=msdyn_scheduleboardsettingid&$top=1",
                    include_annotations=False,
                )
                sb_items = list(sb.get("value", [])) if isinstance(sb, dict) else []
                if sb_items and sb_items[0].get("msdyn_scheduleboardsettingid"):
                    return str(sb_items[0]["msdyn_scheduleboardsettingid"])
            except Exception as e:
                action_errors["msdyn_scheduleboardsettinges"] = str(e)
            return None

        def _try_requirement_based_action(action_name: str, *, sb_setting_id: str, req_id: str) -> list[dict[str, Any]]:
            payloads: list[dict[str, Any]] = [
                {
                    "Version": "1.0",
                    "IsWebApi": True,
                    "Requirement": {
                        "@odata.type": "Microsoft.Dynamics.CRM.msdyn_resourcerequirement",
                        "msdyn_resourcerequirementid": req_id,
                        "msdyn_fromdate": start_iso,
                        "msdyn_todate": end_iso,
                        "msdyn_duration": duration_minutes,
                        "msdyn_timewindowstart": start_iso,
                        "msdyn_timewindowend": end_iso,
                        "msdyn_timezonefortimewindow": 85,
                        "msdyn_worklocation": work_location,
                        "msdyn_latitude": latitude,
                        "msdyn_longitude": longitude,
                    },
                    "Settings": {
                        "@odata.type": "Microsoft.Dynamics.CRM.msdyn_scheduleboardsetting",
                        "msdyn_scheduleboardsettingid": sb_setting_id,
                    },
                },
                {
                    "Version": "1.0",
                    "IsWebApi": False,
                    "Requirement": {
                        "@odata.type": "Microsoft.Dynamics.CRM.msdyn_resourcerequirement",
                        "msdyn_resourcerequirementid": req_id,
                        "msdyn_fromdate": start_iso,
                        "msdyn_todate": end_iso,
                        "msdyn_duration": duration_minutes,
                        "msdyn_timewindowstart": start_iso,
                        "msdyn_timewindowend": end_iso,
                        "msdyn_timezonefortimewindow": 85,
                        "msdyn_worklocation": work_location,
                        "msdyn_latitude": latitude,
                        "msdyn_longitude": longitude,
                    },
                    "Settings": {
                        "@odata.type": "Microsoft.Dynamics.CRM.msdyn_scheduleboardsetting",
                        "msdyn_scheduleboardsettingid": sb_setting_id,
                    },
                },
            ]

            last_error: str | None = None
            for body in payloads:
                try:
                    raw = self.execute_unbound_action(action_name, body)
                except Exception as e:
                    last_error = str(e)
                    continue

                if isinstance(raw, dict):
                    slots = _normalize_time_slots(raw)
                    if slots:
                        return slots

            if last_error:
                action_errors[action_name] = last_error
            return []

        # ----------------------------
        # Requirement-based actions (preferred when requirement is known)
        # ----------------------------
        # Desired default: use msdyn_SearchResourceAvailability to find slots.
        # If a requirement is provided and this path fails, do not fall back to
        # requirement-group/UFX because those are different scheduling models and
        # can mask misconfiguration.
        if requirement_id:
            sb_setting_id = _try_get_schedule_board_setting_id()
            req_id = _normalize_guid(str(requirement_id))
            if not sb_setting_id:
                return {
                    "status": "error",
                    "action": None,
                    "message": "Unable to load Schedule Board Setting id required for requirement-based availability.",
                    "details": action_errors,
                    "slots": [],
                    "raw": {"action_errors": action_errors},
                }

            attempted_actions: list[str] = []
            last_action: str | None = None

            # Try legacy first (requested target), then V2 if present.
            if self.probe_unbound_action_exists("msdyn_SearchResourceAvailability"):
                last_action = "msdyn_SearchResourceAvailability"
                attempted_actions.append(last_action)
                slots_v1 = _try_requirement_based_action(last_action, sb_setting_id=sb_setting_id, req_id=req_id)
                if slots_v1:
                    return {
                        "status": "ok",
                        "action": last_action,
                        "slots": slots_v1,
                        "raw": {
                            "note": "Requirement-based availability search (legacy).",
                            "action_errors": action_errors,
                            "attempted_actions": attempted_actions,
                        },
                    }

            if self.probe_unbound_action_exists("msdyn_SearchResourceAvailabilityV2"):
                last_action = "msdyn_SearchResourceAvailabilityV2"
                attempted_actions.append(last_action)
                slots_v2 = _try_requirement_based_action(last_action, sb_setting_id=sb_setting_id, req_id=req_id)
                if slots_v2:
                    return {
                        "status": "ok",
                        "action": last_action,
                        "slots": slots_v2,
                        "raw": {
                            "note": "Requirement-based availability search (V2).",
                            "action_errors": action_errors,
                            "attempted_actions": attempted_actions,
                        },
                    }

            return {
                "status": "error",
                "action": last_action,
                "message": "Requirement-based availability returned no slots.",
                "details": {
                    **action_errors,
                    "attempted_actions": attempted_actions,
                    "inputs": {
                        "requirement_id": req_id,
                        "start": start_iso,
                        "end": end_iso,
                        "duration_minutes": duration_minutes,
                        "work_location": work_location,
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                },
                "slots": [],
                "raw": {"action_errors": action_errors, "attempted_actions": attempted_actions},
            }

        # ----------------------------
        # Option B (primary): self-scheduling via requirement group
        # ----------------------------
        option_b_error: str | None = None
        try:
            if not self.probe_unbound_action_exists("msdyn_SearchResourceAvailabilityForRequirementGroup"):
                raise RuntimeError("Action msdyn_SearchResourceAvailabilityForRequirementGroup not available")

            effective_max_resources = max_resources
            # When we intend to filter to a single known resource, ask the platform for more
            # candidates to reduce the chance our target resource gets trimmed out upstream.
            if only_resource_norm and effective_max_resources < 25:
                effective_max_resources = 25

            settings_b: dict[str, Any] = {
                "ConsiderTravelTime": True,
                "ConsiderResourceCalendar": True,
                "ConsiderBookings": True,
                "ReturnBestSlots": True,
                "MaxNumberOfResources": effective_max_resources,
                "MaxNumberOfTimeSlots": max_time_slots,
            }

            # RequirementGroup is a crmbaseentity; orgs differ in which keys they accept.
            requirement_group_a = {
                "StartDate": start_iso,
                "EndDate": end_iso,
                "Duration": duration_minutes,
                "Latitude": latitude,
                "Longitude": longitude,
                "WorkLocation": work_location,
                "TimeZoneCode": 85,
            }
            requirement_group_b = {
                "msdyn_fromdate": start_iso,
                "msdyn_todate": end_iso,
                "msdyn_duration": duration_minutes,
                "msdyn_worklocation": work_location,
                "TimeZoneCode": 85,
            }

            candidate_payloads: list[dict[str, Any]] = [
                {
                    "Version": "1.0",
                    "IsWebApi": True,
                    "RequirementGroup": requirement_group_a,
                    "Settings": settings_b,
                },
                {
                    "Version": "1.0",
                    "IsWebApi": True,
                    "RequirementGroup": requirement_group_b,
                    "Settings": settings_b,
                },
            ]

            for body in candidate_payloads:
                try:
                    raw_b = self.execute_unbound_action("msdyn_SearchResourceAvailabilityForRequirementGroup", body)
                except httpx.HTTPStatusError as e:
                    option_b_error = f"{e.response.status_code} {e.response.text}".strip()
                    continue
                except Exception as e:
                    option_b_error = str(e)
                    continue

                if isinstance(raw_b, dict):
                    slots_b = _normalize_time_slots(raw_b)
                    if slots_b:
                        return {
                            "status": "ok",
                            "action": "msdyn_SearchResourceAvailabilityForRequirementGroup",
                            "slots": slots_b,
                            "raw": {
                                "note": "Primary path: requirement-group availability search (self-scheduling).",
                                "action_errors": action_errors,
                            },
                        }
        except Exception as e:
            option_b_error = str(e)

        # ----------------------------
        # Fallback: Schedule Board UFX pipeline
        # ----------------------------

        # 1) Load Schedule Board settings (for filters)
        sb = self._get(
            "msdyn_scheduleboardsettinges?$select=msdyn_scheduleboardsettingid,msdyn_filtervalues,_msdyn_retrieveresourcesquery_value&$top=1",
            include_annotations=True,
        )
        sb_items = list(sb.get("value", [])) if isinstance(sb, dict) else []
        sb_item = sb_items[0] if sb_items else {}

        # Note: for UFX job 403 we use the Booking Setup Metadata resources query id.
        retrieve_resources_query_id = sb_item.get("_msdyn_retrieveresourcesquery_value")

        # 2) Load Booking Setup Metadata (needed by UFX + contains query ids)
        bsm = self._get(
            "msdyn_bookingsetupmetadatas?$select=msdyn_bookingsetupmetadataid,msdyn_entitylogicalname,_msdyn_retrieveresourcesquery_value,_msdyn_retrieveconstraintsquery_value&$filter=msdyn_entitylogicalname eq 'none'&$top=1",
            include_annotations=True,
        )
        bsm_items = list(bsm.get("value", [])) if isinstance(bsm, dict) else []
        bsm_item = bsm_items[0] if bsm_items else {}
        booking_setup_metadata_id = bsm_item.get("msdyn_bookingsetupmetadataid")
        resources_query_id = bsm_item.get("_msdyn_retrieveresourcesquery_value")
        constraints_query_id = bsm_item.get("_msdyn_retrieveconstraintsquery_value")

        if not resources_query_id:
            # Fallback: some orgs may have query id on schedule board setting.
            resources_query_id = retrieve_resources_query_id

        if not resources_query_id:
            return {
                "status": "error",
                "message": "Unable to locate RetrieveResourcesQueryId for UFX availability.",
                "details": "Missing _msdyn_retrieveresourcesquery_value on msdyn_bookingsetupmetadata (entitylogicalname='none') and on schedule board setting.",
                "slots": [],
                "action": "msdyn_FpsAction/403",
                "raw": {"action_errors": action_errors, "option_b_error": option_b_error, "constraints_query_id": constraints_query_id},
            }

        if not booking_setup_metadata_id:
            return {
                "status": "error",
                "message": "Unable to locate Booking Setup Metadata record (entitylogicalname='none').",
                "details": "msdyn_bookingsetupmetadatas query returned no rows.",
                "slots": [],
                "action": "msdyn_FpsAction/403",
                "raw": {"action_errors": action_errors, "option_b_error": option_b_error, "constraints_query_id": constraints_query_id},
            }

        # 3) Requirement id (UFX expects an entity reference).
        if requirement_id:
            requirement_id = _normalize_guid(requirement_id)
        else:
            try:
                rr = self._get(
                    "msdyn_resourcerequirements?$select=msdyn_resourcerequirementid&$orderby=createdon desc&$top=1",
                    include_annotations=False,
                )
                rr_items = list(rr.get("value", [])) if isinstance(rr, dict) else []
                if rr_items:
                    requirement_id = rr_items[0].get("msdyn_resourcerequirementid")
            except Exception:
                # If ordering fails in some orgs, try without it.
                rr = self._get(
                    "msdyn_resourcerequirements?$select=msdyn_resourcerequirementid&$top=1",
                    include_annotations=False,
                )
                rr_items = list(rr.get("value", [])) if isinstance(rr, dict) else []
                if rr_items:
                    requirement_id = rr_items[0].get("msdyn_resourcerequirementid")

        if not requirement_id:
            return {
                "status": "error",
                "message": "Unable to locate a seed resource requirement id.",
                "details": "msdyn_resourcerequirements query returned no rows.",
                "slots": [],
                "action": "msdyn_FpsAction/403",
                "raw": {"action_errors": action_errors, "option_b_error": option_b_error, "constraints_query_id": constraints_query_id},
            }

        # 4) Build ResourceTypes from schedule board filter values (fallback to 'User' = 3)
        resource_types: list[dict[str, Any]] = [{"option": 3, "option@ufx-type": "option"}]
        filter_values_raw = sb_item.get("msdyn_filtervalues")
        if isinstance(filter_values_raw, str) and filter_values_raw.strip():
            try:
                fv = json.loads(filter_values_raw)
                rt = fv.get("ResourceTypes") if isinstance(fv, dict) else None
                if isinstance(rt, list) and rt:
                    resource_types = []
                    for v in rt:
                        try:
                            resource_types.append({"option": int(v), "option@ufx-type": "option"})
                        except Exception:
                            continue
                    if not resource_types:
                        resource_types = [{"option": 3, "option@ufx-type": "option"}]
            except Exception:
                pass

        # 5) UFX job 403 payload (aligns with the Schedule Board pipeline)
        request_info: dict[str, Any] = {
            "ResourceTypes": resource_types,
            "Duration": duration_minutes,
            "Requirement": {
                "msdyn_resourcerequirementid": str(requirement_id),
                "msdyn_fromdate": start_iso,
                "msdyn_todate": end_iso,
                "msdyn_duration": duration_minutes,
                "RealTimeMode": True,
                "IgnoreTravelTime": True,
                "IgnoreDuration": False,
                "ForceDateRange": True,
                "Radius": 0,
            },
        }

        # Remove nulls (server-side code can be picky)
        def _prune(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: _prune(v) for k, v in obj.items() if v is not None}
            if isinstance(obj, list):
                return [_prune(v) for v in obj]
            return obj

        request_info = _prune(request_info)

        input_param_403 = json.dumps({"RetrieveResourcesQueryId": str(resources_query_id), "Bag": json.dumps(request_info)})

        try:
            fps_response = self.execute_unbound_action(
                "msdyn_FpsAction",
                {
                    "Type": 403,
                    "InputParameter": input_param_403,
                },
            )
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "message": "UFX availability call failed.",
                "details": f"{e.response.status_code} {e.response.text}".strip(),
                "slots": [],
                "action": "msdyn_FpsAction/403",
                "raw": {"option_b_error": option_b_error, "constraints_query_id": constraints_query_id, "action_errors": action_errors},
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "UFX availability call failed.",
                "details": str(e),
                "slots": [],
                "action": "msdyn_FpsAction/403",
                "raw": {"option_b_error": option_b_error, "constraints_query_id": constraints_query_id, "action_errors": action_errors},
            }

        output_raw = fps_response.get("OutputParameter") if isinstance(fps_response, dict) else None
        if not isinstance(output_raw, str) or not output_raw.strip():
            return {
                "status": "error",
                "message": "UFX availability call returned no OutputParameter.",
                "details": {"fps_response_keys": list(fps_response.keys()) if isinstance(fps_response, dict) else None},
                "slots": [],
                "action": "msdyn_FpsAction/403",
            }

        try:
            ufx = json.loads(output_raw)
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to parse UFX OutputParameter JSON.",
                "details": str(e),
                "slots": [],
                "action": "msdyn_FpsAction/403",
            }

        results = ufx.get("Results") if isinstance(ufx, dict) else None
        if not isinstance(results, list):
            results = []

        slots: list[dict[str, Any]] = []
        for r in results:
            if not isinstance(r, dict):
                continue
            attrs = r.get("Attributes") if isinstance(r.get("Attributes"), dict) else r

            start = (
                attrs.get("StartTime")
                or attrs.get("starttime")
                or attrs.get("Start")
                or attrs.get("start")
                or attrs.get("StartDate")
                or attrs.get("startdate")
            )
            end = (
                attrs.get("EndTime")
                or attrs.get("endtime")
                or attrs.get("End")
                or attrs.get("end")
                or attrs.get("EndDate")
                or attrs.get("enddate")
            )
            if not isinstance(start, str) or not isinstance(end, str):
                continue

            resource = attrs.get("Resource") or attrs.get("resource")
            resource_id = None
            resource_name = None
            if isinstance(resource, dict):
                resource_id = resource.get("Id")
                resource_name = resource.get("Name")
            elif isinstance(resource, str):
                resource_id = resource

            # Some shapes store lookups as _resource_value + formatted name annotation.
            resource_id = resource_id or attrs.get("_resource_value") or attrs.get("_resourceid_value")
            resource_name = resource_name or attrs.get(
                "_resource_value@OData.Community.Display.V1.FormattedValue"
            ) or attrs.get("_resourceid_value@OData.Community.Display.V1.FormattedValue")

            # UFX often uses @ufx-formatvalue for formatted lookup display names.
            resource_name = resource_name or attrs.get("Resource@ufx-formatvalue") or attrs.get("resource@ufx-formatvalue")

            # Fall back to the 'Resources' array for names if needed.
            if not resource_name:
                resource_name = r.get("ResourceName")

            if not resource_id:
                continue

            if only_resource_norm:
                try:
                    if _normalize_guid(str(resource_id)) != only_resource_norm:
                        continue
                except Exception:
                    if str(resource_id).strip().lower() != str(only_resource_norm).strip().lower():
                        continue

            slot_id = f"{resource_id}|{start}|{end}"
            slots.append(
                {
                    "slot_id": slot_id,
                    "start": start,
                    "end": end,
                    "resource_id": resource_id,
                    "resource_name": resource_name,
                    "raw": {"id": r.get("Id"), "type": r.get("Type") or attrs.get("Type")},
                }
            )

        # Sort and limit (Schedule Board can return many rows)
        try:
            slots.sort(key=lambda s: _parse_iso_datetime(str(s.get("start"))))
        except Exception:
            pass

        if max_time_slots > 0:
            slots = slots[:max_time_slots]

        debug_sample: dict[str, Any] | None = None
        if not slots and results and isinstance(results[0], dict):
            first = results[0]
            first_attrs = first.get("Attributes") if isinstance(first.get("Attributes"), dict) else None
            debug_sample = {
                "result_keys": list(first.keys())[:50],
                "attributes_keys": list(first_attrs.keys())[:50] if isinstance(first_attrs, dict) else None,
                "type": first.get("Type") or (first_attrs.get("Type") if isinstance(first_attrs, dict) else None),
                "start_candidates": {
                    k: (first_attrs.get(k) if isinstance(first_attrs, dict) else first.get(k))
                    for k in ["StartTime", "EndTime", "starttime", "endtime", "Start", "End", "StartDate", "EndDate"]
                    if (isinstance(first_attrs, dict) and k in first_attrs) or (k in first)
                },
            }

        return {
            "status": "ok",
            "action": "msdyn_FpsAction/403",
            "slots": slots,
            "raw": {
                "results_count": len(results),
                "resources_count": len(ufx.get("Resources", [])) if isinstance(ufx, dict) and isinstance(ufx.get("Resources"), list) else None,
                "exception_message": ufx.get("ExceptionMessage") if isinstance(ufx, dict) else None,
                "option_b_error": option_b_error,
                "debug_sample": debug_sample,
                "action_errors": action_errors,
            },
        }

    def book_requirement_via_schedule_assistant(
        self,
        *,
        requirement_id: str,
        schedule_start_utc: datetime,
        schedule_end_utc: datetime,
        apply_option: int = 1,
    ) -> dict[str, Any]:
        """Book a requirement using the same scheduling pipeline as the Schedule Board.

        Uses:
        - `msdyn_FpsAction` Type 153 (Load & Get Resources / creates optimization request)
        - `msdyn_BookResourceSchedulingSuggestions` (applies the suggestions)
        """
        requirement_id = _normalize_guid(requirement_id)

        sb = self._get(
            "msdyn_scheduleboardsettinges?$select=msdyn_scheduleboardsettingid&$top=1",
            include_annotations=False,
        )
        sb_items = list(sb.get("value", [])) if isinstance(sb, dict) else []
        if not sb_items or not sb_items[0].get("msdyn_scheduleboardsettingid"):
            return {"status": "error", "message": "No schedule board setting found."}
        schedule_board_setting_id = str(sb_items[0]["msdyn_scheduleboardsettingid"])

        input_obj = {
            "Id": requirement_id,
            "LogicalName": "msdyn_resourcerequirement",
            "ScheduleBoardSettingId": schedule_board_setting_id,
            "StartDate": _iso(schedule_start_utc),
            "EndDate": _iso(schedule_end_utc),
        }

        try:
            fps_response = self.execute_unbound_action(
                "msdyn_FpsAction",
                {
                    "Type": 153,
                    "InputParameter": json.dumps(input_obj),
                },
            )
        except Exception as e:
            logger.warning("ScheduleAssistant fps_153 failed for requirement %s: %s", requirement_id, str(e))
            return {
                "status": "error",
                "message": "msdyn_FpsAction/153 failed.",
                "details": str(e),
                "raw": {"input": input_obj},
            }

        outp = fps_response.get("OutputParameter") if isinstance(fps_response, dict) else None
        if not isinstance(outp, str) or not outp.strip():
            return {
                "status": "error",
                "message": "msdyn_FpsAction/153 returned no OutputParameter.",
                "raw": fps_response,
            }

        try:
            obj = json.loads(outp)
        except Exception:
            obj = {"_raw": outp}

        def _find_guid_by_key_contains(o: Any, needle: str) -> str | None:
            # Walk the object tree to find a GUID value for a key that contains the needle.
            stack: list[Any] = [o]
            guid_re = re.compile(r"^[0-9a-fA-F-]{36}$")
            while stack:
                cur = stack.pop()
                if isinstance(cur, dict):
                    for k, v in cur.items():
                        if isinstance(k, str) and needle.lower() in k.lower():
                            if isinstance(v, str) and guid_re.match(v.strip()):
                                return v.strip()
                        stack.append(v)
                elif isinstance(cur, list):
                    stack.extend(cur)
            return None

        optimization_request_id = _find_guid_by_key_contains(obj, "OptimizationRequest")
        if not optimization_request_id:
            optimization_request_id = _find_guid_by_key_contains(obj, "OptimizationRequestId")

        if not optimization_request_id:
            logger.warning(
                "ScheduleAssistant fps_153 missing OptimizationRequestId for requirement %s. Parsed type=%s",
                requirement_id,
                type(obj).__name__,
            )
            return {
                "status": "error",
                "message": "Could not locate OptimizationRequestId in msdyn_FpsAction/153 output.",
                "raw": {"input": input_obj, "fps_153": obj},
            }

        try:
            action_resp = self.execute_unbound_action(
                "msdyn_BookResourceSchedulingSuggestions",
                {"OptimizationRequestId": optimization_request_id, "ApplyOption": int(apply_option)},
            )
        except Exception as e:
            logger.warning(
                "ScheduleAssistant apply suggestions failed for requirement %s (opt=%s): %s",
                requirement_id,
                optimization_request_id,
                str(e),
            )
            return {
                "status": "error",
                "message": "msdyn_BookResourceSchedulingSuggestions failed.",
                "details": str(e),
                "raw": {"optimization_request_id": optimization_request_id, "fps_153": obj},
            }

        # Best-effort booking id extraction.
        booking_id = _find_guid_by_key_contains(action_resp, "bookableresourcebooking")
        booking_confirmation = self.try_get_booking_confirmation(booking_id) if booking_id else None
        return {
            "status": "ok",
            "booking": (
                {
                    "id": booking_id,
                    "assigned_resource": (booking_confirmation or {}).get("resource"),
                }
                if booking_id
                else None
            ),
            "raw": {
                "optimization_request_id": optimization_request_id,
                "fps_153": obj,
                "book_action": action_resp,
                "booking_confirmation": booking_confirmation,
            },
        }

    def create_boiler_repair_work_order_and_booking(
        self,
        *,
        slot_id: str,
        priority: str = "normal",
        booking_status_name: str = "Scheduled",
    ) -> dict[str, Any]:
        """Presales demo: create a boiler repair work order + booking."""

        # Slot ID format emitted by search_field_service_availability
        try:
            resource_id, start, end = slot_id.split("|", 2)
        except ValueError as e:
            raise RuntimeError("Invalid slot_id. Expected format: <resourceId>|<start>|<end>") from e

        if resource_id == "unknown":
            # We'll still allow booking if caller wants to pick a default resource.
            resources = self.get_bookable_resources(top=1)
            if not resources:
                raise RuntimeError("No bookable resources found to create a booking.")
            resource_id = str(resources[0].get("bookableresourceid"))

        priority = _normalize_priority(priority)

        # Hardcoded demo values (from provided existing work order payload)
        primary_incident_type_id = "c1033273-2669-ef11-bfe2-000d3a68576d"
        high_priority_id = "d954a64a-dff5-ed11-8e4b-002248a6ca1f"  # High
        work_order_type_id = "e5ccb33e-17bd-ea11-a812-000d3a1b14a2"
        price_list_id = "b9b533c4-2769-ef11-bfe2-000d3a68576d"
        currency_id = "44ed73b4-2769-ef11-bfe2-000d3a68576d"
        service_account_id = "f0622224-3e61-ef11-bfe2-002248a36d0e"

        priority_id: str | None = None
        if priority == "high":
            priority_id = high_priority_id
        else:
            priority_id = None

        # Create Work Order
        work_order_payload: dict[str, Any] = {
            "msdyn_primaryincidentdescription": "No Heating Household (Boiler Problems)",
            "msdyn_primaryincidentestimatedduration": 120,
            "msdyn_totalestimatedduration": 120,
            "msdyn_instructions": "Slow to answer the door. Please allow for this as hard of hearing and mobility issues. Call mobile upon arrival.",
            "msdyn_worklocation": 690970000,
            "msdyn_address1": "1 Ashleigh Road",
            "msdyn_city": "Birmingham",
            "msdyn_postalcode": "B91 1AE",
            "msdyn_latitude": 52.41882,
            "msdyn_longitude": -1.78605,
            # Lookups
            "msdyn_primaryincidenttype@odata.bind": f"/msdyn_incidenttypes({primary_incident_type_id})",
            "msdyn_workordertype@odata.bind": f"/msdyn_workordertypes({work_order_type_id})",
            "msdyn_pricelist@odata.bind": f"/pricelevels({price_list_id})",
            "transactioncurrencyid@odata.bind": f"/transactioncurrencies({currency_id})",
            "msdyn_serviceaccount@odata.bind": f"/accounts({service_account_id})",
            "msdyn_billingaccount@odata.bind": f"/accounts({service_account_id})",
        }
        if priority_id:
            work_order_payload["msdyn_priority@odata.bind"] = f"/msdyn_priorities({priority_id})"
        wo = self.create_record("msdyn_workorders", work_order_payload)
        work_order_id = wo["id"]

        booking_status_id = self.get_booking_status_id(name=booking_status_name)

        # Duration in minutes is commonly required/validated by Field Service.
        try:
            duration = int((_parse_iso_datetime(end) - _parse_iso_datetime(start)).total_seconds() // 60)
        except Exception:
            duration = 120

        # Create Bookable Resource Booking (link to work order)
        # Prefer the more explicit lookup names (some orgs reject the shorter nav property names).
        booking_payload: dict[str, Any] = {
            "starttime": start,
            "endtime": end,
            "duration": duration,
            "bookingstatusid@odata.bind": f"/bookingstatuses({booking_status_id})",
            "resourceid@odata.bind": f"/bookableresources({resource_id})",
            "msdyn_workorder@odata.bind": f"/msdyn_workorders({work_order_id})",
            "name": DEFAULT_DEMO_JOB_NAME,
        }
        booking = self.create_bookable_resource_booking(booking_payload)

        return {
            "status": "ok",
            "work_order": {"id": work_order_id},
            "booking": booking,
            "selected_slot": {"slot_id": slot_id, "resource_id": resource_id, "start": start, "end": end},
            "note": "Presales demo: boiler issue is hardcoded; priority defaults to Normal unless set to High.",
        }

    def create_boiler_repair_case_work_order_and_booking(
        self,
        *,
        slot_id: str,
        contact_id: str,
        priority: str = "normal",
        booking_status_name: str = "Scheduled",
    ) -> dict[str, Any]:
        """Presales demo: create a Case (for the contact) + Work Order (linked to the Case) + Booking."""

        priority = _normalize_priority(priority)

        contact_id = _normalize_guid(contact_id)

        # Create Case (incident) against the contact
        # caseorigincode: default option set values are typically 1=Phone, 2=Email, 3=Web.
        # prioritycode: default option set values are typically 1=High, 2=Normal, 3=Low.
        case_payload: dict[str, Any] = {
            "title": DEFAULT_DEMO_JOB_NAME,
            "description": (
                "Customer reported no heating/hot water. "
                + ("High priority requested. " if priority == "high" else "")
                + "Boiler repair request (presales demo)."
            ),
            "customerid_contact@odata.bind": f"/contacts({contact_id})",
            "caseorigincode": 3,
            "prioritycode": 1 if priority == "high" else 2,
        }
        case = self.create_record("incidents", case_payload)
        case_id = case["id"]

        # Create Work Order (same defaults as the existing demo flow) and link to Case
        try:
            resource_id, start, end = slot_id.split("|", 2)
        except ValueError as e:
            raise RuntimeError("Invalid slot_id. Expected format: <resourceId>|<start>|<end>") from e

        if resource_id == "unknown":
            resources = self.get_bookable_resources(top=1)
            if not resources:
                raise RuntimeError("No bookable resources found to create a booking.")
            resource_id = str(resources[0].get("bookableresourceid"))

        primary_incident_type_id = "c1033273-2669-ef11-bfe2-000d3a68576d"
        high_priority_id = "d954a64a-dff5-ed11-8e4b-002248a6ca1f"  # High
        work_order_type_id = "e5ccb33e-17bd-ea11-a812-000d3a1b14a2"
        price_list_id = "b9b533c4-2769-ef11-bfe2-000d3a68576d"
        currency_id = "44ed73b4-2769-ef11-bfe2-000d3a68576d"
        service_account_id = "f0622224-3e61-ef11-bfe2-002248a36d0e"

        priority_id: str | None = None
        if priority == "high":
            priority_id = high_priority_id
        else:
            priority_id = None

        work_order_payload: dict[str, Any] = {
            "msdyn_primaryincidentdescription": "No Heating Household (Boiler Problems)",
            "msdyn_primaryincidentestimatedduration": 120,
            "msdyn_totalestimatedduration": 120,
            "msdyn_instructions": "Slow to answer the door. Please allow for this as hard of hearing and mobility issues. Call mobile upon arrival.",
            "msdyn_worklocation": 690970000,
            "msdyn_address1": "1 Ashleigh Road",
            "msdyn_city": "Birmingham",
            "msdyn_postalcode": "B91 1AE",
            "msdyn_latitude": 52.41882,
            "msdyn_longitude": -1.78605,
            # Lookups
            "msdyn_primaryincidenttype@odata.bind": f"/msdyn_incidenttypes({primary_incident_type_id})",
            "msdyn_workordertype@odata.bind": f"/msdyn_workordertypes({work_order_type_id})",
            "msdyn_pricelist@odata.bind": f"/pricelevels({price_list_id})",
            "transactioncurrencyid@odata.bind": f"/transactioncurrencies({currency_id})",
            "msdyn_serviceaccount@odata.bind": f"/accounts({service_account_id})",
            "msdyn_billingaccount@odata.bind": f"/accounts({service_account_id})",
            # Link to Case
            "msdyn_servicerequest@odata.bind": f"/incidents({case_id})",
        }
        if priority_id:
            work_order_payload["msdyn_priority@odata.bind"] = f"/msdyn_priorities({priority_id})"
        wo = self.create_record("msdyn_workorders", work_order_payload)
        work_order_id = wo["id"]

        booking_status_id = self.get_booking_status_id(name=booking_status_name)

        try:
            duration = int((_parse_iso_datetime(end) - _parse_iso_datetime(start)).total_seconds() // 60)
        except Exception:
            duration = 120

        booking_payload: dict[str, Any] = {
            "starttime": start,
            "endtime": end,
            "duration": duration,
            "bookingstatusid@odata.bind": f"/bookingstatuses({booking_status_id})",
            "resourceid@odata.bind": f"/bookableresources({resource_id})",
            "msdyn_workorder@odata.bind": f"/msdyn_workorders({work_order_id})",
            "name": DEFAULT_DEMO_JOB_NAME,
        }

        try:
            booking = self.create_bookable_resource_booking(booking_payload)
            return {
                "status": "ok",
                "case": {"id": case_id},
                "work_order": {"id": work_order_id},
                "booking": booking,
                "selected_slot": {"slot_id": slot_id, "resource_id": resource_id, "start": start, "end": end},
                "note": "Presales demo: created Case (Web origin) → Work Order (linked) → Booking. Priority defaults to Normal unless set to High.",
            }
        except Exception as e:
            return {
                "status": "partial",
                "message": "Case and Work Order were created, but booking creation failed.",
                "case": {"id": case_id},
                "work_order": {"id": work_order_id},
                "selected_slot": {"slot_id": slot_id, "resource_id": resource_id, "start": start, "end": end},
                "booking_payload": booking_payload,
                "details": str(e),
                "next_step": {
                    "tool": "create_booking_for_work_order",
                    "args": {"slot_id": slot_id, "work_order_id": work_order_id, "booking_status_name": booking_status_name},
                    "note": "Use this to retry booking without creating a new Case/Work Order.",
                },
            }

    def create_booking_for_work_order(
        self,
        *,
        slot_id: str,
        work_order_id: str,
        booking_status_name: str = "Scheduled",
    ) -> dict[str, Any]:
        """Create a Bookable Resource Booking for an existing Work Order.

        This is a retry-friendly helper to avoid duplicating Cases/Work Orders.
        """

        work_order_id = _normalize_guid(work_order_id)

        try:
            resource_id, start, end = slot_id.split("|", 2)
        except ValueError as e:
            raise RuntimeError("Invalid slot_id. Expected format: <resourceId>|<start>|<end>") from e

        if resource_id == "unknown":
            resources = self.get_bookable_resources(top=1)
            if not resources:
                raise RuntimeError("No bookable resources found to create a booking.")
            resource_id = str(resources[0].get("bookableresourceid"))

        booking_status_id = self.get_booking_status_id(name=booking_status_name)
        try:
            duration = int((_parse_iso_datetime(end) - _parse_iso_datetime(start)).total_seconds() // 60)
        except Exception:
            duration = 120

        payload: dict[str, Any] = {
            "starttime": start,
            "endtime": end,
            "duration": duration,
            "bookingstatusid@odata.bind": f"/bookingstatuses({booking_status_id})",
            "resourceid@odata.bind": f"/bookableresources({resource_id})",
            "msdyn_workorder@odata.bind": f"/msdyn_workorders({work_order_id})",
            "name": DEFAULT_DEMO_JOB_NAME,
        }
        booking = self.create_bookable_resource_booking(payload)
        return {
            "status": "ok",
            "work_order": {"id": work_order_id},
            "booking": booking,
            "selected_slot": {"slot_id": slot_id, "resource_id": resource_id, "start": start, "end": end},
        }


def compute_day_window_utc(which: str) -> tuple[datetime, datetime]:
    """Compute a UK business-hours window in UTC for 'today', 'tomorrow', or 'today_or_tomorrow'."""
    w = (which or "").strip().lower()
    if w not in {"today", "tomorrow", "today_or_tomorrow"}:
        raise ValueError("which must be one of: today, tomorrow, today_or_tomorrow")

    try:
        tz = ZoneInfo("Europe/London")
    except Exception:
        # Common on Windows or minimal containers without tzdata installed.
        # For a presales demo, falling back to UTC is better than failing.
        tz = timezone.utc
    now_local = datetime.now(tz)
    base_date = now_local.date()

    if w == "tomorrow":
        base_date = base_date + timedelta(days=1)

    start_local = datetime.combine(base_date, datetime.min.time(), tzinfo=tz).replace(hour=8, minute=0, second=0)
    end_local = datetime.combine(base_date, datetime.min.time(), tzinfo=tz).replace(hour=18, minute=0, second=0)

    if w == "today" and now_local > start_local:
        start_local = now_local

    if w == "today_or_tomorrow":
        # From now (or 08:00) through end-of-day tomorrow (18:00)
        today_start = datetime.combine(now_local.date(), datetime.min.time(), tzinfo=tz).replace(
            hour=8, minute=0, second=0
        )
        start_local = now_local if now_local > today_start else today_start
        tomorrow = now_local.date() + timedelta(days=1)
        end_local = datetime.combine(tomorrow, datetime.min.time(), tzinfo=tz).replace(hour=18, minute=0, second=0)

    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)
