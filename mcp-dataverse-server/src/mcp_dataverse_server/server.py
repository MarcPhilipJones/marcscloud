from __future__ import annotations

from typing import Any, Callable
from datetime import datetime, timedelta, timezone
import json
import logging
import os
import time
from zoneinfo import ZoneInfo

import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from .auth import TokenProvider
from .config import load_settings
from .dataverse import DataverseClient, compute_day_window_utc
from .scheduling_service_customer import CustomerSelfServiceSchedulingService


_wire_logger = logging.getLogger("mcp_dataverse_server.mcp_wire")


def _sanitize_for_log(value: Any, *, max_string_len: int = 256, max_depth: int = 6, _depth: int = 0) -> Any:
    if _depth >= max_depth:
        return "<max_depth>"

    if isinstance(value, str):
        if len(value) > max_string_len:
            return value[:max_string_len] + "…"
        return value

    if isinstance(value, (int, float, bool)) or value is None:
        return value

    if isinstance(value, list):
        return [_sanitize_for_log(v, max_string_len=max_string_len, max_depth=max_depth, _depth=_depth + 1) for v in value[:50]]

    if isinstance(value, dict):
        redacted_keys = {
            "authorization",
            "token",
            "access_token",
            "refresh_token",
            "client_secret",
            "secret",
            "password",
        }

        sanitized: dict[str, Any] = {}
        for k, v in list(value.items())[:200]:
            key = str(k)
            if key.lower() in redacted_keys:
                sanitized[key] = "<redacted>"
            else:
                sanitized[key] = _sanitize_for_log(v, max_string_len=max_string_len, max_depth=max_depth, _depth=_depth + 1)
        return sanitized

    # Fallback for unknown types
    try:
        return str(value)
    except Exception:
        return "<unserializable>"


