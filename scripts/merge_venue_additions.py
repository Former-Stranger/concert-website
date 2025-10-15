#!/usr/bin/env python3
"""
Merge venue additions from template into main venue_mapping.csv
"""

import csv
from pathlib import Path

def merge_venue_additions():
    """Merge the additions template into the main mapping file"""

    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    main_file = project_root / "mappings" / "venue_mapping.csv"
    additions_file = project_root / "mappings" / "venue_additions_template.csv"

    if not additions_file.exists():
        print("Error: venue_additions_template.csv not found!")
        print(f"Expected at: {additions_file}")
        return

    # Read existing mappings
    existing = []
    existing_originals = set()

    with open(main_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing.append(row)
            existing_originals.add(row['original_name'])

    # Read additions
    additions = []
    with open(additions_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip if already in main file
            if row['original_name'] not in existing_originals:
                # Only add if has city/state (reviewed)
                if row['city'] and row['state']:
                    additions.append(row)

    if not additions:
        print("No new venues to add!")
        print("Make sure you've filled in city/state for venues in the template.")
        return

    # Merge
    merged = existing + additions

    # Write back
    with open(main_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['original_name', 'canonical_name', 'short_name', 'city', 'state', 'venue_type', 'count', 'needs_review', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged)

    print("=" * 80)
    print("VENUE ADDITIONS MERGED")
    print("=" * 80)
    print(f"\n✓ Added {len(additions)} new venue mappings")
    print("\nAdded venues:")

    for row in additions:
        print(f"  ✓ {row['original_name']:30s} → {row['city']}, {row['state']}")

    print(f"\nTotal venue mappings: {len(merged)}")
    print("\nNext step: Run the pipeline to apply changes")
    print("  python3 scripts/run_all.py")

if __name__ == "__main__":
    merge_venue_additions()
