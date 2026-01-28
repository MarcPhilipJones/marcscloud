"""Get the transcript for Chris Walker's most recent conversation."""

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
# Most recent conversation ID from our exploration
LATEST_CONVERSATION_ID = "b6745d2f-2b3e-4344-8a8e-457d542e8dfa"


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
    
    print(f"Getting last conversation transcript for contact: {CONTACT_ID}")
    print(f"Conversation ID: {LATEST_CONVERSATION_ID}")
    print("=" * 80)
    
    # First get the conversation details
    print("\n1. Conversation Details:")
    try:
        conv = client._get(f"msdyn_ocliveworkitems({LATEST_CONVERSATION_ID})")
        print(f"   Title: {conv.get('msdyn_title')}")
        print(f"   Created: {conv.get('createdon')}")
        print(f"   Status: {conv.get('statuscode@OData.Community.Display.V1.FormattedValue', conv.get('statuscode'))}")
        print(f"   Channel: {conv.get('msdyn_channel@OData.Community.Display.V1.FormattedValue', conv.get('msdyn_channel'))}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Get the transcript linked to this conversation
    print("\n2. Looking for transcript...")
    try:
        # First try to find transcript by conversation ID
        path = f"msdyn_transcripts?$filter=_msdyn_liveworkitemid_value eq {LATEST_CONVERSATION_ID}&$orderby=createdon desc&$top=1"
        result = client._get(path)
        if result.get("value"):
            transcript = result["value"][0]
            print(f"   Found transcript ID: {transcript.get('msdyn_transcriptid')}")
            transcript_content = transcript.get("msdyn_transcriptcontrol")
            if transcript_content:
                print(f"\n   Transcript Content (first 2000 chars):")
                print("   " + "-" * 60)
                content = transcript_content[:2000]
                # Pretty print if it's JSON
                try:
                    parsed = json.loads(transcript_content)
                    print(json.dumps(parsed, indent=2)[:2000])
                except:
                    print(f"   {content}")
            else:
                print("   Transcript content is empty or not accessible via this field")
                # Show all fields
                print("\n   Available transcript fields:")
                for k, v in transcript.items():
                    if v and not k.startswith("@"):
                        val_str = str(v)[:100] if v else "None"
                        print(f"      {k}: {val_str}")
        else:
            print("   No transcript found via liveworkitemid")
            
            # Try other approaches
            print("\n   Trying to find transcript via activity relationship...")
            path = f"msdyn_transcripts?$filter=_regardingobjectid_value eq {LATEST_CONVERSATION_ID}&$top=1"
            result = client._get(path)
            if result.get("value"):
                transcript = result["value"][0]
                print(f"   Found transcript ID: {transcript.get('msdyn_transcriptid')}")
            else:
                print("   No transcript found via regardingobject either")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Also check for messages in msdyn_conversationmessageblock
    print("\n3. Looking for conversation messages (msdyn_conversationmessageblock)...")
    try:
        path = f"msdyn_conversationmessageblocks?$filter=_msdyn_conversationid_value eq {LATEST_CONVERSATION_ID}&$orderby=createdon asc&$top=20"
        result = client._get(path)
        if result.get("value"):
            print(f"   Found {len(result['value'])} message blocks")
            for msg in result["value"]:
                sender = msg.get("msdyn_agentname", "Customer")
                content = msg.get("msdyn_content", "")[:100]
                created = msg.get("createdon", "")
                print(f"   [{created}] {sender}: {content}")
        else:
            print("   No message blocks found for this conversation")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Try msdyn_ocsession and related tables
    print("\n4. Looking for session data (msdyn_ocsession)...")
    try:
        path = f"msdyn_ocsessions?$filter=_msdyn_liveworkitemid_value eq {LATEST_CONVERSATION_ID}&$orderby=createdon desc&$top=3"
        result = client._get(path)
        if result.get("value"):
            print(f"   Found {len(result['value'])} sessions")
            for session in result["value"]:
                session_id = session.get("msdyn_ocsessionid")
                print(f"   Session ID: {session_id}")
                print(f"      Started: {session.get('createdon')}")
                print(f"      Agent: {session.get('_msdyn_agentid_value@OData.Community.Display.V1.FormattedValue', session.get('_msdyn_agentid_value'))}")
        else:
            print("   No sessions found")
    except Exception as e:
        print(f"   Error: {e}")
        
    # Look for conversation messages via annotation/notes
    print("\n5. Looking for annotations/notes on conversation...")
    try:
        path = f"annotations?$filter=_objectid_value eq {LATEST_CONVERSATION_ID}&$orderby=createdon desc&$top=5"
        result = client._get(path)
        if result.get("value"):
            print(f"   Found {len(result['value'])} annotations")
            for note in result["value"]:
                print(f"   - Subject: {note.get('subject')}")
                content = note.get("notetext", "")[:200]
                print(f"     Content: {content}")
        else:
            print("   No annotations found")
    except Exception as e:
        print(f"   Error: {e}")


if __name__ == "__main__":
    main()