class _McpMessageLoggingMiddleware:
    """Logs MCP SSE message POST bodies to runtime.log (sanitized).

    This is the most reliable place to see which tool is being called and why
    the client may be retrying (e.g., failures, timeouts, disconnects).
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path") or ""
        method = (scope.get("method") or "").upper()

        # Compatibility shim: some MCP clients POST to /sse/messages even when the
        # server is mounted at /messages. Rewrite so the request hits the MCP app.
        downstream_scope = scope
        if method == "POST" and path == "/sse/messages":
            downstream_scope = dict(scope)
            downstream_scope["path"] = "/messages"

        is_message_post = method == "POST" and path.endswith("/messages")
        if not is_message_post:
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        body_parts: list[bytes] = []
        more_body = True
        try:
            while more_body:
                message = await receive()
                if message.get("type") != "http.request":
                    continue
                body_parts.append(message.get("body", b""))
                more_body = bool(message.get("more_body", False))

            body = b"".join(body_parts)

            extracted: dict[str, Any] = {"path": path, "method": method, "bytes": len(body)}
            try:
                payload = json.loads(body.decode("utf-8")) if body else None
                # Common MCP/JSON-RPC shapes include fields like:
                # - {"method": "tools/call", "params": {"name": "...", "arguments": {...}}}
                # - {"type": "call_tool", "name": "...", "arguments": {...}}
                if isinstance(payload, dict):
                    extracted["rpc_method"] = payload.get("method")
                    params = payload.get("params") if isinstance(payload.get("params"), dict) else None
                    if params:
                        extracted["tool_name"] = params.get("name")
                        extracted["tool_arguments"] = _sanitize_for_log(params.get("arguments"))
                    else:
                        extracted["tool_name"] = payload.get("name")
                        extracted["tool_arguments"] = _sanitize_for_log(payload.get("arguments"))
            except Exception as e:
                extracted["parse_error"] = str(e)

            _wire_logger.info("MCP message received: %s", _sanitize_for_log(extracted))

            sent = False

            async def replay_receive() -> dict[str, Any]:
                nonlocal sent
                if sent:
                    return {"type": "http.request", "body": b"", "more_body": False}
                sent = True
                return {"type": "http.request", "body": body, "more_body": False}

            status_code: int | None = None
            resp_body_parts: list[bytes] = []
            resp_body_bytes = 0
            resp_body_limit = 32 * 1024

            async def send_wrapper(message: dict[str, Any]) -> None:
                nonlocal status_code, resp_body_parts, resp_body_bytes
                if message.get("type") == "http.response.start":
                    status_code = int(message.get("status", 0))
                elif message.get("type") == "http.response.body":
                    chunk = message.get("body", b"") or b""
                    if chunk and resp_body_bytes < resp_body_limit:
                        remaining = resp_body_limit - resp_body_bytes
                        resp_body_parts.append(chunk[:remaining])
                        resp_body_bytes += min(len(chunk), remaining)
                await send(message)

            await self.app(downstream_scope, replay_receive, send_wrapper)
            dur_ms = int((time.perf_counter() - start) * 1000)
            _wire_logger.info("MCP message handled: path=%s status=%s duration_ms=%s", path, status_code, dur_ms)

            # Best-effort: log a small, sanitized view of the response payload.
            if resp_body_parts:
                try:
                    raw_text = b"".join(resp_body_parts).decode("utf-8", errors="replace")
                    payload = json.loads(raw_text)
                    _wire_logger.info("MCP message response (truncated): %s", _sanitize_for_log(payload))
                except Exception:
                    # Keep logs lightweight; do not dump opaque binary/large data.
                    pass
        except Exception:
            _wire_logger.exception("Unhandled exception while processing MCP message: path=%s", path)
            raise


def _compute_window_utc(when: str) -> tuple[datetime, datetime]:
    """Compute a UK-centric window in UTC from a small set of demo phrases.

    Supported examples:
    - today, tomorrow, today_or_tomorrow (existing)
    - this week
    - next 5 working days / next five working days / 5 working days
    - next 3 working days / next three working days / 3 working days
    - around midday / midday today / midday tomorrow
    """
    w = (when or "").strip().lower()
    if w in {"today", "tomorrow", "today_or_tomorrow"}:
        return compute_day_window_utc(w)

    try:
        tz = ZoneInfo("Europe/London")
    except Exception:
        tz = timezone.utc

    now_local = datetime.now(tz)

    def _is_working_day(d) -> bool:
        # Monday=0 ... Sunday=6
        return d.weekday() < 5

    def _next_working_date(d):
        cur = d
        while not _is_working_day(cur):
            cur = cur + timedelta(days=1)
        return cur

    def _add_working_days(d, days: int):
        cur = d
        remaining = int(days)
        while remaining > 0:
            cur = cur + timedelta(days=1)
            if _is_working_day(cur):
                remaining -= 1
        return cur

    def _day_window(date_local, start_h: int, start_m: int, end_h: int, end_m: int):
        start_local = datetime.combine(date_local, datetime.min.time(), tzinfo=tz).replace(
            hour=start_h, minute=start_m, second=0
        )
        end_local = datetime.combine(date_local, datetime.min.time(), tzinfo=tz).replace(hour=end_h, minute=end_m, second=0)
        if start_local < now_local and date_local == now_local.date():
            start_local = now_local
        return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)

    # Midday preference (11:00-14:00 local)
    if "midday" in w or "noon" in w:
        base_date = now_local.date()
        if "tomorrow" in w:
            base_date = base_date + timedelta(days=1)
        return _day_window(base_date, 11, 0, 14, 0)

    # This week = from now (or 08:00) through Sunday 18:00 local
    if "this week" in w or w == "week":
        # Python: Monday=0 ... Sunday=6
        days_to_sunday = 6 - now_local.weekday()
        end_date = now_local.date() + timedelta(days=days_to_sunday)
        start_local = datetime.combine(now_local.date(), datetime.min.time(), tzinfo=tz).replace(hour=8, minute=0, second=0)
        if now_local > start_local:
            start_local = now_local
        end_local = datetime.combine(end_date, datetime.min.time(), tzinfo=tz).replace(hour=18, minute=0, second=0)
        return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)

    # Next 5 working days (default customer horizon): from next working slot time through 18:00
    if w in {
        "next 5 working days",
        "next five working days",
        "5 working days",
        "next_5_working_days",
        "next5workingdays",
        "next 5 days",
        "5 days",
    }:
        base_date = _next_working_date(now_local.date())

        # If it's after hours on a working day, start from the next working day.
        start_day_local = base_date
        if _is_working_day(now_local.date()) and now_local.hour >= 18:
            start_day_local = _next_working_date(now_local.date() + timedelta(days=1))

        # Window starts at max(now, 08:00) on the start day.
        start_local = datetime.combine(start_day_local, datetime.min.time(), tzinfo=tz).replace(hour=8, minute=0, second=0)
        if now_local > start_local:
            start_local = now_local

        end_day_local = _add_working_days(start_day_local, 4)  # inclusive of start day = 5 working days
        end_local = datetime.combine(end_day_local, datetime.min.time(), tzinfo=tz).replace(hour=18, minute=0, second=0)
        return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)

    # Next 3 working days (legacy default)
    if w in {"next 3 working days", "next three working days", "3 working days", "next_3_working_days", "next3workingdays"}:
        base_date = _next_working_date(now_local.date())

        # If it's after hours on a working day, start from the next working day.
        start_day_local = base_date
        if _is_working_day(now_local.date()) and now_local.hour >= 18:
            start_day_local = _next_working_date(now_local.date() + timedelta(days=1))

        # Window starts at max(now, 08:00) on the start day.
        start_local = datetime.combine(start_day_local, datetime.min.time(), tzinfo=tz).replace(hour=8, minute=0, second=0)
        if now_local > start_local:
            start_local = now_local

        end_day_local = _add_working_days(start_day_local, 2)  # inclusive of start day = 3 working days
        end_local = datetime.combine(end_day_local, datetime.min.time(), tzinfo=tz).replace(hour=18, minute=0, second=0)
        return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)

    # Default: next 5 working days
    return _compute_window_utc("next 5 working days")


def _get_any(contact: dict[str, Any], keys: list[str]) -> tuple[str | None, Any, Any]:
    """Return (schema_name_used, raw_value, formatted_value) for the first key present."""
    for key in keys:
        if key in contact:
            raw = contact.get(key)
            formatted = contact.get(f"{key}@OData.Community.Display.V1.FormattedValue")
            return key, raw, formatted
    return None, None, None


def _build_contact_customer_profile(contact: dict[str, Any]) -> dict[str, Any]:
    # Candidate keys are listed with both casing variants because Dataverse
    # logical names are case-insensitive but payload keys may vary.
    field_map: list[tuple[str, list[str]]] = [
        ("EV Owner", ["mj_Utility_EV_Owner", "mj_utility_ev_owner"]),
        ("Home EV Charger", ["mj_HomeEVCharger", "mj_homeevcharger"]),
        ("Do you have a Smart Meter?", ["mj_DoyouhaveSmartMeter", "mj_doyouhavesmartmeter"]),
        ("Do you have a Hive Thermostat?", ["mj_DoyouhaveHiveThermostat", "mj_doyouhavehivethermostat"]),
        ("Do you have Smart Radiator Valves?", ["mj_DoyouhaveSmartRadiatorValves", "mj_doyouhavesmartradiatorvalves"]),
        ("Energy Tariff", ["mj_EnergyTariff", "mj_energytariff"]),
        ("Boiler Make", ["mj_BoilerMake", "mj_boilermake"]),
        ("Boiler Model", ["mj_BoilerModel", "mj_boilermodel"]),
        ("Conversation Logic", ["mj_ConversationLogic", "mj_conversationlogic"]),
        ("Conversation Points", ["mj_ConversationPoints", "mj_conversationpoints"]),
        ("HomeCare Cover", ["mj_HomeCareCover", "mj_homecarecover"]),
        ("HomeCare Type of Cover", ["mj_HomeCareTypeofCover", "mj_homecaretypeofcover"]),
        ("Initiate Outbound Call", ["mj_InitiateOutboundCall", "mj_initiateoutboundcall"]),
        ("Installation Date", ["mj_InstallationDate", "mj_installationdate"]),
        ("Primary Store", ["mj_PrimaryStore", "mj_primarystore"]),
        ("Priority Register", ["mj_PriorityRegister", "mj_priorityregister"]),
        ("Refresh Analysis", ["mj_RefreshAnalysis", "mj_refreshanalysis"]),
        ("Repaired Recently", ["mj_RepairedRecently", "mj_repairedrecently"]),
    ]

    profile: dict[str, Any] = {}
    for label, keys in field_map:
        schema, value, formatted = _get_any(contact, keys)
        profile[label] = {
            "schema": schema or keys[0],
            "value": value,
            "formatted": formatted,
            "present": schema is not None,
        }

    return {
        "contactid": contact.get("contactid"),
        "fullname": contact.get("fullname"),
        "firstname": contact.get("firstname"),
        "lastname": contact.get("lastname"),
        "profile": profile,
        "note": "Fields may be null if not populated in Dataverse; 'present' indicates the attribute was returned in the payload.",
    }


class _BearerTokenMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, token: str) -> None:
        super().__init__(app)
        self._token = token

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        auth = request.headers.get("authorization", "")
        expected = f"Bearer {self._token}"
        if auth != expected:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


def build_mcp() -> FastMCP:
    settings = load_settings()

    read_tool = ToolAnnotations(readOnlyHint=True, openWorldHint=True)
    write_tool = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True)

    token_provider = TokenProvider(
        tenant_id=settings.dataverse_tenant_id,
        client_id=settings.dataverse_client_id,
        client_secret=settings.dataverse_client_secret,
        resource=settings.dataverse_base_url,
    )
    dv = DataverseClient(
        base_url=settings.dataverse_base_url,
        api_version=settings.dataverse_api_version,
        token_provider=token_provider,
    )
    fs = CustomerSelfServiceSchedulingService(
        dv,
        demo_bookable_resource_id=settings.demo_bookable_resource_id,
        demo_resource_name=settings.demo_resource_name,
        demo_job_name=settings.demo_job_name,
        demo_fast=settings.demo_fast,
        clear_demo_caches_on_start=settings.clear_demo_caches_on_start,
    )
    # NOTE: Avoid Dataverse network calls during server startup.
    # Capability probing is done lazily during tool execution.

    # For local + ngrok demos we disable DNS rebinding protection because the
    # public ngrok hostname changes and would otherwise be rejected (421).
    # Do NOT use this setting for production hosting.
    mcp = FastMCP(
        "dataverse-contacts",
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )

    @mcp.tool(annotations=read_tool)
    def search_contacts(query: str, top: int = 5) -> dict[str, Any]:
        """Search contacts by name/email/phone.

        Returns a short list of matching contacts.
        """
        try:
            results = dv.search_contacts(query=query, top=top)
            return {"status": "ok", "count": len(results), "results": results}
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to search contacts.",
                "details": str(e),
                "count": 0,
                "results": [],
            }

    @mcp.tool(annotations=read_tool)
    def get_contact(contact_id: str) -> dict[str, Any]:
        """Get a single contact by GUID."""
        try:
            contact = dv.get_contact(contact_id, select=None)
            # Put the custom-field summary directly into the contact payload so the
            # model can answer questions like "Does Chris have an EV?" without
            # needing a separate tool call.
            contact["_mcp_custom_fields"] = _build_contact_customer_profile(contact).get("profile", {})
            return contact
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to retrieve contact.",
                "details": str(e),
                "contact_id": contact_id,
            }

    @mcp.tool(annotations=write_tool)
    def update_contact(contact_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        """Update a contact. Writes are blocked unless DATAVERSE_ALLOW_WRITES=true."""
        if not settings.allow_writes:
            return {
                "status": "blocked",
                "message": "Writes disabled. Set DATAVERSE_ALLOW_WRITES=true to enable PATCH/POST.",
            }
        try:
            dv.update_contact(contact_id=contact_id, fields=fields)
            return {"status": "ok"}
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to update contact.",
                "details": str(e),
            }

    @mcp.tool(annotations=read_tool)
    def search_cases(query: str, top: int = 5) -> dict[str, Any]:
        """Search Cases (incidents) by title or ticket number."""
        try:
            results = dv.search_cases(query=query, top=top)
            return {"status": "ok", "count": len(results), "results": results}
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to search cases.",
                "details": str(e),
                "count": 0,
                "results": [],
            }

    @mcp.tool(annotations=read_tool)
    def get_case(case_id: str) -> dict[str, Any]:
        """Get a single Case (incident) by GUID."""
        try:
            return dv.get_case(case_id, select=None)
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to retrieve case.",
                "details": str(e),
                "case_id": case_id,
            }

    @mcp.tool(annotations=write_tool)
    def update_case(case_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        """Update a Case (incident). Writes are blocked unless DATAVERSE_ALLOW_WRITES=true."""
        if not settings.allow_writes:
            return {
                "status": "blocked",
                "message": "Writes disabled. Set DATAVERSE_ALLOW_WRITES=true to enable PATCH/POST.",
            }
        try:
            dv.update_case(case_id=case_id, fields=fields)
            return {"status": "ok"}
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to update case.",
                "details": str(e),
                "case_id": case_id,
            }

    @mcp.tool(annotations=read_tool)
    def search_work_orders(query: str, top: int = 5) -> dict[str, Any]:
        """Search Field Service Work Orders by name or work order number."""
        try:
            results = dv.search_work_orders(query=query, top=top)
            return {"status": "ok", "count": len(results), "results": results}
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to search work orders.",
                "details": str(e),
                "count": 0,
                "results": [],
            }

    @mcp.tool(annotations=read_tool)
    def get_work_order(work_order_id: str) -> dict[str, Any]:
        """Get a single Field Service Work Order by GUID."""
        try:
            return dv.get_work_order(work_order_id, select=None)
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to retrieve work order.",
                "details": str(e),
                "work_order_id": work_order_id,
            }

    @mcp.tool(annotations=write_tool)
    def update_work_order(work_order_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        """Update a Field Service Work Order. Writes are blocked unless DATAVERSE_ALLOW_WRITES=true."""
        if not settings.allow_writes:
            return {
                "status": "blocked",
                "message": "Writes disabled. Set DATAVERSE_ALLOW_WRITES=true to enable PATCH/POST.",
            }
        try:
            dv.update_work_order(work_order_id=work_order_id, fields=fields)
            return {"status": "ok"}
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to update work order.",
                "details": str(e),
                "work_order_id": work_order_id,
            }

    @mcp.tool(annotations=read_tool)
    def list_cases_for_contact(contact_id: str, top: int = 50) -> dict[str, Any]:
        """List the most recent Cases for a Contact.

        Note: defaults to 50; increase `top` to retrieve more (up to 500).
        """
        try:
            cases = dv.list_cases_for_contact(contact_id=contact_id, top=top)
            return {"status": "ok", "count": len(cases), "results": cases}
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to list cases for contact.",
                "details": str(e),
                "count": 0,
                "results": [],
            }

    @mcp.tool(annotations=read_tool)
    def list_active_cases_for_contact(contact_id: str, top: int = 200) -> dict[str, Any]:
        """List active Cases for a Contact (statecode=0).

        Increase `top` to retrieve more (up to 500).
        """
        try:
            cases = dv.list_active_cases_for_contact(contact_id=contact_id, top=top)
            return {"status": "ok", "count": len(cases), "results": cases}
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to list active cases for contact.",
                "details": str(e),
                "count": 0,
                "results": [],
            }

    @mcp.tool(annotations=read_tool)
    def get_last_case_for_contact(contact_query: str) -> dict[str, Any]:
        """Find the most recent Case raised by a Contact (by name/email/phone).

        If multiple contacts match, returns a disambiguation list.
        """
        try:
            matches = dv.search_contacts(query=contact_query, top=5)
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to search contacts while resolving last case.",
                "details": str(e),
            }
        if not matches:
            return {
                "status": "not_found",
                "message": f"No contacts matched query: {contact_query}",
            }

        if len(matches) > 1:
            return {
                "status": "disambiguate",
                "message": "Multiple contacts matched; use get_contact(contact_id) then list_cases_for_contact(contact_id).",
                "matches": matches,
            }

        contact_preview = matches[0]
        contact_id = contact_preview.get("contactid")
        if not contact_id:
            return {
                "status": "error",
                "message": "Matched contact did not include contactid.",
                "contact": contact_preview,
            }

        # Return the full contact record (includes custom fields like mj_*).
        try:
            contact = dv.get_contact(str(contact_id), select=None)
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to retrieve contact while resolving last case.",
                "details": str(e),
                "contact_id": str(contact_id),
            }

        try:
            cases = dv.list_cases_for_contact(contact_id=str(contact_id), top=1)
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to list cases for contact while resolving last case.",
                "details": str(e),
                "contact_id": str(contact_id),
            }
        if not cases:
            return {
                "status": "ok",
                "contact": contact,
                "case": None,
                "message": "No cases found for this contact.",
            }

        return {
            "status": "ok",
            "contact": contact,
            "case": cases[0],
        }

    @mcp.tool(annotations=read_tool)
    def get_boiler_repair_availability(
        when: str = "next 5 working days",
        max_slots: int = 8,
        duration_minutes: int = 120,
    ) -> dict[str, Any]:
        """Find Field Service availability for a boiler repair (demo).

        - `when`: supports `today`, `tomorrow`, `today_or_tomorrow`, `this week`, `around midday`
        - Boiler issue + priority are implied (hardcoded in the booking tool).

        Returns `options` with `slot_id` values.

        Note: customer-safe output (does not expose engineers/resources). To book, pass an `options[].slot_id`
        to `book_boiler_repair(slot_id, contact_id)`.
        """
        try:
            start_utc, end_utc = _compute_window_utc(when)
            result = fs.search_availability(
                requirement_id=None,
                window_start_utc=start_utc,
                window_end_utc=end_utc,
                duration_minutes=int(duration_minutes),
                max_slots=int(max_slots),
            )
        except Exception as e:
            return {
                "status": "error",
                "when": when,
                "count": 0,
                "options": [],
                "message": "Failed to retrieve availability. Check Dataverse credentials and Field Service configuration.",
                "details": str(e),
            }

        slots = list(result.get("slots", []))
        options: list[dict[str, Any]] = []
        for s in slots:
            slot_number = s.get("slot_number")
            slot_id = s.get("slot_id")
            start = s.get("start")
            end = s.get("end")
            if not isinstance(slot_id, str) or not isinstance(start, str) or not isinstance(end, str):
                continue
            try:
                sn = int(slot_number)
            except Exception:
                sn = len(options) + 1
            options.append(
                {
                    "slot_number": sn,
                    "slot_id": slot_id,
                    "start": start,
                    "end": end,
                    "display": f"{start} to {end}",
                }
            )

        options_table: list[list[Any]] = []
        options_text: list[str] = []
        for o in options:
            try:
                sn = int(o.get("slot_number"))
            except Exception:
                sn = len(options_table) + 1
            display = str(o.get("display") or "").strip()
            options_table.append([sn, display, o.get("start"), o.get("end"), o.get("slot_id")])
            options_text.append(f"{sn}) {display}")

        return {
            "status": result.get("status", "ok"),
            "when": when,
            "window": {"start_utc": start_utc.isoformat(), "end_utc": end_utc.isoformat()},
            "action": result.get("action"),
            "count": len(options),
            "options": options,
            "options_table": options_table,
            "options_text": options_text,
            "note": "Returned for ChatGPT via MCP. Pick an options[].slot_number, then pass the corresponding options[].slot_id to a booking tool.",
            "error": result.get("details"),
            "debug": result.get("raw"),
        }

    @mcp.tool(annotations=read_tool)
    def get_boiler_repair_availability_windows(
        when: str = "next 5 working days",
        max_windows: int = 8,
        duration_minutes: int = 120,
    ) -> dict[str, Any]:
        """Deprecated: kept for backwards compatibility.

        Returns `slots[]` containing `slot_id` values you can pass to `book_boiler_repair`.
        """
        try:
            start_utc, end_utc = _compute_window_utc(when)
            result = fs.search_availability(
                requirement_id=None,
                window_start_utc=start_utc,
                window_end_utc=end_utc,
                duration_minutes=int(duration_minutes),
                max_slots=int(max_windows),
            )
            result["when"] = when
            result["window"] = {"start_utc": start_utc.isoformat(), "end_utc": end_utc.isoformat()}
            result["note"] = "Use slots[].slot_id with book_boiler_repair(slot_id, contact_id)."
            return result
        except Exception as e:
            return {
                "status": "error",
                "when": when,
                "count": 0,
                "slots": [],
                "message": "Failed to retrieve availability slots.",
                "details": str(e),
            }

    @mcp.tool(annotations=read_tool)
    def get_availability_for_work_order(
        work_order_id: str,
        when: str = "next 5 working days",
        max_slots: int = 8,
        duration_minutes: int = 120,
    ) -> dict[str, Any]:
        """Return numbered availability options for an existing Work Order.

        Assumption: the Work Order (created upstream) auto-creates a Resource Requirement.
        This tool reuses that existing requirement, constrains it to the requested window/duration,
        and returns customer-selectable slots.
        """
        try:
            start_utc, end_utc = _compute_window_utc(when)
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to compute availability window.",
                "details": str(e),
                "when": when,
            }

        try:
            candidates = dv.wait_for_work_order_resource_requirements(
                work_order_id=work_order_id,
                timeout_seconds=25.0,
                poll_interval_seconds=1.0,
                top=10,
            )
            if not candidates:
                return {
                    "status": "error",
                    "message": "No auto-created Resource Requirement found for this Work Order.",
                    "work_order": {"id": work_order_id},
                }

            # Pick first non-demo requirement if present.
            demo_name = settings.demo_job_name
            chosen = None
            for it in candidates:
                if not isinstance(it, dict):
                    continue
                if str(it.get("msdyn_name") or "").strip() == demo_name:
                    continue
                chosen = it
                break
            if chosen is None:
                chosen = candidates[0]

            requirement_id = str((chosen or {}).get("msdyn_resourcerequirementid") or "").strip() or None
            if not requirement_id:
                return {
                    "status": "error",
                    "message": "Unable to resolve requirement id for this Work Order.",
                    "work_order": {"id": work_order_id},
                    "details": {"candidates": candidates},
                }

            from .dataverse import _iso

            dv.update_record(
                "msdyn_resourcerequirements",
                requirement_id,
                {
                    "msdyn_fromdate": _iso(start_utc),
                    "msdyn_todate": _iso(end_utc),
                    "msdyn_duration": int(duration_minutes),
                },
            )

            result = fs.search_availability(
                requirement_id=requirement_id,
                window_start_utc=start_utc,
                window_end_utc=end_utc,
                duration_minutes=int(duration_minutes),
                max_slots=int(max_slots),
            )

            slots = list(result.get("slots", []))
            options: list[dict[str, Any]] = []
            for s in slots:
                slot_number = s.get("slot_number")
                slot_id = s.get("slot_id")
                start = s.get("start")
                end = s.get("end")
                if not isinstance(slot_id, str) or not isinstance(start, str) or not isinstance(end, str):
                    continue
                try:
                    sn = int(slot_number)
                except Exception:
                    sn = len(options) + 1
                options.append(
                    {
                        "slot_number": sn,
                        "slot_id": slot_id,
                        "start": start,
                        "end": end,
                        "display": f"{start} to {end}",
                    }
                )

            options_table: list[list[Any]] = []
            options_text: list[str] = []
            for o in options:
                try:
                    sn = int(o.get("slot_number"))
                except Exception:
                    sn = len(options_table) + 1
                display = str(o.get("display") or "").strip()
                options_table.append([sn, display, o.get("start"), o.get("end"), o.get("slot_id")])
                options_text.append(f"{sn}) {display}")

            return {
                "status": result.get("status", "ok"),
                "when": when,
                "window": {"start_utc": start_utc.isoformat(), "end_utc": end_utc.isoformat()},
                "work_order": {"id": work_order_id},
                "requirement": {"id": requirement_id},
                "action": result.get("action"),
                "count": len(options),
                "options": options,
                "options_table": options_table,
                "options_text": options_text,
                "note": "Returned for ChatGPT via MCP. Pick an options[].slot_number, then book using options[].slot_id.",
                "error": result.get("details"),
                "debug": result.get("raw"),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to retrieve availability for work order.",
                "details": str(e),
                "work_order_id": work_order_id,
                "when": when,
            }

    @mcp.tool(annotations=read_tool)
    def get_boiler_repair_availability_suggestions(
        max_suggestions_per_day: int = 4,
        duration_minutes: int = 120,
    ) -> dict[str, Any]:
        """Return the earliest boiler repair slot and suggested options for today/tomorrow.

        This is optimized for the customer-style question:
        "When is the earliest time you can repair my boiler? Suggest times for today and tomorrow."

        Returns `earliest` plus grouped suggestions, each with a `slot_id`.
        """
        max_suggestions_per_day = int(max_suggestions_per_day)
        if max_suggestions_per_day <= 0:
            max_suggestions_per_day = 4
        if max_suggestions_per_day > 10:
            max_suggestions_per_day = 10

        windows = [
            ("today", "today"),
            ("tomorrow", "tomorrow"),
        ]

        grouped: dict[str, Any] = {}
        all_options: list[dict[str, Any]] = []
        actions_used: dict[str, str | None] = {}
        errors: dict[str, Any] = {}

        for label, when in windows:
            start_utc: datetime | None = None
            end_utc: datetime | None = None
            try:
                start_utc, end_utc = _compute_window_utc(when)
                result = fs.search_availability(
                    requirement_id=None,
                    window_start_utc=start_utc,
                    window_end_utc=end_utc,
                    duration_minutes=int(duration_minutes),
                    max_slots=max_suggestions_per_day,
                )
                actions_used[label] = result.get("action")
                slots = list(result.get("slots", []))
            except Exception as e:
                errors[label] = str(e)
                actions_used[label] = None
                slots = []

            options: list[dict[str, Any]] = []
            for s in slots:
                slot_number = s.get("slot_number")
                slot_id = s.get("slot_id")
                start = s.get("start")
                end = s.get("end")
                if not isinstance(slot_id, str) or not isinstance(start, str) or not isinstance(end, str):
                    continue
                try:
                    sn = int(slot_number)
                except Exception:
                    sn = len(options) + 1
                option = {
                    "slot_number": sn,
                    "slot_id": slot_id,
                    "start": start,
                    "end": end,
                    "display": f"{start} to {end}",
                }
                options.append(option)
                all_options.append(option)

            grouped[label] = {
                "when": when,
                "count": len(options),
                "options": options,
                "options_text": [f"{o.get('slot_number')}) {o.get('display')}" for o in options],
                "window": {
                    "start_utc": start_utc.isoformat() if isinstance(start_utc, datetime) else None,
                    "end_utc": end_utc.isoformat() if isinstance(end_utc, datetime) else None,
                },
            }

        # Earliest = first by ISO timestamp
        earliest: dict[str, Any] | None = None
        try:
            sorted_all = sorted(
                [o for o in all_options if isinstance(o.get("start"), str)],
                key=lambda o: o.get("start"),
            )
            earliest = sorted_all[0] if sorted_all else None
        except Exception:
            earliest = all_options[0] if all_options else None

        return {
            "status": "ok",
            "duration_minutes": int(duration_minutes),
            "earliest": earliest,
            "suggestions": grouped,
            "actions": actions_used,
            "errors": errors,
            "note": "Returned for ChatGPT via MCP. Prefer selecting by earliest.slot_number or suggestions[day].options[].slot_number.",
        }

    @mcp.tool(annotations=write_tool)
    def book_boiler_repair(
        slot_id: str,
        contact_id: str | None = None,
        priority: str = "normal",
        duration_minutes: int = 120,
    ) -> dict[str, Any]:
        """Book a boiler repair using the supported scheduling pattern.

        `slot_id` may be:
        - customer-safe window id: <startIso>|<endIso>
        - legacy slot id: <resourceId>|<startIso>|<endIso> (resource id will be ignored)

        For customer-chosen times (e.g. 14:00 local), prefer `schedule_boiler_repair(window_id, preferred_start_local, contact_id)`.
        """
        if not settings.allow_writes:
            return {
                "status": "blocked",
                "message": "Writes disabled. Set DATAVERSE_ALLOW_WRITES=true to enable creating cases, work orders and bookings.",
            }

        resolved_contact_id = (contact_id or os.getenv("DATAVERSE_DEFAULT_CONTACT_ID", "")).strip() or None
        if not resolved_contact_id:
            return {
                "status": "error",
                "message": "Missing contact_id. Provide contact_id or set DATAVERSE_DEFAULT_CONTACT_ID.",
                "hint": "Use search_contacts to find a contact, then call book_boiler_repair_for_contact(slot_id, contact_id).",
            }

        try:
            parts = (slot_id or "").split("|")
            if len(parts) == 3:
                _, start, end = parts
            elif len(parts) == 2:
                start, end = parts
            else:
                return {"status": "error", "message": "Invalid slot_id/window_id. Expected <start>|<end> (or legacy <resource>|<start>|<end>)."}

            window_id = f"{start}|{end}"
            # Default to booking at the start of the returned window.
            return fs.schedule_customer_request(
                contact_id=resolved_contact_id,
                window_id=window_id,
                preferred_start_local=start,
                duration_minutes=int(duration_minutes),
                priority=priority,
                create_case=True,
                scenario="boiler_repair",
            )
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to schedule boiler repair.",
                "details": str(e),
            }

    @mcp.tool(annotations=write_tool)
    def schedule_boiler_repair(
        window_id: str,
        preferred_start_local: str,
        contact_id: str | None = None,
        duration_minutes: int = 120,
        priority: str = "normal",
    ) -> dict[str, Any]:
        """Book using the supported Field Service self-scheduling pattern.

        This avoids directly creating `bookableresourcebookings` and instead:
        - Creates Case (Web origin) + Work Order
        - Reuses the auto-created Resource Requirement and constrains it to the selected availability window
        - Books via Schedule Assistant pipeline (`msdyn_FpsAction` + `msdyn_BookResourceSchedulingSuggestions`)

        `preferred_start_local` can be an ISO datetime or "HH:MM" (assumed today, Europe/London).
        """
        if not settings.allow_writes:
            return {
                "status": "blocked",
                "message": "Writes disabled. Set DATAVERSE_ALLOW_WRITES=true to enable scheduling.",
            }

        resolved_contact_id = (contact_id or os.getenv("DATAVERSE_DEFAULT_CONTACT_ID", "")).strip() or None
        if not resolved_contact_id:
            return {
                "status": "error",
                "message": "Missing contact_id. Provide contact_id or set DATAVERSE_DEFAULT_CONTACT_ID.",
            }

        try:
            return fs.schedule_customer_request(
                contact_id=resolved_contact_id,
                window_id=window_id,
                preferred_start_local=preferred_start_local,
                duration_minutes=int(duration_minutes),
                priority=priority,
                create_case=True,
                scenario="boiler_repair",
            )
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to schedule boiler repair.",
                "details": str(e),
            }

    @mcp.tool(annotations=write_tool)
    def book_boiler_repair_for_contact(
        slot_id: str,
        contact_id: str,
        priority: str = "normal",
        duration_minutes: int = 120,
    ) -> dict[str, Any]:
        """Book a boiler repair for a specific contact using the supported scheduling pattern."""
        if not settings.allow_writes:
            return {
                "status": "blocked",
                "message": "Writes disabled. Set DATAVERSE_ALLOW_WRITES=true to enable creating cases, work orders and bookings.",
            }

        try:
            parts = (slot_id or "").split("|")
            if len(parts) == 3:
                _, start, end = parts
            elif len(parts) == 2:
                start, end = parts
            else:
                return {"status": "error", "message": "Invalid slot_id/window_id. Expected <start>|<end> (or legacy <resource>|<start>|<end>)."}

            window_id = f"{start}|{end}"
            return fs.schedule_customer_request(
                contact_id=contact_id,
                window_id=window_id,
                preferred_start_local=start,
                duration_minutes=int(duration_minutes),
                priority=priority,
                create_case=True,
                scenario="boiler_repair",
            )
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to schedule boiler repair.",
                "details": str(e),
            }

    @mcp.tool(annotations=write_tool)
    def create_booking_for_work_order(
        slot_id: str,
        work_order_id: str,
        booking_status_name: str = "Scheduled",
        duration_minutes: int = 120,
    ) -> dict[str, Any]:
        """Create a single Bookable Resource Booking for an existing Work Order.

        Uses POST to `/api/data/v9.2/bookableresourcebookings`.
        """
        if not settings.allow_writes:
            return {
                "status": "blocked",
                "message": "Writes disabled. Set DATAVERSE_ALLOW_WRITES=true to enable creating bookings.",
            }

        try:
            parts = (slot_id or "").split("|")
            if len(parts) == 3:
                resource_id, start, end = parts
                # Some availability paths intentionally hide the resource id.
                # For direct booking creation we must resolve a concrete resource.
                chosen_slot_id = None if (resource_id or "").strip().lower() == "unknown" else f"{resource_id}|{start}|{end}"
            elif len(parts) == 2:
                # Backwards compatibility: treat as a window id and book at the start for duration_minutes.
                start, window_end = parts
                from .dataverse import _parse_iso_datetime, _iso

                schedule_start_utc = _parse_iso_datetime(start)
                schedule_end_utc = schedule_start_utc + timedelta(minutes=int(duration_minutes))
                window_end_utc = _parse_iso_datetime(window_end)
                if schedule_end_utc > window_end_utc:
                    return {
                        "status": "error",
                        "message": "Requested duration does not fit inside the selected availability window.",
                        "window": {"start": start, "end": window_end},
                        "requested": {"start": schedule_start_utc.isoformat(), "end": schedule_end_utc.isoformat()},
                    }
                chosen_slot_id = None
            else:
                return {"status": "error", "message": "Invalid slot_id/window_id. Expected <resource>|<start>|<end> (or legacy <start>|<end>)."}

            # Reuse the auto-created requirement for this work order (many orgs create it asynchronously).
            from .dataverse import _parse_iso_datetime, _iso

            window_start_utc = _parse_iso_datetime(start)
            window_end_utc = _parse_iso_datetime(end) if len(parts) == 3 else _parse_iso_datetime(parts[1])

            candidates = dv.wait_for_work_order_resource_requirements(work_order_id=work_order_id, timeout_seconds=25.0, poll_interval_seconds=1.0, top=10)
            if not candidates:
                return {
                    "status": "error",
                    "message": "No auto-created Resource Requirement found for this Work Order.",
                    "work_order": {"id": work_order_id},
                }

            demo_name = settings.demo_job_name
            chosen = None
            for it in candidates:
                if not isinstance(it, dict):
                    continue
                if str(it.get("msdyn_name") or "").strip() == demo_name:
                    continue
                chosen = it
                break
            if chosen is None:
                chosen = candidates[0] if candidates else None

            requirement_id = str((chosen or {}).get("msdyn_resourcerequirementid") or "").strip() or None
            if not requirement_id:
                return {
                    "status": "error",
                    "message": "Unable to resolve requirement id for this Work Order.",
                    "work_order": {"id": work_order_id},
                    "details": {"candidates": candidates},
                }

            dv.update_record(
                "msdyn_resourcerequirements",
                requirement_id,
                {
                    "msdyn_fromdate": _iso(window_start_utc),
                    "msdyn_todate": _iso(window_end_utc),
                    "msdyn_duration": int(duration_minutes) if len(parts) == 2 else int(((_parse_iso_datetime(end) - _parse_iso_datetime(start)).total_seconds()) // 60),
                },
            )

            if chosen_slot_id is None:
                # Find a concrete resource slot for direct creation.
                availability = dv.search_field_service_availability(
                    start_utc=window_start_utc,
                    end_utc=window_end_utc,
                    duration_minutes=int(duration_minutes),
                    requirement_id=requirement_id,
                    max_time_slots=25,
                    max_resources=3,
                )
                found = None
                for s in list(availability.get("slots", [])):
                    sid = s.get("slot_id")
                    if not isinstance(sid, str) or sid.count("|") != 2:
                        continue
                    first = sid.split("|", 1)[0].strip().lower()
                    if first and first != "unknown":
                        found = sid
                        break
                if not found:
                    return {
                        "status": "error",
                        "message": "Unable to resolve a concrete resource slot_id for direct booking creation. This usually means availability is being returned without resources (permissions/config), or no resources are eligible in this window.",
                        "work_order": {"id": work_order_id},
                        "requirement": {"id": requirement_id},
                        "details": availability.get("details"),
                    }
                chosen_slot_id = found

            booking_result = dv.create_booking_for_requirement(
                slot_id=chosen_slot_id,
                requirement_id=requirement_id,
                work_order_id=work_order_id,
                booking_status_name=booking_status_name,
                name="Work order booking (MCP)",
            )

            return {
                "status": booking_result.get("status", "ok"),
                "work_order": {"id": work_order_id},
                "requirement": {"id": requirement_id},
                "booking": booking_result.get("booking"),
                "selected_slot": booking_result.get("selected_slot"),
                "window": {"start": _iso(window_start_utc), "end": _iso(window_end_utc)},
                "note": "Created bookableresourcebooking via POST.",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to create booking for existing work order.",
                "details": str(e),
                "work_order_id": work_order_id,
                "slot_id": slot_id,
            }

    @mcp.tool(annotations=write_tool)
    def create_booking_for_work_order_slot_number(
        work_order_id: str,
        slot_number: int,
        when: str = "today",
        duration_minutes: int = 120,
        booking_status_name: str = "Scheduled",
    ) -> dict[str, Any]:
        """Create a single booking for a Work Order by choosing a numbered slot.

        Intended for ChatGPT UX: show numbered options, user replies with a number.
        """
        if not settings.allow_writes:
            return {
                "status": "blocked",
                "message": "Writes disabled. Set DATAVERSE_ALLOW_WRITES=true to enable creating bookings.",
            }

        try:
            avail = get_availability_for_work_order(
                work_order_id=work_order_id,
                when=when,
                max_slots=25,
                duration_minutes=int(duration_minutes),
            )
            if avail.get("status") != "ok":
                return {
                    "status": "error",
                    "message": "Unable to retrieve availability for work order.",
                    "details": avail,
                }

            options = list(avail.get("options", []) or [])
            chosen = None
            for o in options:
                try:
                    if int(o.get("slot_number")) == int(slot_number):
                        chosen = o
                        break
                except Exception:
                    continue

            if not chosen or not isinstance(chosen.get("slot_id"), str):
                return {
                    "status": "error",
                    "message": "Invalid slot_number for the returned availability options.",
                    "requested": {"slot_number": int(slot_number)},
                    "available_slot_numbers": [o.get("slot_number") for o in options if isinstance(o, dict)],
                }

            return create_booking_for_work_order(
                slot_id=str(chosen["slot_id"]),
                work_order_id=work_order_id,
                booking_status_name=booking_status_name,
                duration_minutes=int(duration_minutes),
            )
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to create booking for work order slot number.",
                "details": str(e),
                "work_order_id": work_order_id,
                "slot_number": slot_number,
            }

    @mcp.tool(annotations=write_tool)
    def book_existing_requirement_for_slot(
        requirement_id: str,
        slot_id: str,
    ) -> dict[str, Any]:
        """Book an existing Resource Requirement for a specific slot.

        Use this when Case/Work Order/Requirement were created successfully but booking failed.

        `slot_id` format: <startIso>|<endIso>
        """
        if not settings.allow_writes:
            return {
                "status": "blocked",
                "message": "Writes disabled. Set DATAVERSE_ALLOW_WRITES=true to enable scheduling.",
            }

        try:
            parts = (slot_id or "").split("|")
            if len(parts) == 3:
                resource_id, start, end = parts
                chosen_slot_id = f"{resource_id}|{start}|{end}"
            elif len(parts) == 2:
                start, end = parts
                chosen_slot_id = None
            else:
                return {"status": "error", "message": "Invalid slot_id. Expected <resource>|<start>|<end> (or legacy <start>|<end>)."}

            from .dataverse import _parse_iso_datetime

            start_utc = _parse_iso_datetime(start)
            end_utc = _parse_iso_datetime(end)
            if end_utc <= start_utc:
                return {"status": "error", "message": "Invalid slot_id: end must be after start."}

            if chosen_slot_id is None:
                # Try to resolve a concrete resource slot for the requirement.
                availability = dv.search_field_service_availability(
                    start_utc=start_utc,
                    end_utc=end_utc,
                    duration_minutes=int((end_utc - start_utc).total_seconds() // 60),
                    requirement_id=requirement_id,
                    max_time_slots=25,
                    max_resources=3,
                )
                found = None
                for s in list(availability.get("slots", [])):
                    sid = s.get("slot_id")
                    if isinstance(sid, str) and sid.count("|") == 2:
                        found = sid
                        break
                if not found:
                    return {
                        "status": "error",
                        "message": "Unable to resolve a concrete resource slot_id for direct booking creation.",
                        "requirement": {"id": requirement_id},
                        "details": availability.get("details"),
                    }
                chosen_slot_id = found

            booking_result = dv.create_booking_for_requirement(
                slot_id=chosen_slot_id,
                requirement_id=requirement_id,
                booking_status_name="Scheduled",
                name="Requirement booking (MCP)",
            )

            return {
                "status": booking_result.get("status", "ok"),
                "requirement": {"id": requirement_id},
                "booking": booking_result.get("booking"),
                "selected_slot": booking_result.get("selected_slot"),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to book existing requirement for slot.",
                "details": str(e),
                "requirement_id": requirement_id,
                "slot_id": slot_id,
            }

    return mcp


def build_asgi_app() -> Any:
    mcp = build_mcp()
    # IMPORTANT: Do not change mount_path here.
    # ChatGPT's MCP client uses the SSE handshake's announced POST endpoint.
    # If mount_path is changed without also remapping message routes, the client
    # will POST to /sse/messages while the server is mounted at /messages.
    app = mcp.sse_app()

    # Log tool-call messages and any unhandled exceptions with tracebacks.
    app.add_middleware(_McpMessageLoggingMiddleware)

    @app.route("/", methods=["GET", "POST"])
    async def _root(_: Request) -> Response:
        return RedirectResponse(url="/sse", status_code=307)

    token = os.getenv("MCP_AUTH_TOKEN", "").strip()
    if token:
        app.add_middleware(_BearerTokenMiddleware, token=token)

    return app


def main() -> None:
    # Best-effort runtime logging to a file so failures aren't lost when VS Code tasks
    # recycle terminals. Safe to call multiple times.
    try:
        import logging
        from pathlib import Path

        base = Path(__file__).resolve().parent.parent.parent  # mcp-dataverse-server
        log_dir = base / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "runtime.log"

        root = logging.getLogger()
        root.setLevel(logging.INFO)

        if not any(getattr(h, "baseFilename", None) == str(log_path) for h in root.handlers):
            fh = logging.FileHandler(log_path, encoding="utf-8")
            fh.setLevel(logging.INFO)
            fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
            root.addHandler(fh)

        # Reduce extremely noisy request-level logging unless explicitly enabled.
        logging.getLogger("httpx").setLevel(logging.WARNING)
    except Exception:
        pass

    app = build_asgi_app()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

