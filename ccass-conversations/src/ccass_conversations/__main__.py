"""CLI entry point for CCaSS Conversations."""

import sys
from .client import DataverseClient


def main() -> int:
    """Main entry point for the CLI."""
    print("CCaSS Conversations - Retrieving conversations from Dataverse")
    print("=" * 60)
    
    try:
        client = DataverseClient()
        conversations = client.get_conversations()
        
        print(f"\nRetrieved {len(conversations)} conversations")
        
        for conv in conversations[:10]:  # Show first 10
            print(f"  - {conv.subject or 'No subject'} ({conv.conversation_id})")
        
        if len(conversations) > 10:
            print(f"  ... and {len(conversations) - 10} more")
        
        return 0
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
