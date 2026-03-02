"""
Find and publish a knowledge article in Dataverse.
Determines the appropriate publish method (status change vs unbound action).
"""

import sys
import os

# Add mcp-dataverse-server to path
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
    
    with httpx.Client(timeout=30.0) as client:
        # Step 1: Find the knowledge article by title
        search_title = "Basic Backflushing with Contoso Coffee"
        url = f"{base_url}/api/data/{api_version}/knowledgearticles"
        params = {
            "$filter": f"contains(title, 'Basic Backflushing')",
            "$select": "knowledgearticleid,title,statecode,statuscode,isrootarticle,articlepublicnumber"
        }
        
        print(f"Searching for: {search_title}")
        resp = client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        
        articles = data.get('value', [])
        if not articles:
            print("No knowledge article found with that title.")
            return
        
        print(f"\nFound {len(articles)} article(s):")
        for art in articles:
            state_map = {0: 'Draft', 1: 'Approved', 2: 'Scheduled', 3: 'Published', 4: 'Expired', 5: 'Archived', 6: 'Discarded'}
            state = state_map.get(art['statecode'], f"Unknown ({art['statecode']})")
            print(f"  - {art['title']}")
            print(f"    ID: {art['knowledgearticleid']}")
            print(f"    State: {state} (statecode={art['statecode']}, statuscode={art['statuscode']})")
            print(f"    Article Number: {art.get('articlepublicnumber', 'N/A')}")
        
        # Take the first matching article
        article = articles[0]
        article_id = article['knowledgearticleid']
        current_state = article['statecode']
        
        if current_state == 3:
            print(f"\nArticle is already Published. No action needed.")
            return
        
        # Step 2: Determine publish method
        # Knowledge Articles use the PublishKnowledgeArticle action (unbound action)
        # Or we can update statecode/statuscode directly
        # The proper way is to use the Publish action
        
        print(f"\n--- Publishing Article ---")
        print("Method: Using PublishKnowledgeArticle action (unbound)")
        
        # PublishKnowledgeArticle action
        # POST /api/data/v9.2/PublishKnowledgeArticle
        # Body: { "EntityId": "<article_id>" }
        
        publish_url = f"{base_url}/api/data/{api_version}/PublishKnowledgeArticle"
        publish_body = {
            "EntityId": article_id
        }
        
        print(f"Calling: POST {publish_url}")
        print(f"Body: {publish_body}")
        
        try:
            resp = client.post(publish_url, headers=headers, json=publish_body)
            resp.raise_for_status()
            print(f"SUCCESS: Article published via PublishKnowledgeArticle action")
        except httpx.HTTPStatusError as e:
            print(f"PublishKnowledgeArticle action failed: {e.response.status_code}")
            print(f"Response: {e.response.text}")
            
            # Fallback: Try direct status update
            print("\nFallback: Trying direct statecode/statuscode update...")
            # statecode=3 (Published), statuscode=7 (Published)
            update_url = f"{base_url}/api/data/{api_version}/knowledgearticles({article_id})"
            update_body = {
                "statecode": 3,
                "statuscode": 7
            }
            
            try:
                resp = client.patch(update_url, headers=headers, json=update_body)
                resp.raise_for_status()
                print(f"SUCCESS: Article published via direct status update")
            except httpx.HTTPStatusError as e2:
                print(f"Direct update also failed: {e2.response.status_code}")
                print(f"Response: {e2.response.text}")
                return
        
        # Step 3: Verify the publish
        print("\n--- Verifying ---")
        resp = client.get(f"{base_url}/api/data/{api_version}/knowledgearticles({article_id})", 
                         headers=headers,
                         params={"$select": "title,statecode,statuscode"})
        resp.raise_for_status()
        updated = resp.json()
        state_map = {0: 'Draft', 1: 'Approved', 2: 'Scheduled', 3: 'Published', 4: 'Expired', 5: 'Archived', 6: 'Discarded'}
        new_state = state_map.get(updated['statecode'], f"Unknown ({updated['statecode']})")
        print(f"Article: {updated['title']}")
        print(f"New State: {new_state} (statecode={updated['statecode']}, statuscode={updated['statuscode']})")


if __name__ == "__main__":
    main()
