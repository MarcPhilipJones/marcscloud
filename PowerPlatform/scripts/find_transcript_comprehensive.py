#!/usr/bin/env python
"""
Get the conversation transcript - comprehensive search.
"""

import sys
import os
import json
import base64

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from powerplatform.client import DataverseClient

CONVERSATION_ID = "b6745d2f-2b3e-4344-8a8e-457d542e8dfa"


def main():
    with DataverseClient() as client:
        # Add annotation header for formatted values
        original_headers = client._auth.get_headers
        def patched_headers():
            h = original_headers()
            h["Prefer"] = 'odata.include-annotations="*"'
            return h
        client._auth.get_headers = patched_headers
        
        print("=" * 80)
        print("COMPREHENSIVE TRANSCRIPT SEARCH")
        print("=" * 80)
        
        # Method 1: Get all fields from the conversation
        print("\n1. All conversation fields:")
        print("-" * 60)
        try:
            conv = client._request("GET", f"msdyn_ocliveworkitems({CONVERSATION_ID})")
            # Look for any transcript-related fields
            for key, value in sorted(conv.items()):
                if value and not key.startswith("@") and "transcript" in key.lower():
                    print(f"  {key}: {str(value)[:200]}")
                if value and not key.startswith("@") and "content" in key.lower():
                    print(f"  {key}: {str(value)[:200]}")
            
            # Show the conversation title
            print(f"\n  Title: {conv.get('msdyn_title')}")
            print(f"  Created: {conv.get('createdon')}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Method 2: Try msdyn_transcript with GUID quotes
        print("\n2. Trying msdyn_transcripts with quoted GUID:")
        print("-" * 60)
        try:
            path = f"msdyn_transcripts?$filter=_msdyn_liveworkitemid_value eq '{CONVERSATION_ID}'"
            result = client._request("GET", path)
            print(f"  Found: {len(result.get('value', []))} transcripts")
            for t in result.get("value", []):
                for k, v in t.items():
                    if v and not k.startswith("@"):
                        print(f"    {k}: {str(v)[:100]}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Method 3: Get all transcripts and filter manually
        print("\n3. Getting recent transcripts and checking for match:")
        print("-" * 60)
        try:
            path = "msdyn_transcripts?$top=20&$orderby=createdon desc"
            result = client._request("GET", path)
            print(f"  Found {len(result.get('value', []))} recent transcripts")
            for t in result.get("value", []):
                lwi = t.get("_msdyn_liveworkitemid_value")
                if lwi:
                    print(f"    - Transcript: {t.get('msdyn_transcriptid')[:8]}... -> LiveWorkItem: {lwi}")
                    if lwi == CONVERSATION_ID:
                        print("      *** MATCH FOUND ***")
                        print(f"      Content: {str(t.get('msdyn_transcriptcontrol', 'N/A'))[:500]}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Method 4: Check annotations on conversation using object type
        print("\n4. Annotations on conversation (by object ID):")
        print("-" * 60)
        try:
            path = f"annotations?$filter=objectid_msdyn_ocliveworkitem/msdyn_ocliveworkitemid eq {CONVERSATION_ID}"
            result = client._request("GET", path)
            print(f"  Found: {len(result.get('value', []))} annotations")
        except Exception as e:
            # Try simpler query
            try:
                path = f"annotations?$top=50&$orderby=createdon desc&$select=annotationid,subject,filename,_objectid_value,objecttypecode"
                result = client._request("GET", path)
                print(f"  Checking {len(result.get('value', []))} recent annotations...")
                for ann in result.get("value", []):
                    obj_id = ann.get("_objectid_value")
                    if obj_id and CONVERSATION_ID in str(obj_id):
                        print(f"    *** MATCH: {ann.get('subject')} - {ann.get('filename')}")
            except Exception as e2:
                print(f"  Error: {e2}")
        
        # Method 5: Get session IDs properly and check their annotations
        print("\n5. Sessions and their annotations:")
        print("-" * 60)
        try:
            path = f"msdyn_ocsessions?$filter=_msdyn_liveworkitemid_value eq '{CONVERSATION_ID}'&$select=msdyn_ocsessionid,createdon,msdyn_name"
            result = client._request("GET", path)
            sessions = result.get("value", [])
            print(f"  Found {len(sessions)} session(s)")
            
            for session in sessions:
                session_id = session.get("msdyn_ocsessionid")
                print(f"\n  Session: {session_id}")
                print(f"  Name: {session.get('msdyn_name')}")
                print(f"  Created: {session.get('createdon')}")
                
                # Get annotations for this session
                if session_id:
                    try:
                        ann_path = f"annotations?$filter=_objectid_value eq '{session_id}'&$select=subject,filename,documentbody,mimetype"
                        ann_result = client._request("GET", ann_path)
                        anns = ann_result.get("value", [])
                        print(f"  Annotations: {len(anns)}")
                        
                        for ann in anns:
                            print(f"    - Subject: {ann.get('subject')}")
                            print(f"      Filename: {ann.get('filename')}")
                            
                            # Decode transcript
                            doc = ann.get("documentbody")
                            if doc:
                                print("\n    TRANSCRIPT CONTENT:")
                                print("    " + "=" * 56)
                                try:
                                    decoded = base64.b64decode(doc).decode("utf-8")
                                    parsed = json.loads(decoded)
                                    
                                    # Pretty print the messages
                                    if isinstance(parsed, list):
                                        for msg in parsed:
                                            sender = msg.get("from", {}).get("user", {}).get("displayName", "Unknown")
                                            content = msg.get("content", "")
                                            timestamp = msg.get("createdDateTime", "")[:19]
                                            
                                            # Strip HTML tags
                                            import re
                                            content = re.sub(r'<[^>]+>', '', content)
                                            
                                            print(f"\n    [{timestamp}] {sender}:")
                                            print(f"      {content}")
                                    else:
                                        print(json.dumps(parsed, indent=2)[:2000])
                                except Exception as e:
                                    print(f"    Decode error: {e}")
                                    print(f"    Raw (first 500): {decoded[:500] if 'decoded' in dir() else doc[:500]}")
                    except Exception as e:
                        print(f"  Error getting annotations: {e}")
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    main()
