#!/usr/bin/env python
"""
Get the conversation transcript from a known conversation ID.

The conversation was found on the case timeline via activitypointers.
"""

import sys
import os
import json
import base64

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from powerplatform.client import DataverseClient

# The conversation ID found on the case timeline
CONVERSATION_ID = "b6745d2f-2b3e-4344-8a8e-457d542e8dfa"
CASE_ID = "7811eee8-60fb-f011-8406-7ced8d4279eb"


def main():
    with DataverseClient() as client:
        print("=" * 80)
        print("CONVERSATION TRANSCRIPT RETRIEVAL")
        print("=" * 80)
        print(f"Case ID: {CASE_ID}")
        print(f"Conversation ID: {CONVERSATION_ID}")
        
        # Step 1: Get conversation details
        print("\n" + "-" * 80)
        print("STEP 1: Get Conversation Details")
        print("-" * 80)
        
        try:
            conv = client._request("GET", f"msdyn_ocliveworkitems({CONVERSATION_ID})")
            print(f"Title: {conv.get('msdyn_title', 'N/A')}")
            print(f"Created: {conv.get('createdon')}")
            print(f"Customer: {conv.get('_msdyn_customer_value@OData.Community.Display.V1.FormattedValue', conv.get('_msdyn_customer_value'))}")
            print(f"Channel: {conv.get('msdyn_channel@OData.Community.Display.V1.FormattedValue', conv.get('msdyn_channel'))}")
            print(f"Status: {conv.get('statuscode@OData.Community.Display.V1.FormattedValue', conv.get('statuscode'))}")
            print(f"Work Stream: {conv.get('_msdyn_liveworkstreamid_value@OData.Community.Display.V1.FormattedValue', 'N/A')}")
        except Exception as e:
            print(f"Error getting conversation details: {e}")
        
        transcript_found = False
        
        # Step 2: Try msdyn_transcripts entity
        print("\n" + "-" * 80)
        print("STEP 2: Look for Transcript in msdyn_transcripts")
        print("-" * 80)
        
        try:
            path = f"msdyn_transcripts?$filter=_msdyn_liveworkitemid_value eq {CONVERSATION_ID}&$orderby=createdon desc"
            result = client._request("GET", path)
            
            if result.get("value"):
                print(f"Found {len(result['value'])} transcript record(s)")
                for t in result["value"]:
                    print(f"\nTranscript ID: {t.get('msdyn_transcriptid')}")
                    print(f"Created: {t.get('createdon')}")
                    
                    # Check all possible content fields
                    content = t.get("msdyn_transcriptcontrol") or t.get("msdyn_output") or t.get("msdyn_transcriptoutput")
                    if content:
                        transcript_found = True
                        print("\nTranscript Content:")
                        print("=" * 60)
                        try:
                            parsed = json.loads(content)
                            print(json.dumps(parsed, indent=2))
                        except:
                            print(content)
            else:
                print("No transcripts found in msdyn_transcripts entity")
        except Exception as e:
            print(f"Error: {e}")
        
        # Step 3: Try annotations (transcript stored as attachment)
        print("\n" + "-" * 80)
        print("STEP 3: Look for Transcript in Annotations (Notes)")
        print("-" * 80)
        
        try:
            path = f"annotations?$filter=_objectid_value eq {CONVERSATION_ID}&$select=annotationid,subject,notetext,filename,documentbody,mimetype,createdon&$orderby=createdon desc"
            result = client._request("GET", path)
            
            if result.get("value"):
                print(f"Found {len(result['value'])} annotation(s)")
                for note in result["value"]:
                    print(f"\nAnnotation ID: {note.get('annotationid')}")
                    print(f"Subject: {note.get('subject')}")
                    print(f"Filename: {note.get('filename')}")
                    print(f"MIME Type: {note.get('mimetype')}")
                    print(f"Created: {note.get('createdon')}")
                    
                    # Decode document body if present
                    doc_body = note.get("documentbody")
                    if doc_body:
                        transcript_found = True
                        print("\nDecoded Transcript Content:")
                        print("=" * 60)
                        try:
                            decoded = base64.b64decode(doc_body).decode("utf-8")
                            try:
                                # Parse and pretty-print JSON
                                parsed = json.loads(decoded)
                                
                                # Format the transcript nicely
                                if isinstance(parsed, list):
                                    for item in parsed:
                                        sender = item.get("from", {}).get("user", {}).get("displayName", "Unknown")
                                        content = item.get("content", "")
                                        timestamp = item.get("createdDateTime", "")
                                        
                                        # Handle HTML content
                                        if "<p>" in content:
                                            import re
                                            content = re.sub(r'<[^>]+>', '', content)
                                        
                                        print(f"\n[{timestamp[:19]}] {sender}:")
                                        print(f"  {content}")
                                else:
                                    print(json.dumps(parsed, indent=2))
                            except json.JSONDecodeError:
                                print(decoded[:5000])
                        except Exception as e:
                            print(f"Error decoding: {e}")
                    
                    # Also show notetext if present
                    notetext = note.get("notetext")
                    if notetext:
                        print(f"\nNote Text: {notetext[:500]}")
            else:
                print("No annotations found")
        except Exception as e:
            print(f"Error: {e}")
        
        # Step 4: Try conversation action messages
        print("\n" + "-" * 80)
        print("STEP 4: Look for Conversation Action/Messages")
        print("-" * 80)
        
        try:
            path = f"msdyn_ocliveworkitemconversationactions?$filter=_msdyn_ocliveworkitemid_value eq {CONVERSATION_ID}&$orderby=createdon asc"
            result = client._request("GET", path)
            
            if result.get("value"):
                print(f"Found {len(result['value'])} conversation actions")
                for action in result["value"]:
                    print(f"  - {action.get('createdon')}: {action.get('msdyn_name', 'N/A')}")
            else:
                print("No conversation actions found")
        except Exception as e:
            print(f"Entity not found or error: {e}")
        
        # Step 5: Check msdyn_ocsession for session-based transcripts
        print("\n" + "-" * 80)
        print("STEP 5: Look for Session Data")
        print("-" * 80)
        
        try:
            path = f"msdyn_ocsessions?$filter=_msdyn_liveworkitemid_value eq {CONVERSATION_ID}&$orderby=createdon desc"
            result = client._request("GET", path)
            
            if result.get("value"):
                print(f"Found {len(result['value'])} session(s)")
                for session in result["value"]:
                    session_id = session.get("msdyn_ocsessionid")
                    print(f"\n  Session ID: {session_id}")
                    print(f"  Created: {session.get('createdon')}")
                    print(f"  Agent: {session.get('_msdyn_agentid_value@OData.Community.Display.V1.FormattedValue', session.get('_msdyn_agentid_value'))}")
                    
                    # Try to get transcript for this session
                    try:
                        ann_path = f"annotations?$filter=_objectid_value eq {session_id}&$select=subject,filename,documentbody"
                        ann_result = client._request("GET", ann_path)
                        if ann_result.get("value"):
                            print(f"  Found {len(ann_result['value'])} annotation(s) on session")
                    except:
                        pass
            else:
                print("No sessions found")
        except Exception as e:
            print(f"Error: {e}")
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Transcript Found: {'Yes' if transcript_found else 'No - try checking the conversation directly in D365'}")


if __name__ == "__main__":
    main()
