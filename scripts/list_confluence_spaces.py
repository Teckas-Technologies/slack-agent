#!/usr/bin/env python3
"""
List all accessible Confluence spaces

This script helps you discover all Confluence spaces that your API credentials can access.
Use this to verify your setup or to find space keys for the CONFLUENCE_SPACES config.

Usage:
    python scripts/list_confluence_spaces.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.confluence_handler import ConfluenceHandler


def main():
    """List all accessible Confluence spaces"""

    print("=" * 80)
    print("CONFLUENCE SPACES DISCOVERY")
    print("=" * 80)
    print()

    try:
        # Initialize Confluence handler
        print("Connecting to Confluence...")
        handler = ConfluenceHandler()

        # Validate connection
        validation = handler.validate_connection()
        print(f"Connection Status: {validation['status']}")
        print(f"Message: {validation['message']}")
        print()

        if validation['status'] != 'connected':
            print("❌ Cannot connect to Confluence. Please check your credentials.")
            return 1

        # Get all spaces
        print("Fetching all accessible spaces...")
        spaces = handler._get_spaces()

        if not spaces:
            print("⚠️  No spaces found. Check your API credentials and permissions.")
            return 1

        print(f"✅ Found {len(spaces)} accessible spaces\n")
        print("=" * 80)

        # Display spaces in a formatted table
        print(f"{'KEY':<15} {'NAME':<40} {'TYPE':<10}")
        print("-" * 80)

        for space in spaces:
            key = space.get('key', 'N/A')
            name = space.get('name', 'N/A')
            space_type = space.get('type', 'N/A')

            # Truncate name if too long
            if len(name) > 37:
                name = name[:37] + "..."

            print(f"{key:<15} {name:<40} {space_type:<10}")

        print("=" * 80)
        print()

        # Generate environment variable suggestion
        print("💡 To index ALL spaces, leave CONFLUENCE_SPACES empty in your .env.backup file:")
        print("   CONFLUENCE_SPACES=")
        print()
        print("💡 To index SPECIFIC spaces, set CONFLUENCE_SPACES in your .env.backup file:")
        space_keys = ','.join([space['key'] for space in spaces[:5]])
        if len(spaces) > 5:
            print(f"   CONFLUENCE_SPACES={space_keys},...")
        else:
            print(f"   CONFLUENCE_SPACES={space_keys}")
        print()

        # Get document count for each space
        print("Fetching document counts (this may take a moment)...")
        print()
        print(f"{'KEY':<15} {'DOCUMENTS':<15} {'NAME':<40}")
        print("-" * 80)

        total_docs = 0
        for space in spaces:
            key = space.get('key', 'N/A')
            name = space.get('name', 'N/A')

            # Get documents for this space
            docs = handler._get_space_documents(key)
            doc_count = len(docs)
            total_docs += doc_count

            # Truncate name if too long
            if len(name) > 37:
                name = name[:37] + "..."

            print(f"{key:<15} {doc_count:<15} {name:<40}")

        print("=" * 80)
        print(f"Total documents across all spaces: {total_docs}")
        print()

        return 0

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
