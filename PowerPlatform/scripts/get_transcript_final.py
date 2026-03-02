#!/usr/bin/env python
"""
Get the conversation transcript - final attempt with correct OData syntax.
"""

import sys
import os
import json
import base64
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from powerplatform.client import DataverseClient

CONVERSATION_ID = "b6745d2f-2b3e-4344-8a8e-457d542e8dfa"


def main():
    with DataverseClient() as client:
        print("=" * 80)
        print("TRANSCRIPT RETRIEVAL FOR CONVERSATION")
        print("=" * 80)
        print(f"Conversation ID: {CONVERSATION_ID}")
        
        # Get all transcripts and find matching one
        print("\n1. Searching all transcripts for matching conversation...")
        print("-" * 60)
        
        transcript_content = None
        
        try:
            # Get transcripts with all fields
            path = "msdyn_transcripts?$top=50&$orderby=createdon desc"
            result = client._request("GET", path)
            transcripts = result.get("value", [])
            print(f"   Retrieved {len(transcripts)} recent transcripts")
            
            for t in transcripts:
                lwi_value = t.get("_msdyn_liveworkitemid_value", "")
                if lwi_value and lwi_value.lower() == CONVERSATION_ID.lower():
                    print(f"\n   ✓ MATCH FOUND!")
                    print(f"   Transcript ID: {t.get('msdyn_transcriptid')}")
                    print(f"   Created: {t.get('createdon')}")
                    
                    # Get the content
                    transcript_content = t.get("msdyn_transcriptcontrol") or t.get("msdyn_output")
                    
                    if transcript_content:
                        print("\n   Content found in msdyn_transcriptcontrol!")
                    else:
                        print("\n   No content in standard fields, listing all non-null fields:")
                        for k, v in t.items():
                            if v and not k.startswith("@") and not k.startswith("_"):
                                print(f"      {k}: {str(v)[:80]}")
                    break
        except Exception as e:
            print(f"   Error: {e}")
        
        # Try getting transcript directly with navigation
        print("\n2. Getting transcript via conversation expand...")
        print("-" * 60)
        
        try:
            # Try to expand the transcript relationship from the conversation
            path = f"msdyn_ocliveworkitems({CONVERSATION_ID})?$expand=msdyn_msdyn_ocliveworkitem_msdyn_transcript_liveworkitemid"
            result = client._request("GET", path)
            expanded = result.get("msdyn_msdyn_ocliveworkitem_msdyn_transcript_liveworkitemid", [])
            if expanded:
                print(f"   Found {len(expanded)} transcript(s) via expand")
                for t in expanded:
                    print(f"   - ID: {t.get('msdyn_transcriptid')}")
                    content = t.get("msdyn_transcriptcontrol")
                    if content:
                        transcript_content = content
        except Exception as e:
            print(f"   Error (expand may not be available): {e}")
        
        # Check session annotations
        print("\n3. Checking session annotations...")
        print("-" * 60)
        
        try:
            # First get sessions
            path = f"msdyn_ocsessions?$select=msdyn_ocsessionid,msdyn_name,createdon&$top=100"
            result = client._request("GET", path)
            sessions = result.get("value", [])
            
            # For each session, check if it's linked to our conversation
            for session in sessions:
                session_id = session.get("msdyn_ocsessionid")
                if not session_id:
                    continue
                
                # Get the full session record to check the liveworkitem link
                try:
                    session_full = client._request("GET", f"msdyn_ocsessions({session_id})?$select=_msdyn_liveworkitemid_value")
                    lwi = session_full.get("_msdyn_liveworkitemid_value", "")
                    
                    if lwi.lower() == CONVERSATION_ID.lower():
                        print(f"\n   ✓ Found matching session: {session_id}")
                        print(f"   Session Name: {session.get('msdyn_name')}")
                        print(f"   Created: {session.get('createdon')}")
                        
                        # Get annotations for this session
                        ann_path = f"annotations?$filter=_objectid_value eq {session_id}&$select=annotationid,subject,filename,documentbody,notetext,mimetype"
                        ann_result = client._request("GET", ann_path)
                        annotations = ann_result.get("value", [])
                        
                        if annotations:
                            print(f"   Found {len(annotations)} annotation(s)")
                            
                            for ann in annotations:
                                print(f"\n   Annotation: {ann.get('subject')}")
                                print(f"   Filename: {ann.get('filename')}")
                                
                                # Decode the transcript
                                doc_body = ann.get("documentbody")
                                if doc_body and "transcript" in (ann.get("filename") or "").lower():
                                    print("\n" + "=" * 60)
                                    print("TRANSCRIPT CONTENT")
                                    print("=" * 60)
                                    
                                    try:
                                        decoded = base64.b64decode(doc_body).decode("utf-8")
                                        parsed = json.loads(decoded)
                                        
                                        if isinstance(parsed, list):
                                            for msg in parsed:
                                                # Extract sender info
                                                from_info = msg.get("from", {})
                                                user_info = from_info.get("user", {})
                                                sender = user_info.get("displayName", "Unknown")
                                                
                                                # Extract message content
                                                content = msg.get("content", "")
                                                timestamp = msg.get("createdDateTime", "")[:19]
                                                
                                                # Strip HTML tags
                                                content = re.sub(r'<[^>]+>', '', content).strip()
                                                
                                                if content:
                                                    print(f"\n[{timestamp}] {sender}:")
                                                    print(f"  {content}")
                                        else:
                                            print(json.dumps(parsed, indent=2))
                                        
                                        transcript_content = decoded
                                        
                                    except Exception as e:
                                        print(f"   Decode error: {e}")
                                        print(f"   Raw content (first 1000 chars):")
                                        try:
                                            decoded = base64.b64decode(doc_body).decode("utf-8")
                                            print(decoded[:1000])
                                        except:
                                            pass
                        break
                except:
                    continue
        except Exception as e:
            print(f"   Error: {e}")
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        if transcript_content:
            print("✓ Transcript successfully retrieved!")
        else:
            print("✗ Transcript not found via API")
            print("\nPossible reasons:")
            print("  - Transcript may be stored in a different format")
            print("  - May need specific Omnichannel for Customer Service license")
            print("  - Transcript storage location varies by channel type")


if __name__ == "__main__":
    main()
