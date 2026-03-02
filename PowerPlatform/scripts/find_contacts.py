#!/usr/bin/env python
"""Find contacts for demo cases."""
import sys
sys.path.insert(0, 'src')
from powerplatform.client import DataverseClient

with DataverseClient() as client:
    data = client._request('GET', 'contacts?$select=contactid,fullname,emailaddress1&$top=10&$orderby=fullname')
    contacts = data.get('value', [])
    
    print(f"Available Contacts ({len(contacts)}):")
    for c in contacts:
        print(f"  - {c.get('fullname', 'N/A')} | {c.get('emailaddress1', 'N/A')} | {c['contactid']}")
