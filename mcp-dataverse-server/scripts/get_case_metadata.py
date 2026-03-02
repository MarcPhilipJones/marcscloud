#!/usr/bin/env python
"""
Retrieve Case metadata from Dynamics 365 Customer Service:
- Subjects (from subjects entity)
- Case Origins (caseorigincode option set on incident)
- Priorities (prioritycode option set on incident)
"""

import os
import sys

# Add the parent src to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcp_dataverse_server.config import load_settings
from mcp_dataverse_server.dataverse import DataverseClient


def get_option_set_values(client: DataverseClient, entity_name: str, attribute_name: str) -> list[dict]:
    """
    Retrieve option set values for a given entity attribute.
    
    Uses the EntityDefinitions API to get picklist metadata.
    """
    url = (
        f"EntityDefinitions(LogicalName='{entity_name}')"
        f"/Attributes(LogicalName='{attribute_name}')"
        f"/Microsoft.Dynamics.CRM.PicklistAttributeMetadata"
        f"?$select=LogicalName&$expand=OptionSet($select=Options)"
    )
    
    with client._client() as http:
        resp = http.get(client._url(url), headers=client._headers())
        resp.raise_for_status()
        data = resp.json()
    
    options = data.get("OptionSet", {}).get("Options", [])
    return [
        {
            "value": opt.get("Value"),
            "label": opt.get("Label", {}).get("UserLocalizedLabel", {}).get("Label", "Unknown"),
        }
        for opt in options
    ]


def get_subjects(client: DataverseClient) -> list[dict]:
    """Retrieve all subjects from the subjects entity."""
    url = client._url(
        "subjects"
        "?$select=subjectid,title,description,_parentsubject_value"
        "&$orderby=title"
    )
    
    with client._client() as http:
        resp = http.get(url, headers=client._headers())
        resp.raise_for_status()
        data = resp.json()
    
    return [
        {
            "id": s.get("subjectid"),
            "title": s.get("title"),
            "description": s.get("description"),
            "parent_id": s.get("_parentsubject_value"),
        }
        for s in data.get("value", [])
    ]


def main():
    settings = load_settings()
    client = DataverseClient(settings)
    
    print("=" * 70)
    print("DYNAMICS 365 CUSTOMER SERVICE - CASE METADATA")
    print("=" * 70)
    
    # 1. Get Subjects
    print("\n📋 SUBJECTS")
    print("-" * 40)
    try:
        subjects = get_subjects(client)
        if subjects:
            for s in subjects:
                parent_info = f" (Parent: {s['parent_id'][:8]}...)" if s.get("parent_id") else ""
                print(f"  • {s['title']}{parent_info}")
                if s.get("description"):
                    print(f"    └─ {s['description'][:60]}...")
            print(f"\n  Total: {len(subjects)} subjects")
        else:
            print("  No subjects found.")
    except Exception as e:
        print(f"  Error fetching subjects: {e}")
    
    # 2. Get Case Origins (caseorigincode)
    print("\n📍 CASE ORIGINS (caseorigincode)")
    print("-" * 40)
    try:
        origins = get_option_set_values(client, "incident", "caseorigincode")
        if origins:
            for opt in sorted(origins, key=lambda x: x["value"]):
                print(f"  {opt['value']:3d} = {opt['label']}")
            print(f"\n  Total: {len(origins)} origins")
        else:
            print("  No case origins found.")
    except Exception as e:
        print(f"  Error fetching case origins: {e}")
    
    # 3. Get Priorities (prioritycode)
    print("\n⚡ PRIORITIES (prioritycode)")
    print("-" * 40)
    try:
        priorities = get_option_set_values(client, "incident", "prioritycode")
        if priorities:
            for opt in sorted(priorities, key=lambda x: x["value"]):
                print(f"  {opt['value']:3d} = {opt['label']}")
            print(f"\n  Total: {len(priorities)} priorities")
        else:
            print("  No priorities found.")
    except Exception as e:
        print(f"  Error fetching priorities: {e}")
    
    # Bonus: Also get status codes
    print("\n🔄 STATUS CODES (statuscode)")
    print("-" * 40)
    try:
        statuses = get_option_set_values(client, "incident", "statuscode")
        if statuses:
            for opt in sorted(statuses, key=lambda x: x["value"]):
                print(f"  {opt['value']:3d} = {opt['label']}")
            print(f"\n  Total: {len(statuses)} statuses")
        else:
            print("  No statuses found.")
    except Exception as e:
        print(f"  Error fetching statuses: {e}")
    
    print("\n" + "=" * 70)
    print("Done!")


if __name__ == "__main__":
    main()
