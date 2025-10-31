#!/usr/bin/env python3
"""
Update cache-busting version numbers in all HTML files.
Generates a timestamp-based version and updates all ?v= query parameters.
"""

import re
import time
import glob
from pathlib import Path

def update_version_in_file(filepath, new_version):
    """Update all ?v= version strings in a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace all instances of ?v=NNNNNNNNNN with new version
    # Pattern matches ?v= followed by digits
    updated_content = re.sub(r'\?v=\d+', f'?v={new_version}', content)

    # Only write if changes were made
    if updated_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        return True
    return False

def main():
    # Generate new version from current timestamp
    new_version = int(time.time())

    print(f"Updating cache version to: {new_version}")
    print("=" * 60)

    # Find all HTML files in website directory
    website_dir = Path(__file__).parent.parent / 'website'
    html_files = list(website_dir.glob('*.html'))

    updated_count = 0
    for html_file in sorted(html_files):
        if update_version_in_file(html_file, new_version):
            print(f"✓ Updated: {html_file.name}")
            updated_count += 1
        else:
            print(f"- No changes: {html_file.name}")

    print("=" * 60)
    print(f"Updated {updated_count} file(s) to version {new_version}")

    if updated_count > 0:
        print("\nNext steps:")
        print("1. Review changes: git diff website/*.html")
        print("2. Deploy: firebase deploy --only hosting")

if __name__ == '__main__':
    main()
