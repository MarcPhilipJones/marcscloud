"""List all Home Assistant entities."""

from client import HomeAssistantClient


def main() -> None:
    """List all entities grouped by domain."""
    client = HomeAssistantClient.from_env()
    states = client.get_states()
    
    # Group by domain
    by_domain: dict[str, list] = {}
    for state in states:
        entity_id = state["entity_id"]
        domain = entity_id.split(".")[0]
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(state)
    
    # Print
    for domain in sorted(by_domain.keys()):
        entities = by_domain[domain]
        print(f"\n{domain.upper()} ({len(entities)})")
        print("-" * 40)
        for entity in sorted(entities, key=lambda x: x["entity_id"]):
            entity_id = entity["entity_id"]
            state = entity["state"]
            name = entity.get("attributes", {}).get("friendly_name", "")
            print(f"  {entity_id}: {state}")
            if name and name != entity_id.split(".")[1].replace("_", " ").title():
                print(f"    ({name})")


if __name__ == "__main__":
    main()
