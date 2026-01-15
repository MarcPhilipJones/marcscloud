from __future__ import annotations

import argparse

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings
from mcp_dataverse_server.dataverse import DataverseClient


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("booking_id")
    args = parser.parse_args()

    s = load_settings()
    tp = TokenProvider(
        tenant_id=s.dataverse_tenant_id,
        client_id=s.dataverse_client_id,
        client_secret=s.dataverse_client_secret,
        resource=s.dataverse_base_url,
    )
    dv = DataverseClient(base_url=s.dataverse_base_url, api_version=s.dataverse_api_version, token_provider=tp)

    bid = (args.booking_id or "").strip()
    if not bid:
        raise SystemExit("Missing booking_id")

    # Prefer navigation-property expansions (org/schema-safe) over guessing _<lookup>_value fields.
    base_select = "bookableresourcebookingid,starttime,endtime,name"
    expand_parts: list[str] = [
        "Resource($select=bookableresourceid,name)",
        "BookingStatus($select=bookingstatusid,name)",
        "msdyn_ResourceRequirement($select=msdyn_resourcerequirementid,msdyn_name)",
    ]

    wo_nav = dv.try_get_many_to_one_nav_property(
        referencing_entity_logical_name="bookableresourcebooking",
        referenced_entity_logical_name="msdyn_workorder",
    )
    if wo_nav:
        expand_parts.append(f"{wo_nav}($select=msdyn_workorderid,msdyn_name)")

    try:
        record = dv._get(
            f"bookableresourcebookings({bid})?$select={base_select}&$expand={','.join(expand_parts)}",
            include_annotations=True,
        )
        print(record)
        return
    except Exception as e:
        print("EXPAND_FAILED=", str(e))

    # Fallback: just fetch minimal fields.
    record = dv._get(f"bookableresourcebookings({bid})?$select={base_select}", include_annotations=True)
    print(record)


if __name__ == "__main__":
    main()
