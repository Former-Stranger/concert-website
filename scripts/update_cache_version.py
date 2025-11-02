#!/usr/bin/env python3
"""
Update Service Worker cache version automatically.
This script increments the cache version number in service-worker.js,
which forces all browsers to fetch fresh JavaScript and CSS files.
"""

import re
from pathlib import Path

def update_service_worker_version(sw_path):
    """Bump the Service Worker cache version."""
    with open(sw_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find current version number in CACHE_NAME
    match = re.search(r"const CACHE_NAME = 'earplugs-memories-v(\d+)'", content)
    if not match:
        print("❌ Could not find CACHE_NAME in service-worker.js")
        return False

    current_version = int(match.group(1))
    new_version = current_version + 1

    print(f"Service Worker Cache Version:")
    print(f"  Current: v{current_version}")
    print(f"  New:     v{new_version}")

    # Update CACHE_NAME
    content = re.sub(
        r"const CACHE_NAME = 'earplugs-memories-v\d+'",
        f"const CACHE_NAME = 'earplugs-memories-v{new_version}'",
        content
    )

    # Update DATA_CACHE_NAME
    content = re.sub(
        r"const DATA_CACHE_NAME = 'earplugs-memories-data-v\d+'",
        f"const DATA_CACHE_NAME = 'earplugs-memories-data-v{new_version}'",
        content
    )

    # Update version comment
    content = re.sub(
        r"// Version: 1\.0\.\d+",
        f"// Version: 1.0.{new_version}",
        content
    )

    with open(sw_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

def main():
    print("=" * 60)
    print("Updating Service Worker Cache Version")
    print("=" * 60)

    # Find service-worker.js
    website_dir = Path(__file__).parent.parent / 'website'
    sw_path = website_dir / 'service-worker.js'

    if not sw_path.exists():
        print(f"❌ Service Worker not found at: {sw_path}")
        return 1

    if update_service_worker_version(sw_path):
        print("✓ Service Worker updated successfully")
        print("=" * 60)
        print("")
        print("The new cache version will:")
        print("  • Force browsers to fetch fresh JS/CSS files")
        print("  • Clear old cached files automatically")
        print("  • Apply changes to all users on next visit")
        return 0
    else:
        return 1

if __name__ == '__main__':
    exit(main())
