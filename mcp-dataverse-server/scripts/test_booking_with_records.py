from __future__ import annotations

import argparse
from datetime import datetime, timezone

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings
from mcp_dataverse_server.dataverse import DataverseClient


def _parse_utc(value: str) -> datetime:
    v = (value or "").strip()
    if not v:
        raise ValueError("Empty datetime")
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a bookableresourcebooking for an existing requirement/work order")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--work-order-id", required=True)
    parser.add_argument("--requirement-id", required=True)
    parser.add_argument("--start", default="2026-01-16T09:00:00Z", help="UTC start ISO, default: 2026-01-16T09:00:00Z")
    parser.add_argument("--end", default="2026-01-16T11:00:00Z", help="UTC end ISO, default: 2026-01-16T11:00:00Z")
    parser.add_argument("--slot-index", type=int, default=3, help="1-based slot index to pick (default 3)")
    args = parser.parse_args()

    start_utc = _parse_utc(args.start)
    end_utc = _parse_utc(args.end)

    s = load_settings()
    tp = TokenProvider(
        tenant_id=s.dataverse_tenant_id,
        client_id=s.dataverse_client_id,
        client_secret=s.dataverse_client_secret,
        resource=s.dataverse_base_url,
    )
    dv = DataverseClient(base_url=s.dataverse_base_url, api_version=s.dataverse_api_version, token_provider=tp)

    # Make the requirement window explicit so requirement-based availability has what it needs.
    dv.update_record(
        "msdyn_resourcerequirements",
        args.requirement_id,
        {
            "msdyn_fromdate": start_utc.isoformat().replace("+00:00", "Z"),
            "msdyn_todate": end_utc.isoformat().replace("+00:00", "Z"),
            "msdyn_duration": int((end_utc - start_utc).total_seconds() // 60),
            "msdyn_timewindowstart": start_utc.isoformat().replace("+00:00", "Z"),
            "msdyn_timewindowend": end_utc.isoformat().replace("+00:00", "Z"),
            "msdyn_timezonefortimewindow": 85,
        },
    )

    availability = dv.search_field_service_availability(
        start_utc=start_utc,
        end_utc=end_utc,
        duration_minutes=int((end_utc - start_utc).total_seconds() // 60),
        requirement_id=args.requirement_id,
        max_time_slots=25,
        max_resources=10,
    )

    slots = list(availability.get("slots", []) or [])
    print("availability_status=", availability.get("status"), "action=", availability.get("action"), "slot_count=", len(slots))

    def _concrete_slots(items: list[dict]) -> list[str]:
        out: list[str] = []
        for it in items:
            sid = it.get("slot_id")
            if isinstance(sid, str) and sid.count("|") == 2 and not sid.lower().startswith("unknown|"):
                out.append(sid)
        return out

    concrete = _concrete_slots(slots)

    # If requirement-based availability returns no concrete resource, fall back to the UFX pipeline preview.
    if not concrete:
        generic = dv.search_field_service_availability(
            start_utc=start_utc,
            end_utc=end_utc,
            duration_minutes=int((end_utc - start_utc).total_seconds() // 60),
            requirement_id=None,
            max_time_slots=10,
            max_resources=10,
        )
        gslots = list(generic.get("slots", []) or [])
        print(
            "generic_status=",
            generic.get("status"),
            "action=",
            generic.get("action"),
            "slot_count=",
            len(gslots),
        )
        concrete = _concrete_slots(gslots)

    if not concrete:
        raise SystemExit("No concrete slots available to book.")

    # Slot index is 1-based as users describe "Slot 3".
    idx = max(1, int(args.slot_index)) - 1
    if idx >= len(concrete):
        idx = 0

    slot_id = concrete[idx]
    print("chosen_slot_id=", slot_id)

    result = dv.create_booking_for_requirement(
        slot_id=slot_id,
        requirement_id=args.requirement_id,
        work_order_id=args.work_order_id,
        booking_status_name="Scheduled",
        name="Customer booking (client record repro)",
    )

    booking = result.get("booking") or {}
    booking_id = booking.get("id") or booking.get("bookableresourcebookingid")
    print("booking_create_status=", result.get("status"))
    print("booking_id=", booking_id)
    print("selected_slot=", result.get("selected_slot"))


if __name__ == "__main__":
    main()
