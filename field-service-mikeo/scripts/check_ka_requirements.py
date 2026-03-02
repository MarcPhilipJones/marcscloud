"""Check knowledge article requirements."""
import sys
import os

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
    # Get English language locale
    url = f"{base}/api/data/{ver}/languagelocales?$filter=localeid eq 1033&$select=languagelocaleid,localeid,name,code"
    r = c.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        print("English Language Locale:")
        for rec in data.get("value", []):
            print(f"  ID: {rec.get('languagelocaleid')}, Name: {rec.get('name')}")
    
    # Get subjects (topics) available
    print("\nAvailable Subjects (sample):")
    url = f"{base}/api/data/{ver}/subjects?$top=10&$select=subjectid,title"
    r = c.get(url, headers=headers)
    if r.status_code == 200:
        for rec in r.json().get("value", []):
            print(f"  {rec.get('title')} ({rec.get('subjectid')})")
