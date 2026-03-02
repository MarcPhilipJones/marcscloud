#!/usr/bin/env python
"""Check conversation end status and relationship traversal."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcp_dataverse_server.config import load_settings
from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.dataverse import DataverseClient


def main():
    settings = load_settings()
    token_provider = TokenProvider(
        tenant_id=settings.dataverse_tenant_id,
        client_id=settings.dataverse_client_id,
        client_secret=settings.dataverse_client_secret,
        resource=settings.dataverse_base_url,
    )
    client = DataverseClient(
        base_url=settings.dataverse_base_url,
        api_version=settings.dataverse_api_version,
        token_provider=token_provider,
    )

    print("=" * 80)
    print("CONVERSATION STATUS AND RELATIONSHIPS")
    print("=" * 80)

    # Get recent conversations with all status fields
    path = "msdyn_ocliveworkitems?$select=msdyn_ocliveworkitemid,msdyn_title,createdon,statecode,statuscode,_msdyn_customer_value,_msdyn_caseid_value,_regardingobjectid_value&$orderby=createdon desc&$top=5"
    result = client._get(path)

    for conv in result.get("value", []):
        print()
        print(f"Conversation ID: {conv.get('msdyn_ocliveworkitemid')}")
        print(f"Title: {conv.get('msdyn_title', 'N/A')}")
        print(f"Created: {conv.get('createdon')}")
        print()
        print("STATUS:")
        print(f"  statecode: {conv.get('statecode')} ({conv.get('statecode@OData.Community.Display.V1.FormattedValue', 'N/A')})")
        print(f"  statuscode: {conv.get('statuscode')} ({conv.get('statuscode@OData.Community.Display.V1.FormattedValue', 'N/A')})")
        print()
        print("RELATIONSHIPS:")
        print(f"  Customer: {conv.get('_msdyn_customer_value')}")
        print(f"    Name: {conv.get('_msdyn_customer_value@OData.Community.Display.V1.FormattedValue', 'N/A')}")
        print(f"    Type: {conv.get('_msdyn_customer_value@Microsoft.Dynamics.CRM.lookuplogicalname', 'N/A')}")
        print()
        print(f"  Case: {conv.get('_msdyn_caseid_value', 'None')}")
        print(f"    Name: {conv.get('_msdyn_caseid_value@OData.Community.Display.V1.FormattedValue', 'N/A')}")
        print()
        print(f"  Regarding: {conv.get('_regardingobjectid_value', 'None')}")
        print(f"    Name: {conv.get('_regardingobjectid_value@OData.Community.Display.V1.FormattedValue', 'N/A')}")
        print(f"    Type: {conv.get('_regardingobjectid_value@Microsoft.Dynamics.CRM.lookuplogicalname', 'N/A')}")
        print("-" * 80)

    # Now get the option set values for status
    print()
    print("=" * 80)
    print("STATUS CODE OPTION SET VALUES")
    print("=" * 80)
    
    try:
        # Get entity metadata for msdyn_ocliveworkitem
        metadata_path = "EntityDefinitions(LogicalName='msdyn_ocliveworkitem')/Attributes/Microsoft.Dynamics.CRM.StatusAttributeMetadata?$select=LogicalName&$expand=OptionSet($select=Options)"
        metadata = client._get(metadata_path)
        
        if "value" in metadata:
            for attr in metadata["value"]:
                print(f"\n{attr.get('LogicalName')} options:")
                options = attr.get("OptionSet", {}).get("Options", [])
                for opt in options:
                    print(f"  {opt.get('Value')}: {opt.get('Label', {}).get('UserLocalizedLabel', {}).get('Label', 'N/A')}")
    except Exception as e:
        print(f"Could not get metadata: {e}")

    # Get statecode options too
    try:
        state_path = "EntityDefinitions(LogicalName='msdyn_ocliveworkitem')/Attributes/Microsoft.Dynamics.CRM.StateAttributeMetadata?$select=LogicalName&$expand=OptionSet($select=Options)"
        state_meta = client._get(state_path)
        
        if "value" in state_meta:
            for attr in state_meta["value"]:
                print(f"\n{attr.get('LogicalName')} options:")
                options = attr.get("OptionSet", {}).get("Options", [])
                for opt in options:
                    print(f"  {opt.get('Value')}: {opt.get('Label', {}).get('UserLocalizedLabel', {}).get('Label', 'N/A')}")
    except Exception as e:
        print(f"Could not get state metadata: {e}")


if __name__ == "__main__":
    main()
