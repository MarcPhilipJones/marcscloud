"""Find and retrieve the actual chat messages for a conversation."""

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
    
    print(f"Finding actual chat messages for conversation: {LATEST_CONVERSATION_ID}")
    print("=" * 80)
    
    # Try various entity names that might contain messages
    entities_to_try = [
        "msdyn_conversationmessages",
        "msdyn_ocliveworkitemcharacteristics", 
        "msdyn_ocsessioncharacteristics",
        "msdyn_ocliveworkitemcontextitems",
        "msdyn_conversationactions",
        "msdyn_conversationinsights",
        "msdyn_oclinesaveds",
        "msdyn_ocsentimentdailytopics",
    ]
    
    print("\n1. Trying to find message entities...")
    for entity in entities_to_try:
        try:
            result = client._get(f"{entity}?$top=1")
            if result.get("value"):
                print(f"\n   {entity}: EXISTS - Sample fields:")
                for k, v in list(sorted(result["value"][0].items()))[:10]:
                    if not k.startswith("@"):
                        val_str = str(v)[:60] if v else "null"
                        print(f"      {k}: {val_str}")
        except Exception as e:
            if "404" not in str(e):
                print(f"   {entity}: Error - {e}")
    
    # Try the transcript annotation approach - transcript may have file attachment
    print(f"\n2. Looking for transcript file attachments (annotations on transcript):")
    TRANSCRIPT_ID = "4db8302a-241b-4c9e-a6a4-a6460917e41b"
    try:
        path = f"annotations?$filter=_objectid_value eq {TRANSCRIPT_ID}&$top=5"
        result = client._get(path)
        if result.get("value"):
            print(f"   Found {len(result['value'])} annotations on transcript")
            for ann in result["value"]:
                print(f"\n   Annotation: {ann.get('annotationid')}")
                print(f"      Subject: {ann.get('subject')}")
                print(f"      FileName: {ann.get('filename')}")
                print(f"      MimeType: {ann.get('mimetype')}")
                doc_body = ann.get("documentbody")
                if doc_body:
                    print(f"      DocumentBody length: {len(doc_body)} chars")
                    # Decode if it's base64
                    import base64
                    try:
                        decoded = base64.b64decode(doc_body).decode('utf-8')
                        print(f"      Decoded content (first 1000 chars):")
                        print(f"      {decoded[:1000]}")
                    except:
                        print(f"      (Could not decode)")
        else:
            print("   No annotations found on transcript")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Try expanding the ocliveworkitem with all relationships
    print(f"\n3. Checking ocliveworkitem navigation properties via $metadata:")
    try:
        # Get metadata for the entity
        result = client._get(f"msdyn_ocliveworkitems({LATEST_CONVERSATION_ID})?$expand=msdyn_msdyn_ocliveworkitem_msdyn_ocsessionparticipantevent")
        events = result.get("msdyn_msdyn_ocliveworkitem_msdyn_ocsessionparticipantevent", [])
        if events:
            print(f"   Found {len(events)} session participant events")
            for event in events[:5]:
                print(f"\n   Event: {event.get('msdyn_ocsessionparticipanteventid')}")
                for k, v in sorted(event.items()):
                    if not k.startswith("@") and v:
                        val_str = str(v)[:100] if v else "null"
                        print(f"      {k}: {val_str}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Try msdyn_ocsessionparticipantevent directly  
    print(f"\n4. Looking for session participant events (msdyn_ocsessionparticipantevents):")
    try:
        path = f"msdyn_ocsessionparticipantevents?$top=1"
        result = client._get(path)
        if result.get("value"):
            event = result["value"][0]
            print(f"   Sample event fields:")
            for k, v in sorted(event.items()):
                if not k.startswith("@"):
                    val_str = str(v)[:80] if v else "null"
                    print(f"      {k}: {val_str}")
            
            # Now filter for our conversation's sessions
            session_ids = ["fe39c2d8-4ea6-45a9-b1c1-e77efd80114b", "fcc4dcb9-2184-4f44-9f1c-7f7ca0cb533f"]
            for session_id in session_ids:
                print(f"\n   Events for session {session_id}:")
                path = f"msdyn_ocsessionparticipantevents?$filter=_msdyn_sessionid_value eq {session_id}&$orderby=createdon asc&$top=20"
                result = client._get(path)
                if result.get("value"):
                    print(f"      Found {len(result['value'])} events")
                    for ev in result["value"]:
                        created = ev.get("createdon", "")
                        event_type = ev.get("msdyn_eventtype@OData.Community.Display.V1.FormattedValue", ev.get("msdyn_eventtype", ""))
                        participant = ev.get("_msdyn_participantid_value@OData.Community.Display.V1.FormattedValue", "")
                        content = ev.get("msdyn_messagedata", ev.get("msdyn_eventtext", ""))[:100] if ev.get("msdyn_messagedata") or ev.get("msdyn_eventtext") else ""
                        print(f"      [{created}] {event_type} - {participant}: {content}")
    except Exception as e:
        print(f"   Error: {e}")


if __name__ == "__main__":
    main()
