#!/usr/bin/env python
"""Find all cases using 'Statements and Documents' subject and build URLs."""
import sys
sys.path.insert(0, 'src')
from powerplatform.client import DataverseClient

with DataverseClient() as client:
    # Find the subject ID
    data = client._request('GET', "subjects?$select=subjectid,title&$filter=title eq 'Statements and Documents'")
    subjects = data.get('value', [])
    
    if not subjects:
        print('Subject not found')
        exit()
    
    subject_id = subjects[0]['subjectid']
    print(f'Subject ID: {subject_id}')
    print()
    
    # Find cases using this subject
    cases_data = client._request('GET', f'incidents?$select=incidentid,title,ticketnumber,createdon&$filter=_subjectid_value eq {subject_id}&$orderby=createdon desc')
    cases = cases_data.get('value', [])
    
    print(f'Found {len(cases)} case(s) using "Statements and Documents":')
    print()
    
    # Base URL for Dynamics 365
    base_url = 'https://org6cb3e9fb.crm4.dynamics.com'
    
    if not cases:
        print('No cases found.')
    else:
        for case in cases:
            case_id = case['incidentid']
            ticket = case.get('ticketnumber', 'N/A')
            title = case.get('title', 'Untitled')
            created = case.get('createdon', '')[:10] if case.get('createdon') else ''
            
            # Build the URL to open the case in Dynamics 365
            url = f'{base_url}/main.aspx?etn=incident&id={case_id}&pagetype=entityrecord'
            
            print(f'{ticket}: {title}')
            print(f'  Created: {created}')
            print(f'  URL: {url}')
            print()
