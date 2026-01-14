from __future__ import annotations

from typing import Any, Callable
import os

import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from .auth import TokenProvider
from .config import load_settings
from .dataverse import DataverseClient


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
        results = dv.search_contacts(query=query, top=top)
        return {"count": len(results), "results": results}

    @mcp.tool(annotations=read_tool)
    def get_contact(contact_id: str) -> dict[str, Any]:
        """Get a single contact by GUID."""
        contact = dv.get_contact(contact_id, select=None)
        # Put the custom-field summary directly into the contact payload so the
        # model can answer questions like "Does Chris have an EV?" without
        # needing a separate tool call.
        contact["_mcp_custom_fields"] = _build_contact_customer_profile(contact).get("profile", {})
        return contact

    @mcp.tool(annotations=write_tool)
    def update_contact(contact_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        """Update a contact. Writes are blocked unless DATAVERSE_ALLOW_WRITES=true."""
        if not settings.allow_writes:
            return {
                "status": "blocked",
                "message": "Writes disabled. Set DATAVERSE_ALLOW_WRITES=true to enable PATCH/POST.",
            }
        dv.update_contact(contact_id=contact_id, fields=fields)
        return {"status": "ok"}

    @mcp.tool(annotations=read_tool)
    def search_cases(query: str, top: int = 5) -> dict[str, Any]:
        """Search Cases (incidents) by title or ticket number."""
        results = dv.search_cases(query=query, top=top)
        return {"count": len(results), "results": results}

    @mcp.tool(annotations=read_tool)
    def get_case(case_id: str) -> dict[str, Any]:
        """Get a single Case (incident) by GUID."""
        return dv.get_case(case_id, select=None)

    @mcp.tool(annotations=read_tool)
    def list_cases_for_contact(contact_id: str, top: int = 50) -> dict[str, Any]:
        """List the most recent Cases for a Contact.

        Note: defaults to 50; increase `top` to retrieve more (up to 500).
        """
        cases = dv.list_cases_for_contact(contact_id=contact_id, top=top)
        return {"count": len(cases), "results": cases}

    @mcp.tool(annotations=read_tool)
    def list_active_cases_for_contact(contact_id: str, top: int = 200) -> dict[str, Any]:
        """List active Cases for a Contact (statecode=0).

        Increase `top` to retrieve more (up to 500).
        """
        cases = dv.list_active_cases_for_contact(contact_id=contact_id, top=top)
        return {"count": len(cases), "results": cases}

    @mcp.tool(annotations=read_tool)
    def get_last_case_for_contact(contact_query: str) -> dict[str, Any]:
        """Find the most recent Case raised by a Contact (by name/email/phone).

        If multiple contacts match, returns a disambiguation list.
        """
        matches = dv.search_contacts(query=contact_query, top=5)
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
        contact = dv.get_contact(str(contact_id), select=None)

        cases = dv.list_cases_for_contact(contact_id=str(contact_id), top=1)
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

    return mcp


def build_asgi_app() -> Any:
    mcp = build_mcp()
    # IMPORTANT: Do not change mount_path here.
    # ChatGPT's MCP client uses the SSE handshake's announced POST endpoint.
    # If mount_path is changed without also remapping message routes, the client
    # will POST to /sse/messages while the server is mounted at /messages.
    app = mcp.sse_app()

    @app.route("/", methods=["GET", "POST"])
    async def _root(_: Request) -> Response:
        return RedirectResponse(url="/sse", status_code=307)

    token = os.getenv("MCP_AUTH_TOKEN", "").strip()
    if token:
        app.add_middleware(_BearerTokenMiddleware, token=token)

    return app


def main() -> None:
    app = build_asgi_app()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

