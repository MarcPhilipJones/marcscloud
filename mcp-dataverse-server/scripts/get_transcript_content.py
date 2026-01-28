"""Get the full transcript content for Chris Walker's most recent conversation."""

import sys
import os
import json

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcp_dataverse_server.config import load_settings
from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.dataverse import DataverseClient

# Chris Walker contact GUID
CONTACT_ID = "7fba73b9-2461-ef11-bfe2-002248a36d0e"
# Most recent conversation ID
LATEST_CONVERSATION_ID = "b6745d2f-2b3e-4344-8a8e-457d542e8dfa"
# Transcript ID we found
TRANSCRIPT_ID = "4db8302a-241b-4c9e-a6a4-a6460917e41b"


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
    
    print(f"Getting transcript content for conversation: {LATEST_CONVERSATION_ID}")
    print("=" * 80)
    
    # Get the full transcript record
    print("\n1. Full Transcript Record:")
    try:
        transcript = client._get(f"msdyn_transcripts({TRANSCRIPT_ID})")
        print(f"   All fields:")
        for k, v in sorted(transcript.items()):
            if not k.startswith("@") and v:
                val_str = str(v)[:200] if v else "null"
                print(f"      {k}: {val_str}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Now let's look for message blocks with the correct field name
    print(f"\n2. Message Blocks (using _msdyn_ocliveworkitemid_value):")
    try:
        path = f"msdyn_conversationmessageblocks?$filter=_msdyn_ocliveworkitemid_value eq {LATEST_CONVERSATION_ID}&$orderby=createdon asc&$top=20"
        result = client._get(path)
        if result.get("value"):
            print(f"   Found {len(result['value'])} message blocks")
            for msg in result["value"]:
                print(f"\n   Message block: {msg.get('msdyn_conversationmessageblockid')}")
                for k, v in sorted(msg.items()):
                    if not k.startswith("@") and v:
                        val_str = str(v)[:100] if v else "null"
                        print(f"      {k}: {val_str}")
        else:
            print("   No message blocks found")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Look for msdyn_ocliveworkitemmessage (actual chat messages)
    print(f"\n3. Looking for Omnichannel Messages (msdyn_ocliveworkitemmessages):")
    try:
        # Try without filter first to see fields
        path = "msdyn_ocliveworkitemmessages?$top=1"
        result = client._get(path)
        if result.get("value"):
            msg = result["value"][0]
            print(f"   Sample message fields:")
            for k, v in sorted(msg.items()):
                if not k.startswith("@"):
                    val_str = str(v)[:80] if v else "null"
                    print(f"      {k}: {val_str}")
            
            # Now find the lookup field and query for our conversation
            print(f"\n   Looking for messages for conversation {LATEST_CONVERSATION_ID}...")
            # Look for the field that references the live work item
            lwi_field = None
            for k in msg.keys():
                if "liveworkitem" in k.lower() and "_value" in k:
                    lwi_field = k
                    break
            
            if lwi_field:
                print(f"   Found lookup field: {lwi_field}")
                path = f"msdyn_ocliveworkitemmessages?$filter={lwi_field} eq {LATEST_CONVERSATION_ID}&$orderby=createdon asc&$top=50"
                result = client._get(path)
                if result.get("value"):
                    print(f"\n   Found {len(result['value'])} messages for this conversation:\n")
                    for msg in result["value"]:
                        created = msg.get("createdon", "")
                        content = msg.get("msdyn_content", "")
                        sender = msg.get("msdyn_sendername", msg.get("_msdyn_senderid_value@OData.Community.Display.V1.FormattedValue", "Unknown"))
                        msg_type = msg.get("msdyn_messagetype@OData.Community.Display.V1.FormattedValue", msg.get("msdyn_messagetype", ""))
                        print(f"   [{created}] {sender} ({msg_type}):")
                        print(f"      {content[:200] if content else '(no content)'}")
                        print()
        else:
            print("   No messages table found or empty")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Also try msdyn_conversationdata
    print(f"\n4. Looking for Conversation Data (msdyn_conversationdatas):")
    try:
        path = "msdyn_conversationdatas?$top=1"
        result = client._get(path)
        if result.get("value"):
            print(f"   Found conversation data table")
            data = result["value"][0]
            for k, v in sorted(data.items()):
                if not k.startswith("@"):
                    val_str = str(v)[:80] if v else "null"
                    print(f"      {k}: {val_str}")
    except Exception as e:
        print(f"   Error: {e}")


if __name__ == "__main__":
    main()
