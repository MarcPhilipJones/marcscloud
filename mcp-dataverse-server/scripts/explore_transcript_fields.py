"""Explore entity metadata to find correct field names for conversation data."""

import sys
import os
import json

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcp_dataverse_server.config import load_settings
from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.dataverse import DataverseClient

# Most recent conversation ID
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
    
    print("Exploring entity fields for conversation-related tables")
    print("=" * 80)
    
    # Get a sample transcript record and see all its fields
    print("\n1. Sample msdyn_transcript record fields:")
    try:
        result = client._get("msdyn_transcripts?$top=1")
        if result.get("value"):
            transcript = result["value"][0]
            print(f"   All fields on transcript record:")
            for k, v in sorted(transcript.items()):
                if not k.startswith("@"):
                    val_str = str(v)[:80] if v else "null"
                    print(f"      {k}: {val_str}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Get a sample message block and see all fields
    print("\n2. Sample msdyn_conversationmessageblock record fields:")
    try:
        result = client._get("msdyn_conversationmessageblocks?$top=1")
        if result.get("value"):
            msg = result["value"][0]
            print(f"   All fields on message block record:")
            for k, v in sorted(msg.items()):
                if not k.startswith("@"):
                    val_str = str(v)[:80] if v else "null"
                    print(f"      {k}: {val_str}")
    except Exception as e:
        print(f"   Error: {e}")
        
    # Get an ocliveworkitem and see all relationships
    print(f"\n3. Full msdyn_ocliveworkitem record for conversation {LATEST_CONVERSATION_ID}:")
    try:
        result = client._get(f"msdyn_ocliveworkitems({LATEST_CONVERSATION_ID})")
        print(f"   All fields:")
        for k, v in sorted(result.items()):
            if not k.startswith("@"):
                val_str = str(v)[:100] if v else "null"
                print(f"      {k}: {val_str}")
    except Exception as e:
        print(f"   Error: {e}")
        
    # Check session record details
    print(f"\n4. Session records linked to conversation:")
    try:
        result = client._get(f"msdyn_ocsessions?$filter=_msdyn_liveworkitemid_value eq {LATEST_CONVERSATION_ID}&$top=2")
        if result.get("value"):
            for session in result["value"]:
                print(f"\n   Session fields:")
                for k, v in sorted(session.items()):
                    if not k.startswith("@") and v:
                        val_str = str(v)[:100] if v else "null"
                        print(f"      {k}: {val_str}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Look for msdyn_ocliveworkstreamcontextvariable or similar
    print(f"\n5. Looking for related entities via navigation properties...")
    try:
        # Try expanding the transcript relationship
        result = client._get(f"msdyn_ocliveworkitems({LATEST_CONVERSATION_ID})?$expand=msdyn_msdyn_ocliveworkitem_msdyn_transcript")
        transcripts = result.get("msdyn_msdyn_ocliveworkitem_msdyn_transcript", [])
        if transcripts:
            print(f"   Found {len(transcripts)} transcripts via navigation")
            for t in transcripts[:1]:
                for k, v in sorted(t.items()):
                    if not k.startswith("@") and v:
                        val_str = str(v)[:200] if v else "null"
                        print(f"      {k}: {val_str}")
    except Exception as e:
        print(f"   Navigation error: {e}")


if __name__ == "__main__":
    main()
