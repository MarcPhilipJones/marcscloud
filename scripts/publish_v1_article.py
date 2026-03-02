"""Publish the Version 1.0 draft knowledge article."""

import sys
import os

os.chdir(r'c:\VSCODE_Developement\logicappsdevelopment\logicappsdevelopment\mcp-dataverse-server')
sys.path.insert(0, 'src')

import httpx
from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings


def main():
    settings = load_settings()
    token_provider = TokenProvider(
        tenant_id=settings.dataverse_tenant_id,
        client_id=settings.dataverse_client_id,
        client_secret=settings.dataverse_client_secret,
        resource=settings.dataverse_base_url
    )
    token = token_provider.get_access_token()
    base_url = settings.dataverse_base_url
    api_version = settings.dataverse_api_version
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'OData-MaxVersion': '4.0',
        'OData-Version': '4.0',
        'Accept': 'application/json'
    }

    # The Version 1.0 draft article
    article_id = "bd5b4fbb-aa3b-45d3-b699-423583d26a92"
    
    with httpx.Client(timeout=30.0) as client:
        print(f"Publishing article ID: {article_id} (Version 1.0)")
        
        # Direct status update to Published
        update_url = f"{base_url}/api/data/{api_version}/knowledgearticles({article_id})"
        update_body = {
            "statecode": 3,
            "statuscode": 7
        }
        
        try:
            resp = client.patch(update_url, headers=headers, json=update_body)
            resp.raise_for_status()
            print("SUCCESS: Article published via direct status update")
        except httpx.HTTPStatusError as e:
            print(f"Failed: {e.response.status_code}")
            print(f"Response: {e.response.text}")
            return
        
        # Verify
        print("\n--- Verifying ---")
        resp = client.get(f"{base_url}/api/data/{api_version}/knowledgearticles({article_id})", 
                         headers=headers,
                         params={"$select": "title,statecode,statuscode,majorversionnumber,minorversionnumber"})
        resp.raise_for_status()
        updated = resp.json()
        state_map = {0: 'Draft', 1: 'Approved', 2: 'Scheduled', 3: 'Published', 4: 'Expired', 5: 'Archived', 6: 'Discarded'}
        print(f"Article: {updated['title']}")
        print(f"Version: {updated.get('majorversionnumber')}.{updated.get('minorversionnumber')}")
        print(f"State: {state_map.get(updated['statecode'], 'Unknown')} (statecode={updated['statecode']}, statuscode={updated['statuscode']})")


if __name__ == "__main__":
    main()
