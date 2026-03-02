#!/usr/bin/env python
"""
Get details of a specific topic from a Copilot Studio agent.
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from powerplatform.client import DataverseClient

# VSCODE_Experimentation bot ID
BOT_ID = "23ecd735-0f01-f111-8406-000d3ab5d629"
TOPIC_NAME = "Conversation Start"


def main():
    with DataverseClient() as client:
        # Get all components and filter in Python
        url = f"botcomponents?$filter=_parentbotid_value eq {BOT_ID}&$select=name,componenttype,description,content,data"
        components = client._request("GET", url)
        
        for c in components.get("value", []):
            if TOPIC_NAME.lower() in c.get("name", "").lower():
                print("=" * 70)
                print(f"Topic: {c.get('name')}")
                print("=" * 70)
                print(f"Description: {c.get('description', 'N/A')}")
                print(f"Component Type: {c.get('componenttype')}")
                print()
                
                content = c.get("content")
                if content:
                    try:
                        parsed = json.loads(content)
                        print("Content Structure:")
                        print("-" * 50)
                        
                        # Extract key information
                        if "$kind" in parsed:
                            print(f"Kind: {parsed['$kind']}")
                        
                        if "triggers" in parsed:
                            print(f"\nTriggers ({len(parsed['triggers'])}):")
                            for t in parsed["triggers"]:
                                print(f"  - {t.get('$kind', 'Unknown')}: {t.get('$id', '')}")
                                if "eventName" in t:
                                    print(f"    Event: {t['eventName']}")
                        
                        if "actions" in parsed:
                            print(f"\nActions ({len(parsed['actions'])}):")
                            for a in parsed["actions"]:
                                kind = a.get("$kind", "Unknown")
                                print(f"  - {kind}")
                                if "activity" in a:
                                    print(f"    Activity: {a['activity'][:100]}...")
                        
                        # Show raw JSON (truncated)
                        print("\n" + "-" * 50)
                        print("Raw JSON (first 2000 chars):")
                        print(json.dumps(parsed, indent=2)[:2000])
                        
                    except json.JSONDecodeError:
                        print("Content (raw):", content[:2000])
                
                data = c.get("data")
                if data:
                    print("\n" + "-" * 50)
                    print("Data field:", data[:500] if len(data) > 500 else data)
                
                break


if __name__ == "__main__":
    main()
