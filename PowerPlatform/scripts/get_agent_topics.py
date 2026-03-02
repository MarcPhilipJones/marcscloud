#!/usr/bin/env python
"""
Get topics and components for a Copilot Studio agent.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from powerplatform.client import DataverseClient

# VSCODE_Experimentation bot ID
BOT_ID = "23ecd735-0f01-f111-8406-000d3ab5d629"


def main():
    with DataverseClient() as client:
        # Get bot components (topics, dialogs, etc.)
        url = f"botcomponents?$filter=_parentbotid_value eq {BOT_ID}&$select=name,componenttype,botcomponentid,description&$orderby=name"
        components = client._request("GET", url)
        
        comp_list = components.get("value", [])
        
        if not comp_list:
            print("No topics/components found for this agent.")
            return
            
        print(f"VSCODE_Experimentation - Components ({len(comp_list)} total)")
        print("=" * 70)
        
        type_names = {
            0: "Topic",
            1: "Skill", 
            2: "Bot variable",
            3: "Dialog",
            4: "Trigger",
            5: "Language generation",
            6: "Language understanding",
            7: "Entity"
        }
        
        by_type = {}
        for c in comp_list:
            ctype = c.get("componenttype", 0)
            if ctype not in by_type:
                by_type[ctype] = []
            by_type[ctype].append(c)
        
        for ctype, comps in sorted(by_type.items()):
            type_name = type_names.get(ctype, f"Type {ctype}")
            print(f"\n{type_name}s ({len(comps)}):")
            print("-" * 50)
            for c in comps:
                name = c.get("name", "Unnamed")
                desc = c.get("description", "")
                if desc:
                    print(f"  - {name}: {desc[:60]}")
                else:
                    print(f"  - {name}")


if __name__ == "__main__":
    main()
