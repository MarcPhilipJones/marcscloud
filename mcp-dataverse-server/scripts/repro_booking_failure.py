from __future__ import annotations

from datetime import datetime, timezone

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings
from mcp_dataverse_server.dataverse import DataverseClient


def main() -> None:
    s = load_settings()
    tp = TokenProvider(
        tenant_id=s.dataverse_tenant_id,
        client_id=s.dataverse_client_id,
        client_secret=s.dataverse_client_secret,
        resource=s.dataverse_base_url,
    )
    dv = DataverseClient(base_url=s.dataverse_base_url, api_version=s.dataverse_api_version, token_provider=tp)

    # Note: this GUID may not exist in every org. We keep it here for reference
    # but omit work_order_id from booking creation so we can validate payload schema.
    work_order_id = "e2441ab4-f9f1-f011-8406-6045bddd0ab1"
    requirement_id = "e9441ab4-f9f1-f011-8406-6045bddd0ab1"

    start_utc = datetime(2026, 1, 15, 11, 0, 0, tzinfo=timezone.utc)
    end_utc = datetime(2026, 1, 15, 13, 0, 0, tzinfo=timezone.utc)

    # Align with the MCP booking flow: explicitly populate fields that many orgs
    # require for requirement-based availability to return concrete slots.
    dv.update_record(
        "msdyn_resourcerequirements",
        requirement_id,
        {
            "msdyn_fromdate": start_utc.isoformat().replace("+00:00", "Z"),
            "msdyn_todate": end_utc.isoformat().replace("+00:00", "Z"),
            "msdyn_duration": 120,
            "msdyn_timewindowstart": start_utc.isoformat().replace("+00:00", "Z"),
            "msdyn_timewindowend": end_utc.isoformat().replace("+00:00", "Z"),
            "msdyn_timezonefortimewindow": 85,
            "msdyn_worklocation": 690970000,
            "msdyn_latitude": 52.41882,
            "msdyn_longitude": -1.78605,
        },
    )

    a = dv.search_field_service_availability(
        start_utc=start_utc,
        end_utc=end_utc,
        duration_minutes=120,
        requirement_id=requirement_id,
        max_time_slots=25,
        max_resources=5,
    )

    slots = list(a.get("slots", []) or [])
    print("availability_status=", a.get("status"), "action=", a.get("action"), "slot_count=", len(slots))

    try:
        g = dv.search_field_service_availability(
            start_utc=start_utc,
            end_utc=end_utc,
            duration_minutes=120,
            requirement_id=None,
            max_time_slots=5,
            max_resources=3,
        )
        print(
            "generic_preview_status=",
            g.get("status"),
            "action=",
            g.get("action"),
            "slot_count=",
            len(list(g.get("slots", []) or [])),
        )
    except Exception as e:
        print("generic_preview_error=", str(e))

    slot_id = None
    for s in slots:
        sid = s.get("slot_id")
        if isinstance(sid, str) and sid.count("|") == 2 and not sid.lower().startswith("unknown|"):
            slot_id = sid
            break

    print("chosen_slot_id=", slot_id)

    if not slot_id:
        print("NO_CONCRETE_SLOT")
        print("message=", a.get("message"))
        print("details=", a.get("details"))
        # Try generic slots so we can still validate booking POST payload works.
        g_slots = list((g.get("slots", []) if isinstance(g, dict) else []) or [])
        for s in g_slots:
            sid = s.get("slot_id")
            if isinstance(sid, str) and sid.count("|") == 2 and not sid.lower().startswith("unknown|"):
                slot_id = sid
                break
        print("fallback_slot_id=", slot_id)
        if not slot_id:
            return

    try:
        r = dv.create_booking_for_requirement(
            slot_id=slot_id,
            requirement_id=requirement_id,
            work_order_id=None,
            booking_status_name="Scheduled",
            name="Customer booking (manual repro)",
        )
        print("booking_create_status=", r.get("status"))
        b = r.get("booking") or {}
        print("booking_id=", b.get("bookableresourcebookingid") or b.get("id"))
        print("selected_slot=", r.get("selected_slot"))
    except Exception as e:
        print("BOOKING_CREATE_ERROR=", str(e))


if __name__ == "__main__":
    main()
