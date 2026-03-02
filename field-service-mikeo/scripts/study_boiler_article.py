"""Study the Boiler article format."""
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
    # Find the Boiler article
    url = f"{base}/api/data/{ver}/knowledgearticles?$filter=contains(title,'Boiler')&$select=title,description,content,keywords,statecode,statuscode,articlepublicnumber,_subjectid_value"
    r = c.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        if data.get("value"):
            article = data["value"][0]
            print("=" * 60)
            print("BOILER ARTICLE FORMAT ANALYSIS")
            print("=" * 60)
            print(f"\nTitle: {article.get('title')}")
            print(f"\nDescription: {article.get('description')}")
            print(f"\nKeywords: {article.get('keywords')}")
            print(f"\nArticle Number: {article.get('articlepublicnumber')}")
            print(f"\nState Code: {article.get('statecode')}")
            print(f"\nStatus Code: {article.get('statuscode')}")
            print(f"\nSubject ID: {article.get('_subjectid_value')}")
            print(f"\n{'=' * 60}")
            print("CONTENT (HTML):")
            print("=" * 60)
            print(article.get("content"))
        else:
            print("Article not found")
    else:
        print(f"Error: {r.status_code}")
        print(r.text[:500])
