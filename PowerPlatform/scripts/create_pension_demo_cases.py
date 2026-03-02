#!/usr/bin/env python
"""Create sample pension cases for UK Pensions Provider demo."""
import sys
import urllib.parse
sys.path.insert(0, 'src')
from powerplatform.client import DataverseClient

# Pensions parent subject ID
PENSIONS_SUBJECT_ID = "31895e8f-61fb-f011-8406-7ced8d4279eb"

# Existing contact IDs
CONTACTS = {
    "Abbie Gardiner": "a7bf9a01-b056-e711-abaa-00155d701c02",
    "Aidan Knaggs": "a9bf9a01-b056-e711-abaa-00155d701c02",
    "Alan Steiner": "00b62b5d-7cb4-ea11-a812-000d3a8b3ec6",
    "Alex Baker": "c5b62b5d-7cb4-ea11-a812-000d3a8b3ec6",
    "Alfonso Albritton": "abbf9a01-b056-e711-abaa-00155d701c02",
    "Alfonso Santos": "b9d2d356-513c-ee11-bdf4-000d3a3386ed",
    "Alva Tharaldsen": "adbf9a01-b056-e711-abaa-00155d701c02",
    "Amanda Hegg": "afbf9a01-b056-e711-abaa-00155d701c02",
    "Andrew Palmer": "b1bf9a01-b056-e711-abaa-00155d701c02",
}

# New subjects to create under Pensions
NEW_SUBJECTS = [
    {"title": "Retirement Options", "description": "Queries about retirement age, flexible retirement, pension forecasts"},
    {"title": "Statements and Documents", "description": "Annual statements, benefit illustrations, member certificates"},
    {"title": "Transfers", "description": "CETV requests, transfers in/out"},
    {"title": "Death Benefits", "description": "Nominations, bereavement claims, dependant benefits"},
    {"title": "Tax and Contributions", "description": "Tax relief, contribution changes, AVCs"},
    {"title": "Personal Details", "description": "Address changes, contact updates"},
    {"title": "Complaints", "description": "Formal complaints and escalations"},
]

# Cases to create
CASES = [
    {
        "title": "Retirement Date Confirmation",
        "description": "Customer requesting confirmation of their earliest retirement date and projected pension value at age 65.",
        "prioritycode": 2,  # Normal
        "caseorigincode": 3,  # Web
        "subject": "Retirement Options",
        "contact": "Abbie Gardiner",
    },
    {
        "title": "Annual Benefit Statement Not Received",
        "description": "Member reports they have not received their annual pension statement which was due in December 2025.",
        "prioritycode": 1,  # High
        "caseorigincode": 1,  # Phone
        "subject": "Statements and Documents",
        "contact": "Aidan Knaggs",
    },
    {
        "title": "Transfer Value Request",
        "description": "Request for a Cash Equivalent Transfer Value (CETV) quote to transfer pension to another provider.",
        "prioritycode": 2,  # Normal
        "caseorigincode": 2,  # Email
        "subject": "Transfers",
        "contact": "Alan Steiner",
    },
    {
        "title": "Death Benefit Nomination Update",
        "description": "Customer wishes to update their expression of wish for death benefit beneficiaries following divorce.",
        "prioritycode": 1,  # High
        "caseorigincode": 3,  # Web
        "subject": "Death Benefits",
        "contact": "Alex Baker",
    },
    {
        "title": "Flexible Retirement Enquiry",
        "description": "Enquiry about partial pension drawdown options while continuing to work part-time from age 60.",
        "prioritycode": 2,  # Normal
        "caseorigincode": 1,  # Phone
        "subject": "Retirement Options",
        "contact": "Alfonso Albritton",
    },
    {
        "title": "Tax Relief Query",
        "description": "Question regarding why tax relief has not been applied to recent additional voluntary contributions.",
        "prioritycode": 2,  # Normal
        "caseorigincode": 2,  # Email
        "subject": "Tax and Contributions",
        "contact": "Alva Tharaldsen",
    },
    {
        "title": "Contribution Increase Request",
        "description": "Request to increase monthly pension contributions from 5% to 8% of salary.",
        "prioritycode": 3,  # Low
        "caseorigincode": 3,  # Web
        "subject": "Tax and Contributions",
        "contact": "Amanda Hegg",
    },
    {
        "title": "Address Change Notification",
        "description": "Member has moved house and needs to update their address and contact details on record.",
        "prioritycode": 3,  # Low
        "caseorigincode": 3,  # Web
        "subject": "Personal Details",
        "contact": "Andrew Palmer",
    },
    {
        "title": "Complaint - Service Delays",
        "description": "Formal complaint regarding 6-week delay in processing retirement application.",
        "prioritycode": 1,  # High
        "caseorigincode": 2,  # Email
        "subject": "Complaints",
        "contact": "Alfonso Santos",
    },
    {
        "title": "State Pension Forecast Integration",
        "description": "Query about how state pension entitlement will integrate with occupational pension at retirement.",
        "prioritycode": 2,  # Normal
        "caseorigincode": 1,  # Phone
        "subject": "Retirement Options",
        "contact": "Abbie Gardiner",
    },
]


