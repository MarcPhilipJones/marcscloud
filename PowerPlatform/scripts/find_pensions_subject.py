#!/usr/bin/env python
"""Find Pensions subject and its children."""
import sys
sys.path.insert(0, 'src')
from powerplatform.client import DataverseClient

with DataverseClient() as client:
    # Get all subjects to find Pensions and its children
    data = client._request('GET', 'subjects?$select=subjectid,title,_parentsubject_value&$orderby=title')
    subjects = data.get('value', [])
    
    # Find Pensions subject
    pensions = next((s for s in subjects if s['title'] == 'Pensions'), None)
    if pensions:
        print(f"Pensions Subject ID: {pensions['subjectid']}")
        print(f"Parent ID: {pensions.get('_parentsubject_value')}")
        
        # Find children of Pensions
        children = [s for s in subjects if s.get('_parentsubject_value') == pensions['subjectid']]
        print(f"\nChildren of Pensions ({len(children)}):")
        for c in children:
            print(f"  - {c['title']} ({c['subjectid']})")
    else:
        print('Pensions subject not found')
