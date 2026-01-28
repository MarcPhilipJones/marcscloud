"""Explore conversation entities for a contact in Dataverse."""

import sys
import os
import json
from urllib.parse import quote

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcp_dataverse_server.config import load_settings
from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.dataverse import DataverseClient

# Chris Walker contact GUID
CONTACT_ID = "7fba73b9-2461-ef11-bfe2-002248a36d0e"


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
    
    print(f"Exploring conversations for contact: {CONTACT_ID}")
    print("=" * 80)
    
    # First, let's look at what activities are associated with this contact
    # The timeline in D365 shows activities, which include conversations
    
    # Try to find Omnichannel conversations (msdyn_ocliveworkitem)
    print("\n1. Looking for Omnichannel Live Work Items (msdyn_ocliveworkitem)...")
    try:
        path = f"msdyn_ocliveworkitems?$filter=_msdyn_customer_value eq {CONTACT_ID}&$orderby=createdon desc&$top=5"
        result = client._get(path)
        if result.get("value"):
            print(f"   Found {len(result['value'])} Omnichannel conversations")
            for conv in result["value"]:
                print(f"   - {conv.get('msdyn_title', 'No title')} | Created: {conv.get('createdon')} | ID: {conv.get('msdyn_ocliveworkitemid')}")
        else:
            print("   No Omnichannel live work items found")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Try activities (activitypointer) - this is the base entity for timeline items
    print("\n2. Looking for Activity Pointers (timeline activities)...")
    try:
        path = f"activitypointers?$filter=_regardingobjectid_value eq {CONTACT_ID}&$orderby=createdon desc&$top=10"
        result = client._get(path)
        if result.get("value"):
            print(f"   Found {len(result['value'])} activities")
            for act in result["value"]:
                print(f"   - Type: {act.get('activitytypecode')} | Subject: {act.get('subject', 'No subject')[:50]} | Created: {act.get('createdon')}")
        else:
            print("   No activities found")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Try msdyn_transcript entity (conversation transcripts)
    print("\n3. Looking for Conversation Transcripts (msdyn_transcript)...")
    try:
        path = "msdyn_transcripts?$top=5&$orderby=createdon desc"
        result = client._get(path)
        if result.get("value"):
            print(f"   Found {len(result['value'])} transcripts")
            for t in result["value"]:
                print(f"   - ID: {t.get('msdyn_transcriptid')} | Conversation: {t.get('_msdyn_ocliveworkitemid_value')} | Created: {t.get('createdon')}")
        else:
            print("   No transcripts found")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Try the msdyn_conversationmessageblock entity 
    print("\n4. Looking for Conversation Message Blocks...")
    try:
        path = "msdyn_conversationmessageblocks?$top=5&$orderby=createdon desc"
        result = client._get(path)
        if result.get("value"):
            print(f"   Found {len(result['value'])} message blocks")
            for m in result["value"]:
                print(f"   - ID: {m.get('msdyn_conversationmessageblockid')} | Created: {m.get('createdon')}")
        else:
            print("   No message blocks found")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Let's also check for phone calls, emails, and other activity types
    print("\n5. Looking for specific activity types (phonecalls, emails, tasks)...")
    for entity in ["phonecalls", "emails", "tasks", "appointments"]:
        try:
            path = f"{entity}?$filter=_regardingobjectid_value eq {CONTACT_ID}&$orderby=createdon desc&$top=3"
            result = client._get(path)
            if result.get("value"):
                print(f"   {entity}: Found {len(result['value'])} records")
                for act in result["value"]:
                    print(f"      - Subject: {act.get('subject', 'No subject')[:40]} | Created: {act.get('createdon')}")
            else:
                print(f"   {entity}: None found")
        except Exception as e:
            print(f"   {entity}: Error - {e}")


if __name__ == "__main__":
    main()
