#!/usr/bin/env python
"""
Get the conversation transcript from a case timeline.

Steps:
1. Get the case details
2. Find activities on the case timeline (using regardingobjectid)
3. Find Omnichannel conversations linked to the case
4. Get the transcript content from the conversation
"""

import sys
import os
import json
import base64

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from powerplatform.client import DataverseClient

# The case GUID provided
CASE_ID = "7811eee8-60fb-f011-8406-7ced8d4279eb"


def main():
    with DataverseClient() as client:
        print("=" * 80)
        print("STEP 1: Get Case Details")
        print("=" * 80)
        
        try:
            case = client._request("GET", f"incidents({CASE_ID})?$select=title,ticketnumber,description,createdon,_customerid_value")
            print(f"Case ID: {CASE_ID}")
            print(f"Ticket: {case.get('ticketnumber')}")
            print(f"Title: {case.get('title')}")
            print(f"Created: {case.get('createdon')}")
            print(f"Customer ID: {case.get('_customerid_value')}")
        except Exception as e:
            print(f"Error getting case: {e}")
            return
        
        print("\n" + "=" * 80)
        print("STEP 2: Find Omnichannel Conversations linked to Case")
        print("=" * 80)
        
        # Omnichannel conversations (msdyn_ocliveworkitem) can be linked to a case
        # via the msdyn_caseid lookup field
        conversation_id = None
        
        try:
            path = f"msdyn_ocliveworkitems?$filter=_msdyn_caseid_value eq {CASE_ID}&$orderby=createdon desc&$top=5"
            result = client._request("GET", path)
            
            if result.get("value"):
                print(f"Found {len(result['value'])} conversations linked via msdyn_caseid")
                for conv in result["value"]:
                    conv_id = conv.get("msdyn_ocliveworkitemid")
                    print(f"\n  Conversation ID: {conv_id}")
                    print(f"  Title: {conv.get('msdyn_title', 'N/A')}")
                    print(f"  Created: {conv.get('createdon')}")
                    print(f"  Channel: {conv.get('msdyn_channel@OData.Community.Display.V1.FormattedValue', conv.get('msdyn_channel'))}")
                    print(f"  Status: {conv.get('statuscode@OData.Community.Display.V1.FormattedValue', conv.get('statuscode'))}")
                    if not conversation_id:
                        conversation_id = conv_id
            else:
                print("No conversations found via msdyn_caseid, trying regardingobjectid...")
                
                # Try alternative lookup field
                path = f"msdyn_ocliveworkitems?$filter=_regardingobjectid_value eq {CASE_ID}&$orderby=createdon desc&$top=5"
                result = client._request("GET", path)
                
                if result.get("value"):
                    print(f"Found {len(result['value'])} conversations linked via regardingobjectid")
                    for conv in result["value"]:
                        conv_id = conv.get("msdyn_ocliveworkitemid")
                        print(f"\n  Conversation ID: {conv_id}")
                        print(f"  Title: {conv.get('msdyn_title', 'N/A')}")
                        print(f"  Created: {conv.get('createdon')}")
                        if not conversation_id:
                            conversation_id = conv_id
                else:
                    print("No conversations found via regardingobjectid either")
        except Exception as e:
            print(f"Error: {e}")
        
        if not conversation_id:
            # Try to find activities on the case timeline
            print("\nTrying to find activities on case timeline...")
            try:
                path = f"activitypointers?$filter=_regardingobjectid_value eq {CASE_ID}&$orderby=createdon desc&$top=10&$select=activityid,subject,activitytypecode,createdon"
                result = client._request("GET", path)
                
                if result.get("value"):
                    print(f"Found {len(result['value'])} activities on timeline:")
                    for act in result["value"]:
                        print(f"  - {act.get('activitytypecode')}: {act.get('subject', 'No subject')[:50]} | {act.get('createdon')}")
                        print(f"    Activity ID: {act.get('activityid')}")
                else:
                    print("No activities found on case timeline")
            except Exception as e:
                print(f"Error: {e}")
            return
        
        print("\n" + "=" * 80)
        print("STEP 3: Get Transcript for Conversation")
        print("=" * 80)
        print(f"Using Conversation ID: {conversation_id}")
        
        # Method 1: Try msdyn_transcript entity
        print("\n3a. Looking for transcript in msdyn_transcripts...")
        transcript_found = False
        
        try:
            path = f"msdyn_transcripts?$filter=_msdyn_liveworkitemid_value eq {conversation_id}&$orderby=createdon desc&$top=1"
            result = client._request("GET", path)
            
            if result.get("value"):
                transcript = result["value"][0]
                print(f"Found transcript ID: {transcript.get('msdyn_transcriptid')}")
                
                # Try different content fields
                content = transcript.get("msdyn_transcriptcontrol") or transcript.get("msdyn_output")
                if content:
                    transcript_found = True
                    print("\nTranscript Content:")
                    print("-" * 60)
                    try:
                        parsed = json.loads(content)
                        print(json.dumps(parsed, indent=2))
                    except:
                        print(content)
            else:
                print("No transcript found in msdyn_transcripts")
        except Exception as e:
            print(f"Error: {e}")
        
        # Method 2: Try annotations (notes with transcript attachment)
        if not transcript_found:
            print("\n3b. Looking for transcript in annotations/notes...")
            try:
                path = f"annotations?$filter=_objectid_value eq {conversation_id}&$select=subject,notetext,filename,documentbody,mimetype&$orderby=createdon desc"
                result = client._request("GET", path)
                
                if result.get("value"):
                    print(f"Found {len(result['value'])} annotations")
                    for note in result["value"]:
                        print(f"\n  Subject: {note.get('subject')}")
                        print(f"  Filename: {note.get('filename')}")
                        print(f"  MIME Type: {note.get('mimetype')}")
                        
                        # If there's a document body (base64 encoded), decode it
                        doc_body = note.get("documentbody")
                        if doc_body:
                            print("\n  Document Content (decoded):")
                            print("  " + "-" * 60)
                            try:
                                decoded = base64.b64decode(doc_body).decode("utf-8")
                                # Try to parse as JSON
                                try:
                                    parsed = json.loads(decoded)
                                    print(json.dumps(parsed, indent=2))
                                except:
                                    print(decoded[:5000])
                                transcript_found = True
                            except Exception as e:
                                print(f"  Error decoding: {e}")
                        
                        # Also check notetext
                        notetext = note.get("notetext")
                        if notetext:
                            print(f"\n  Note Text:")
                            print(f"  {notetext[:1000]}")
                else:
                    print("No annotations found")
            except Exception as e:
                print(f"Error: {e}")
        
        # Method 3: Try conversation message blocks
        if not transcript_found:
            print("\n3c. Looking for conversation messages...")
            try:
                path = f"msdyn_conversationmessageblocks?$filter=_msdyn_conversationid_value eq {conversation_id}&$orderby=createdon asc"
                result = client._request("GET", path)
                
                if result.get("value"):
                    print(f"Found {len(result['value'])} message blocks")
                    print("\nConversation Messages:")
                    print("-" * 60)
                    for msg in result["value"]:
                        sender = msg.get("msdyn_agentname") or msg.get("msdyn_sendername") or "Customer"
                        content = msg.get("msdyn_content", "")
                        created = msg.get("createdon", "")[:19]
                        print(f"[{created}] {sender}:")
                        print(f"  {content}\n")
                    transcript_found = True
                else:
                    print("No message blocks found")
            except Exception as e:
                print(f"Error: {e}")
        
        # Method 4: Try msdyn_ocliveworkstreamcontexts or msdyn_ocrecording
        if not transcript_found:
            print("\n3d. Checking for other transcript sources...")
            
            # Check msdyn_ocrecording for voice/video transcripts
            try:
                path = f"msdyn_ocrecordings?$filter=_msdyn_liveworkitemid_value eq {conversation_id}"
                result = client._request("GET", path)
                if result.get("value"):
                    print(f"Found {len(result['value'])} recordings")
                    for rec in result["value"]:
                        print(f"  Recording ID: {rec.get('msdyn_ocrecordingid')}")
                        print(f"  Created: {rec.get('createdon')}")
            except:
                pass
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Case: {case.get('ticketnumber')} - {case.get('title')}")
        print(f"Conversation ID: {conversation_id}")
        print(f"Transcript Found: {'Yes' if transcript_found else 'No'}")


if __name__ == "__main__":
    main()
