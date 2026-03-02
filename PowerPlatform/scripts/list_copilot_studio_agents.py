#!/usr/bin/env python
"""
List Copilot Studio agents (bots) from Dataverse.

Copilot Studio agents are stored in the 'bot' entity in Dataverse.
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from powerplatform.client import DataverseClient


def main():
    print("=" * 80)
    print("COPILOT STUDIO AGENTS")
    print("=" * 80)
    
    with DataverseClient() as client:
        # Query the bot entity - this stores Copilot Studio agents
        # Key fields: name, botid, statecode, statuscode, createdon, modifiedon
        try:
            # First, get the list of bots with key fields
            bots = client._request(
                "GET",
                "bots",
                params={
                    "$select": "name,botid,statecode,statuscode,createdon,modifiedon,schemaname,accesscontrolpolicy,language,publishedon",
                    "$orderby": "modifiedon desc"
                }
            )
            
            bot_list = bots.get("value", [])
            
            if not bot_list:
                print("\nNo Copilot Studio agents found in this environment.")
                print("\nThis could mean:")
                print("  - No agents have been created yet")
                print("  - The app registration doesn't have permission to read bots")
                print("  - The bot entity is not available in this environment")
                return
            
            print(f"\nFound {len(bot_list)} agent(s):\n")
            print("-" * 80)
            
            for i, bot in enumerate(bot_list, 1):
                name = bot.get("name", "Unnamed")
                bot_id = bot.get("botid", "N/A")
                schema_name = bot.get("schemaname", "N/A")
                language = bot.get("language", "N/A")
                
                # State: 0=Active, 1=Inactive
                state = bot.get("statecode", 0)
                state_label = "Active" if state == 0 else "Inactive"
                
                # Status codes can vary
                status = bot.get("statuscode", 1)
                
                created = bot.get("createdon", "")[:10] if bot.get("createdon") else "N/A"
                modified = bot.get("modifiedon", "")[:10] if bot.get("modifiedon") else "N/A"
                published = bot.get("publishedon", "")[:10] if bot.get("publishedon") else "Never"
                
                # Access control: 0=Anonymous, 1=Authenticated
                access = bot.get("accesscontrolpolicy", 0)
                access_label = "Authenticated" if access == 1 else "Anonymous"
                
                print(f"{i}. {name}")
                print(f"   ID:         {bot_id}")
                print(f"   Schema:     {schema_name}")
                print(f"   Language:   {language}")
                print(f"   Status:     {state_label} (statecode={state}, statuscode={status})")
                print(f"   Access:     {access_label}")
                print(f"   Created:    {created}")
                print(f"   Modified:   {modified}")
                print(f"   Published:  {published}")
                print()
            
            print("-" * 80)
            print(f"\nTotal: {len(bot_list)} agent(s)")
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ Error querying bots: {error_msg}")
            
            if "404" in error_msg or "Not Found" in error_msg:
                print("\nThe 'bots' entity was not found. This could mean:")
                print("  - Copilot Studio is not provisioned in this environment")
                print("  - Try querying 'chatbots' entity instead (older API)")
            elif "403" in error_msg or "Forbidden" in error_msg:
                print("\nAccess denied. The app registration may need:")
                print("  - 'System Administrator' or 'Bot Author' security role")
                print("  - Permission to read the bot entity")
            else:
                print("\nTroubleshooting tips:")
                print("  - Check your DATAVERSE_* environment variables")
                print("  - Verify the app registration has proper permissions")


if __name__ == "__main__":
    main()
