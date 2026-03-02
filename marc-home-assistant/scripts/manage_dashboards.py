#!/usr/bin/env python3
"""
Dashboard Management CLI for Home Assistant.

This script provides a clean interface for creating, updating, and managing
Lovelace dashboards via the Home Assistant REST API.

Usage:
    python manage_dashboards.py list                    # List all dashboards
    python manage_dashboards.py get <url_path>          # Get dashboard config
    python manage_dashboards.py create <url_path>       # Create new dashboard
    python manage_dashboards.py update <url_path> <file> # Update from JSON file
    python manage_dashboards.py temperatures            # Create temperatures dashboard
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from marc_home_assistant.client import HomeAssistantClient


def list_dashboards(client: HomeAssistantClient) -> None:
    """List all dashboards."""
    dashboards = client.get_dashboards()
    print(f"\n📊 Found {len(dashboards)} dashboard(s):\n")
    for db in dashboards:
        icon = db.get("icon", "mdi:view-dashboard")
        title = db.get("title", "Untitled")
        url = db.get("url_path", "lovelace")
        mode = db.get("mode", "storage")
        sidebar = "✅" if db.get("show_in_sidebar") else "❌"
        print(f"  {icon} {title}")
        print(f"     URL: /{url}")
        print(f"     Mode: {mode}, Sidebar: {sidebar}")
        print()


def get_dashboard(client: HomeAssistantClient, url_path: str) -> None:
    """Get and display a dashboard configuration."""
    try:
        config = client.get_dashboard_config(url_path)
        print(f"\n📋 Dashboard: {url_path}\n")
        print(json.dumps(config, indent=2))
    except Exception as e:
        print(f"❌ Error getting dashboard: {e}")
        sys.exit(1)


def create_dashboard(
    client: HomeAssistantClient,
    url_path: str,
    title: str,
    icon: str = "mdi:view-dashboard",
) -> None:
    """Create a new empty dashboard."""
    try:
        result = client.create_dashboard(
            url_path=url_path,
            title=title,
            icon=icon,
            show_in_sidebar=True,
        )
        print(f"✅ Dashboard created: {title} (/{url_path})")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Error creating dashboard: {e}")
        sys.exit(1)


def update_dashboard_from_file(
    client: HomeAssistantClient,
    url_path: str,
    config_file: Path,
) -> None:
    """Update a dashboard from a JSON config file."""
    try:
        with open(config_file) as f:
            config = json.load(f)
        
        # If the file has the full storage format, extract just the config
        if "data" in config and "config" in config["data"]:
            config = config["data"]["config"]
        
        client.update_dashboard_config(config, url_path)
        print(f"✅ Dashboard '{url_path}' updated from {config_file}")
    except FileNotFoundError:
        print(f"❌ Config file not found: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error updating dashboard: {e}")
        sys.exit(1)


def create_temperatures_dashboard(client: HomeAssistantClient) -> None:
    """Create the temperatures dashboard with Tado TRV sensors."""
    url_path = "dashboard-temperatures"
    
    # Define the sensors
    sensors = [
        {
            "entity_id": "sensor.smart_radiator_thermostat_x_temperature",
            "name": "Kitchen",
            "icon": "mdi:stove",
        },
        {
            "entity_id": "sensor.smart_radiator_thermostat_x_temperature_2",
            "name": "Living Room",
            "icon": "mdi:sofa",
        },
        {
            "entity_id": "sensor.smart_radiator_thermostat_x_temperature_3",
            "name": "Marcs Bedroom",
            "icon": "mdi:bed",
        },
    ]
    
    # Build the cards
    cards = []
    for sensor in sensors:
        card = client.create_mini_graph_card(
            entity_id=sensor["entity_id"],
            name=sensor["name"],
            icon=sensor["icon"],
            hours_to_show=24,
            points_per_hour=4,
        )
        cards.append(card)
    
    # Build the dashboard config
    config = {
        "title": "Temperatures",
        "views": [
            {
                "title": "All Rooms",
                "path": "all-rooms",
                "icon": "mdi:thermometer",
                "cards": cards,
            }
        ],
    }
    
    # Check if dashboard exists
    dashboards = client.get_dashboards()
    existing = [d for d in dashboards if d.get("url_path") == url_path]
    
    if not existing:
        # Create the dashboard first
        print(f"📝 Creating dashboard: Temperatures")
        client.create_dashboard(
            url_path=url_path,
            title="Temperatures",
            icon="mdi:thermometer",
            show_in_sidebar=True,
        )
    
    # Update the configuration
    print(f"📝 Updating dashboard configuration...")
    client.update_dashboard_config(config, url_path)
    
    print(f"✅ Temperatures dashboard ready at /{url_path}")
    print(f"   Cards: {', '.join(s['name'] for s in sensors)}")


def validate_json_file(file_path: Path) -> bool:
    """Validate a JSON file before uploading."""
    try:
        with open(file_path) as f:
            content = f.read()
        
        # Check for BOM
        if content.startswith('\ufeff'):
            print("⚠️  Warning: File contains UTF-8 BOM - removing...")
            content = content[1:]
        
        # Try to parse
        data = json.loads(content)
        
        # Check for required structure
        if "views" not in data and "data" not in data:
            print("⚠️  Warning: Config missing 'views' key")
        
        print("✅ JSON validation passed")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Manage Home Assistant Lovelace dashboards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_dashboards.py list
  python manage_dashboards.py get dashboard-temperatures
  python manage_dashboards.py create my-dashboard "My Dashboard" --icon mdi:home
  python manage_dashboards.py update dashboard-temperatures config.json
  python manage_dashboards.py temperatures
  python manage_dashboards.py validate config.json
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # list command
    subparsers.add_parser("list", help="List all dashboards")
    
    # get command
    get_parser = subparsers.add_parser("get", help="Get dashboard configuration")
    get_parser.add_argument("url_path", help="Dashboard URL path")
    
    # create command
    create_parser = subparsers.add_parser("create", help="Create a new dashboard")
    create_parser.add_argument("url_path", help="Dashboard URL path")
    create_parser.add_argument("title", help="Dashboard title")
    create_parser.add_argument("--icon", default="mdi:view-dashboard", help="MDI icon")
    
    # update command
    update_parser = subparsers.add_parser("update", help="Update dashboard from JSON file")
    update_parser.add_argument("url_path", help="Dashboard URL path")
    update_parser.add_argument("config_file", type=Path, help="Path to JSON config file")
    
    # temperatures command (shortcut for the specific use case)
    subparsers.add_parser("temperatures", help="Create/update the temperatures dashboard")
    
    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a JSON config file")
    validate_parser.add_argument("config_file", type=Path, help="Path to JSON config file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Validate command doesn't need the client
    if args.command == "validate":
        success = validate_json_file(args.config_file)
        sys.exit(0 if success else 1)
    
    # All other commands need the client
    try:
        client = HomeAssistantClient()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nMake sure .env file exists with HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN")
        sys.exit(1)
    
    with client:
        # Check connection
        if not client.check_api():
            print("❌ Cannot connect to Home Assistant API")
            sys.exit(1)
        
        if args.command == "list":
            list_dashboards(client)
        elif args.command == "get":
            get_dashboard(client, args.url_path)
        elif args.command == "create":
            create_dashboard(client, args.url_path, args.title, args.icon)
        elif args.command == "update":
            update_dashboard_from_file(client, args.url_path, args.config_file)
        elif args.command == "temperatures":
            create_temperatures_dashboard(client)


if __name__ == "__main__":
    main()