def create_subject(client, title, description, parent_id):
    """Create a subject or return existing one."""
    # First check if it already exists
    encoded_title = urllib.parse.quote(title)
    try:
        data = client._request("GET", f"subjects?$filter=title eq '{encoded_title}'&$select=subjectid,title")
        existing = data.get("value", [])
        for s in existing:
            if s.get("title") == title:
                return s["subjectid"], False  # Already exists
    except Exception:
        pass  # Continue to try creating
    
    # Create new subject
    payload = {
        "title": title,
        "description": description,
        "parentsubject@odata.bind": f"/subjects({parent_id})",
    }
    
    # POST returns 204 No Content with OData-EntityId header
    # We need to use a different approach - use Prefer header to get representation
    headers = client._auth.get_headers()
    headers["Prefer"] = "return=representation"
    
    response = client.http_client.request(
        method="POST",
        url="subjects",
        headers=headers,
        json=payload,
    )
    response.raise_for_status()
    
    if response.status_code == 201:
        result = response.json()
        return result.get("subjectid"), True
    elif response.status_code == 204:
        # Extract ID from OData-EntityId header
        entity_id = response.headers.get("OData-EntityId", "")
        # Format: https://.../subjects(guid)
        if "(" in entity_id and ")" in entity_id:
            guid = entity_id.split("(")[-1].rstrip(")")
            return guid, True
    
    return None, False


def create_case(client, title, description, prioritycode, caseorigincode, subject_id, contact_id):
    """Create a case and return the ticket number."""
    payload = {
        "title": title,
        "description": description,
        "prioritycode": prioritycode,
        "caseorigincode": caseorigincode,
        "subjectid@odata.bind": f"/subjects({subject_id})",
        "customerid_contact@odata.bind": f"/contacts({contact_id})",
    }
    
    headers = client._auth.get_headers()
    headers["Prefer"] = "return=representation"
    
    response = client.http_client.request(
        method="POST",
        url="incidents",
        headers=headers,
        json=payload,
    )
    response.raise_for_status()
    
    if response.status_code == 201:
        result = response.json()
        return result.get("incidentid"), result.get("ticketnumber")
    elif response.status_code == 204:
        entity_id = response.headers.get("OData-EntityId", "")
        if "(" in entity_id and ")" in entity_id:
            guid = entity_id.split("(")[-1].rstrip(")")
            return guid, "TBD"
    
    return None, None


def main():
    with DataverseClient() as client:
        subject_ids = {}
        
        # Step 1: Create new subjects under Pensions
        print("=" * 60)
        print("CREATING SUBJECTS")
        print("=" * 60)
        
        for subj in NEW_SUBJECTS:
            try:
                subject_id, created = create_subject(
                    client,
                    subj["title"],
                    subj["description"],
                    PENSIONS_SUBJECT_ID,
                )
                if subject_id:
                    subject_ids[subj["title"]] = subject_id
                    status = "Created" if created else "Exists"
                    print(f"✓ {status}: {subj['title']} ({subject_id[:8]}...)")
                else:
                    print(f"✗ Failed: {subj['title']}")
            except Exception as e:
                print(f"✗ Error creating '{subj['title']}': {e}")
        
        # Step 2: Create cases
        print("\n" + "=" * 60)
        print("CREATING CASES")
        print("=" * 60)
        
        created_cases = []
        for case in CASES:
            subject_id = subject_ids.get(case["subject"])
            contact_id = CONTACTS.get(case["contact"])
            
            if not subject_id:
                print(f"✗ Skipping case '{case['title']}' - subject not found")
                continue
            if not contact_id:
                print(f"✗ Skipping case '{case['title']}' - contact not found")
                continue
            
            try:
                case_id, ticket_number = create_case(
                    client,
                    case["title"],
                    case["description"],
                    case["prioritycode"],
                    case["caseorigincode"],
                    subject_id,
                    contact_id,
                )
                if case_id:
                    created_cases.append({
                        "ticket": ticket_number or "N/A",
                        "title": case["title"],
                        "priority": {1: "High", 2: "Normal", 3: "Low"}[case["prioritycode"]],
                        "origin": {1: "Phone", 2: "Email", 3: "Web"}[case["caseorigincode"]],
                        "contact": case["contact"],
                    })
                    print(f"✓ Created: {ticket_number} - {case['title'][:40]}")
                else:
                    print(f"✗ Failed to create case '{case['title']}'")
            except Exception as e:
                print(f"✗ Error creating case '{case['title']}': {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Subjects: {len(subject_ids)}")
        print(f"Cases created: {len(created_cases)}")
        
        if created_cases:
            print("\n{:<12} | {:<6} | {:<5} | {}".format("Ticket", "Prior", "Orig", "Contact"))
            print("-" * 60)
            for c in created_cases:
                print(f"{c['ticket']:<12} | {c['priority']:<6} | {c['origin']:<5} | {c['contact']}")


if __name__ == "__main__":
    main()
