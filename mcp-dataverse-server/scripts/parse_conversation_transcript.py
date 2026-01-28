"""Get and parse the complete chat transcript for Chris Walker's last conversation."""

import sys
import os
import json
import base64

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcp_dataverse_server.config import load_settings
from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.dataverse import DataverseClient

# Most recent conversation ID
LATEST_CONVERSATION_ID = "b6745d2f-2b3e-4344-8a8e-457d542e8dfa"
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
    
    print("=" * 80)
    print("CHRIS WALKER'S LAST CONVERSATION TRANSCRIPT")
    print(f"Conversation ID: {LATEST_CONVERSATION_ID}")
    print("=" * 80)
    
    # Get the annotation with the message file
    path = f"annotations?$filter=_objectid_value eq {TRANSCRIPT_ID}&$select=annotationid,subject,filename,documentbody&$top=5"
    result = client._get(path)
    
    if not result.get("value"):
        print("No transcript annotation found!")
        return
    
    annotation = result["value"][0]
    print(f"\nConversation: {annotation.get('subject')}")
    print(f"File: {annotation.get('filename')}")
    print("-" * 80)
    
    # Decode the base64 document body
    doc_body = annotation.get("documentbody")
    if not doc_body:
        print("No document body found!")
        return
    
    decoded = base64.b64decode(doc_body).decode('utf-8')
    
    # The content is a JSON array wrapped in another array with a "Content" key
    outer = json.loads(decoded)
    
    # Extract the actual messages
    if outer and isinstance(outer, list) and len(outer) > 0:
        content_wrapper = outer[0]
        if isinstance(content_wrapper, dict) and "Content" in content_wrapper:
            messages_json = content_wrapper["Content"]
            messages = json.loads(messages_json)
        elif isinstance(content_wrapper, dict):
            messages = [content_wrapper]
        else:
            messages = outer
    else:
        messages = outer
    
    # Filter out control messages and sort by time
    chat_messages = []
    for msg in messages:
        if isinstance(msg, dict):
            is_control = msg.get("isControlMessage", False)
            content = msg.get("content", "")
            
            # Skip control messages (system events like member join/leave)
            if is_control:
                continue
            
            # Skip if no meaningful content
            if not content or content.startswith("<"):
                continue
            
            # Skip JSON event messages (context/metadata)
            if content.startswith("{") and "EventName" in content:
                continue
            
            chat_messages.append(msg)
    
    # Sort by created time
    chat_messages.sort(key=lambda x: x.get("created", ""))
    
    print(f"\n{len(chat_messages)} messages in conversation:\n")
    
    for msg in chat_messages:
        created = msg.get("created", "")[:19]  # Just date/time without timezone
        sender_info = msg.get("from", {})
        
        if sender_info:
            user_info = sender_info.get("user", {})
            sender_name = user_info.get("displayName", "Unknown")
        else:
            sender_name = "Customer"
        
        content = msg.get("content", "")
        content_type = msg.get("contentType", "text")
        
        # Format nicely
        print(f"[{created}] {sender_name}:")
        if content_type == "text":
            print(f"    {content}")
        else:
            print(f"    [{content_type}] {content[:100]}...")
        print()
    
    print("-" * 80)
    print(f"End of conversation ({len(chat_messages)} messages)")


if __name__ == "__main__":
    main()
