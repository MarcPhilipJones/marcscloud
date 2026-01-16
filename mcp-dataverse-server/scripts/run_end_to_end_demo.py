from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone


def _parse_iso_utc(value: str) -> datetime:
    v = (value or "").strip()
    if not v:
        raise ValueError("Empty datetime")
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def main() -> int:
    # Ensure local src is importable when running from repo.
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_dir = os.path.join(repo_root, "src")
    sys.path.insert(0, src_dir)

    from mcp_dataverse_server.auth import TokenProvider
    from mcp_dataverse_server.config import load_settings
    from mcp_dataverse_server.dataverse import DataverseClient
    from mcp_dataverse_server.scheduling_service_customer import CustomerSelfServiceSchedulingService
    from mcp_dataverse_server.server import _compute_window_utc

    settings = load_settings()
    if not settings.allow_writes:
        raise SystemExit("Writes are disabled. Set DATAVERSE_ALLOW_WRITES=true.")

    contact_id = (os.getenv("DATAVERSE_DEFAULT_CONTACT_ID") or "").strip()
    if not contact_id:
        raise SystemExit("Missing DATAVERSE_DEFAULT_CONTACT_ID.")

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

    svc = CustomerSelfServiceSchedulingService(
        dv,
        demo_bookable_resource_id=settings.demo_bookable_resource_id,
        demo_resource_name=settings.demo_resource_name,
        demo_job_name=settings.demo_job_name,
        demo_fast=settings.demo_fast,
        clear_demo_caches_on_start=settings.clear_demo_caches_on_start,
    )

    window_start_utc, window_end_utc = _compute_window_utc("next 5 working days")
    window_id = f"{window_start_utc.isoformat().replace('+00:00','Z')}|{window_end_utc.isoformat().replace('+00:00','Z')}"

    availability = svc.search_availability(
        requirement_id=None,
        window_start_utc=window_start_utc,
        window_end_utc=window_end_utc,
        duration_minutes=120,
        max_slots=8,
    )
    slots = list(availability.get("slots", []) or [])
    if not slots:
        print(json.dumps(availability, indent=2)[:8000])
        raise SystemExit("No slots returned; cannot run end-to-end demo.")

    slot0 = slots[0]
    start = str(slot0.get("start") or "").strip()
    end = str(slot0.get("end") or "").strip()
    if not start or not end:
        raise SystemExit("First slot did not contain start/end")

    # Use the chosen slot start as the preferred appointment time.
    # Provide as ISO (UTC) so no local parsing ambiguity.
    preferred_start_local = start

    print("base_url:", settings.dataverse_base_url)
    print("demo_resource_id:", settings.demo_bookable_resource_id)
    print("window_id:", window_id)
    print("chosen_slot:", {"start": start, "end": end, "slot_id": slot0.get("slot_id")})

    out = svc.schedule_customer_request(
        contact_id=contact_id,
        window_id=window_id,
        preferred_start_local=preferred_start_local,
        duration_minutes=120,
        priority="normal",
        create_case=True,
        scenario="boiler_repair",
    )

    print("\nSCHEDULE_RESULT:")
    print(json.dumps(out, indent=2)[:12000])

    if out.get("status") != "ok":
        return 2

    case_id = (out.get("case") or {}).get("id")
    work_order_id = (out.get("work_order") or {}).get("id")
    requirement_id = (out.get("requirement") or {}).get("id")
    booking = out.get("booking") if isinstance(out.get("booking"), dict) else {}
    booking_id = (booking or {}).get("id")

    print("\nCREATED_IDS:")
    print(json.dumps({"case": case_id, "work_order": work_order_id, "requirement": requirement_id, "booking": booking_id}, indent=2))

    # Verify records exist in Dataverse
    print("\nVERIFY_EXISTS:")
    checks = {
        "case": f"incidents({case_id})?$select=incidentid,title,createdon",
        "work_order": f"msdyn_workorders({work_order_id})?$select=msdyn_workorderid,msdyn_name,createdon",
        "requirement": f"msdyn_resourcerequirements({requirement_id})?$select=msdyn_resourcerequirementid,msdyn_name,createdon",
        "booking": f"bookableresourcebookings({booking_id})?$select=bookableresourcebookingid,name,starttime,endtime,createdon",
    }

    verified: dict[str, object] = {}
    for k, path in checks.items():
        try:
            verified[k] = dv._get(path, include_annotations=False)  # intentionally internal for this diagnostic
            # Basic sanity check: ensure the id appears.
            if k == "booking":
                _ = verified[k].get("bookableresourcebookingid")  # type: ignore[union-attr]
        except Exception as e:
            verified[k] = {"status": "error", "message": str(e)[:2000], "path": path}

    print(json.dumps(verified, indent=2)[:12000])

    # Optional: show the exact appointment range we booked.
    try:
        st = _parse_iso_utc(start)
        en = _parse_iso_utc(end)
        print("\nBOOKED_WINDOW_UTC:", st.isoformat(), "->", en.isoformat())
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
