"""Check current state of knowledge articles."""

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
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

    with httpx.Client(timeout=30.0) as client:
        url = f'{base_url}/api/data/{api_version}/knowledgearticles'
        params = {
            "$filter": "contains(title, 'Basic Backflushing')",
            "$select": "knowledgearticleid,title,statecode,statuscode,articlepublicnumber,majorversionnumber,minorversionnumber,isrootarticle"
        }
        resp = client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        
        articles = resp.json().get('value', [])
        print(f"Found {len(articles)} article(s):\n")
        
        state_map = {0: 'Draft', 1: 'Approved', 2: 'Scheduled', 3: 'Published', 4: 'Expired', 5: 'Archived', 6: 'Discarded'}
        
        for art in articles:
            print(f"Title: {art['title']}")
            print(f"  ID: {art['knowledgearticleid']}")
            print(f"  State: {state_map.get(art['statecode'], 'Unknown')} (statecode={art['statecode']}, statuscode={art['statuscode']})")
            print(f"  Article#: {art.get('articlepublicnumber')}, Version: {art.get('majorversionnumber')}.{art.get('minorversionnumber')}")
            print(f"  IsRoot: {art.get('isrootarticle')}")
            print()


if __name__ == "__main__":
    main()
