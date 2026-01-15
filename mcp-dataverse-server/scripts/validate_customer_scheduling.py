from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings
from mcp_dataverse_server.dataverse import DataverseClient
from mcp_dataverse_server.scheduling_service_customer import CustomerSelfServiceSchedulingService
from mcp_dataverse_server.server import _compute_window_utc


def _odata_guid(value: str) -> str:
    v = (value or "").strip()
    # Dataverse Web API typically expects bare GUID values for *_value comparisons.
    return v


def _synthetic_slot_test(svc: CustomerSelfServiceSchedulingService, *, duration_minutes: int) -> None:
    """Run deterministic post-processing checks without needing live FS availability."""

    now_utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start_utc = now_utc
    end_utc = now_utc + timedelta(days=1)

    raw = {
        "status": "ok",
        "slots": [
            # Too early and misaligned minutes -> should be pushed to >= now+30 and to :00/:30
            {"start": (now_utc - timedelta(minutes=10)).isoformat().replace("+00:00", "Z"), "end": (now_utc + timedelta(hours=3)).isoformat().replace("+00:00", "Z")},
            {"start": (now_utc + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"), "end": (now_utc + timedelta(hours=2)).isoformat().replace("+00:00", "Z")},
            # Duplicate windows (format variations) -> should dedupe
            {"start": (now_utc + timedelta(hours=4)).isoformat(), "end": (now_utc + timedelta(hours=6)).isoformat()},
            {"start": (now_utc + timedelta(hours=4)).isoformat().replace("+00:00", "Z"), "end": (now_utc + timedelta(hours=6)).isoformat().replace("+00:00", "Z")},
            # Same start, different ends -> should keep smallest end that still fits duration
            {"start": (now_utc + timedelta(hours=8)).isoformat().replace("+00:00", "Z"), "end": (now_utc + timedelta(hours=10)).isoformat().replace("+00:00", "Z")},
            {"start": (now_utc + timedelta(hours=8)).isoformat().replace("+00:00", "Z"), "end": (now_utc + timedelta(hours=12)).isoformat().replace("+00:00", "Z")},
        ],
    }

    dv = svc._dv  # intentionally internal for this diagnostic script
    original = dv.search_field_service_availability
    try:
        dv.search_field_service_availability = lambda **_: raw  # type: ignore[assignment]
        res = svc.search_availability(
            requirement_id=None,
            window_start_utc=start_utc,
            window_end_utc=end_utc,
            duration_minutes=duration_minutes,
            max_slots=12,
        )
    finally:
        dv.search_field_service_availability = original  # type: ignore[assignment]

    slots = list(res.get("slots", []) or [])
    print("synthetic_slot_count:", len(slots))
    print("synthetic_first_slots:")
    for w in slots[:8]:
        print(" ", w)

    violations: list[tuple[str, str]] = []
    for w in slots:
        st = w.get("start")
        if not isinstance(st, str):
            continue
        try:
            minute = int(st[14:16])
            if minute not in (0, 30):
                violations.append(("minute_not_00_or_30", st))
        except Exception:
            violations.append(("unparseable_start", st))
    print("synthetic_violations_sample:", violations[:10])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", action="store_true", help="Run synthetic slot post-processing test")
    parser.add_argument(
        "--write-create-requirement",
        action="store_true",
        help="Attempt to create a Resource Requirement (writes to Dataverse).",
    )
    parser.add_argument("--work-order-id", type=str, default="", help="Existing Work Order GUID (required for write test)")
    args = parser.parse_args()

    settings = load_settings()

    start_utc, end_utc = _compute_window_utc("next 5 working days")
    print("base_url:", settings.dataverse_base_url)
    print("window_utc:", start_utc.isoformat(), "->", end_utc.isoformat())

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
    svc = CustomerSelfServiceSchedulingService(dv)

    caps = svc.probe_capabilities()
    print("caps:", caps)

    nav = dv.try_get_many_to_one_nav_property(
        referencing_entity_logical_name="msdyn_resourcerequirement",
        referenced_entity_logical_name="msdyn_workorder",
    )
    print("nav_property(msdyn_resourcerequirement->msdyn_workorder):", nav)

    # Helpful for the optional write test: locate a recent Work Order id.
    try:
        recent = dv._get(  # intentionally internal for this diagnostic script
            "msdyn_workorders?$select=msdyn_workorderid&$orderby=createdon desc&$top=1",
            include_annotations=False,
        )
        items = list(recent.get("value", []) or []) if isinstance(recent, dict) else []
        wo_id = items[0].get("msdyn_workorderid") if items and isinstance(items[0], dict) else None
        print("recent_work_order_id:", wo_id)
    except Exception as e:
        print("recent_work_order_id: <unavailable>", str(e))

    # Read-only availability sample
    duration_minutes = 120
    res = svc.search_availability(
        requirement_id=None,
        window_start_utc=start_utc,
        window_end_utc=end_utc,
        duration_minutes=duration_minutes,
        max_slots=12,
    )
    slots = list(res.get("slots", []) or [])
    print("slot_count:", len(slots))

    violations: list[tuple[str, str]] = []
    for w in slots:
        st = w.get("start")
        if not isinstance(st, str):
            continue

        # Minute alignment check based on ISO string
        try:
            minute = int(st[14:16])
            if minute not in (0, 30):
                violations.append(("minute_not_00_or_30", st))
        except Exception:
            violations.append(("unparseable_start", st))

    print("violations_sample:", violations[:10])
    print("first_slots:")
    for w in slots[:8]:
        print(" ", w)

    # Surface Dataverse-side action errors (non-fatal; helpful diagnostics)
    print("action_errors:", res.get("action_errors"))

    if args.synthetic or len(slots) == 0:
        _synthetic_slot_test(svc, duration_minutes=duration_minutes)

    if args.write_create_requirement:
        work_order_id = (args.work_order_id or "").strip()
        if not work_order_id:
            raise SystemExit("--work-order-id is required for --write-create-requirement")
        print("\nWRITE TEST: creating requirement for work_order_id", work_order_id)
        req_id = svc.create_requirement(
            work_order_id=work_order_id,
            window_start_utc=start_utc,
            window_end_utc=end_utc,
            duration_minutes=duration_minutes,
        )
        print("created_requirement_id:", req_id)

        try:
            boiler_name = "Boiler Heating Household Specialist"
            cid = dv.try_get_characteristic_id_by_name(boiler_name)
            print("characteristic_id(boiler):", cid)
            if cid:
                rel = dv._get(
                    "msdyn_requirementcharacteristics?$select=msdyn_requirementcharacteristicid&$filter="
                    + "_msdyn_resourcerequirementid_value eq "
                    + _odata_guid(req_id)
                    + " and _msdyn_characteristicid_value eq "
                    + _odata_guid(cid)
                    + "&$top=1",
                    include_annotations=False,
                )
                items = list(rel.get("value", [])) if isinstance(rel, dict) else []
                print("requirement_has_boiler_characteristic:", bool(items))
        except Exception as e:
            print("requirement_characteristic_check_failed:", str(e))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
