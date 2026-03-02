"""Compare article content formats."""
import sys
import os
import json

os.chdir(r"c:\VSCODE_Developement\logicappsdevelopment\logicappsdevelopment\mcp-dataverse-server")
sys.path.insert(0, "src")

from dotenv import load_dotenv
load_dotenv(".env")

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings
import httpx

settings = load_settings()
tp = TokenProvider(
    settings.dataverse_tenant_id,
    settings.dataverse_client_id,
    settings.dataverse_client_secret,
    settings.dataverse_base_url
)
token = tp.get_access_token()
base = settings.dataverse_base_url
ver = settings.dataverse_api_version

headers = {"Authorization": f"Bearer {token}"}

with httpx.Client(timeout=30.0) as c:
    # Get the Boiler article
    print("=" * 60)
    print("BOILER ARTICLE (WORKING)")
    print("=" * 60)
    url = f"{base}/api/data/{ver}/knowledgearticles?$filter=contains(title,'Boiler')&$select=title,content&$top=1"
    r = c.get(url, headers=headers)
    if r.status_code == 200 and r.json().get("value"):
        article = r.json()["value"][0]
        print(f"Title: {article.get('title')}")
        content = article.get("content", "")
        print(f"\nContent length: {len(content)}")
        print(f"\nFirst 500 chars:\n{content[:500]}")
    
    # Get my Printer article
    print("\n" + "=" * 60)
    print("PRINTER ARTICLE (NEW)")
    print("=" * 60)
    url = f"{base}/api/data/{ver}/knowledgearticles?$filter=contains(title,'Network Printer Installation')&$select=title,content&$top=1"
    r = c.get(url, headers=headers)
    if r.status_code == 200 and r.json().get("value"):
        article = r.json()["value"][0]
        print(f"Title: {article.get('title')}")
        content = article.get("content", "")
        print(f"\nContent length: {len(content)}")
        print(f"\nFirst 500 chars:\n{content[:500]}")
    else:
        print("Not found or error")
        print(r.text[:300])
    
    # Get the Coffee Grounds article for another comparison
    print("\n" + "=" * 60)
    print("COFFEE GROUNDS ARTICLE (SAMPLE)")
    print("=" * 60)
    url = f"{base}/api/data/{ver}/knowledgearticles?$filter=contains(title,'Coffee')&$select=title,content&$top=1"
    r = c.get(url, headers=headers)
    if r.status_code == 200 and r.json().get("value"):
        article = r.json()["value"][0]
        print(f"Title: {article.get('title')}")
        content = article.get("content", "")
        print(f"\nContent length: {len(content)}")
        print(f"\nFirst 500 chars:\n{content[:500]}")
