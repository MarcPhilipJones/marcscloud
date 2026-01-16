from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone


def _env(name: str, default: str) -> str:
    v = os.getenv(name)
    return v.strip() if isinstance(v, str) and v.strip() else default


def main() -> int:
    # Ensure local src is importable when running from repo.
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_dir = os.path.join(repo_root, "src")
    sys.path.insert(0, src_dir)

    from mcp_dataverse_server.auth import TokenProvider
    from mcp_dataverse_server.config import load_settings
    from mcp_dataverse_server.dataverse import DataverseClient

    settings = load_settings()

    requirement_id = _env("MCP_TEST_REQUIREMENT_ID", "96e20b8b-34f2-f011-8406-6045bddd0ab1")
    work_order_id = _env("MCP_TEST_WORK_ORDER_ID", "8fe20b8b-34f2-f011-8406-6045bddd0ab1")
    case_id = _env("MCP_TEST_CASE_ID", "78e20b8b-34f2-f011-8406-6045bddd0ab1")

    # Alan Steiner (Bookable Resource)
    resource_id = _env("MCP_TEST_BOOKABLE_RESOURCE_ID", "b8dddd9c-3b61-ef11-bfe2-002248a36d0e")

    # UK time in winter == UTC
    start_iso = _env("MCP_TEST_START_ISO", "2026-01-19T09:00:00Z")
    end_iso = _env("MCP_TEST_END_ISO", "2026-01-19T11:00:00Z")
    slot_id = f"{resource_id}|{start_iso}|{end_iso}"

    print("Dataverse:", settings.dataverse_base_url)
    print("API version:", settings.dataverse_api_version)
    print("Existing records:")
    print("- requirement:", requirement_id)
    print("- work_order:", work_order_id)
    print("- case:", case_id)
    print("Slot:")
    print("- slot_id:", slot_id)

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

    print("\nMetadata probes (best-effort):")
    for refed in ["bookingstatus", "bookableresource", "msdyn_resourcerequirement", "msdyn_workorder"]:
        nav = dv.try_get_many_to_one_nav_property(
            referencing_entity_logical_name="bookableresourcebooking",
            referenced_entity_logical_name=refed,
        )
        attr = dv.try_get_many_to_one_referencing_attribute(
            referencing_entity_logical_name="bookableresourcebooking",
            referenced_entity_logical_name=refed,
        )
        print(f"- {refed}: nav={nav!r} attr={attr!r}")

    print("\nRelationship metadata dump (bookableresourcebooking ManyToOneRelationships):")
    try:
        rels = dv._get(
            "EntityDefinitions(LogicalName='bookableresourcebooking')/ManyToOneRelationships"
            "?$select=ReferencingAttribute,ReferencedEntity,ReferencingEntityNavigationPropertyName"
            "&$filter=(ReferencingAttribute eq 'resource' or ReferencingAttribute eq 'bookingstatus' "
            "or ReferencingAttribute eq 'msdyn_workorder' or ReferencingAttribute eq 'msdyn_resourcerequirement')",
            include_annotations=False,
        )
        items = list(rels.get("value", [])) if isinstance(rels, dict) else []
        for it in items:
            if not isinstance(it, dict):
                continue
            print(
                "-",
                {
                    "ReferencingAttribute": it.get("ReferencingAttribute"),
                    "ReferencedEntity": it.get("ReferencedEntity"),
                    "Nav": it.get("ReferencingEntityNavigationPropertyName"),
                },
            )
        if not items:
            print("- (no relationship rows returned; may be permission-filtered)")
    except Exception as e:
        print("- relationship query failed:", str(e)[:400])

    print("\nAttempt 1: direct bookableresourcebookings POST (create_booking_for_requirement)")
    try:
        direct = dv.create_booking_for_requirement(
            slot_id=slot_id,
            requirement_id=requirement_id,
            work_order_id=work_order_id,
            booking_status_name="Scheduled",
            name=f"MCP test booking (existing req {requirement_id[:8]})",
        )
        print(json.dumps(direct, indent=2))
        return 0
    except Exception as e:
        print("DIRECT FAILED:")
        print(str(e)[:2000])

    print("\nAttempt 2: Schedule Assistant pipeline (msdyn_FpsAction/153 + msdyn_BookResourceSchedulingSuggestions)")
    try:
        start_dt = datetime(2026, 1, 19, 9, 0, tzinfo=timezone.utc)
        end_dt = datetime(2026, 1, 19, 11, 0, tzinfo=timezone.utc)
        sa = dv.book_requirement_via_schedule_assistant(
            requirement_id=requirement_id,
            schedule_start_utc=start_dt,
            schedule_end_utc=end_dt,
            apply_option=1,
        )
        print(json.dumps(sa, indent=2))
        return 0 if sa.get("status") == "ok" else 2
    except Exception as e:
        print("SCHEDULE ASSISTANT FAILED:")
        print(str(e)[:2000])
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
