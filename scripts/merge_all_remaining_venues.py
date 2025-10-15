#!/usr/bin/env python3
"""
Merge all remaining venues from the template into main venue_mapping.csv
"""

import csv
from pathlib import Path

def merge_remaining_venues():
    """Merge all remaining venues into the main mapping file"""

    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    main_file = project_root / "mappings" / "venue_mapping.csv"
    remaining_file = project_root / "mappings" / "all_remaining_venues.csv"

    if not remaining_file.exists():
        print("Error: all_remaining_venues.csv not found!")
        print(f"Expected at: {remaining_file}")
        return

    # Read existing mappings
    existing = []
    existing_originals = set()

    with open(main_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing.append(row)
            existing_originals.add(row['original_name'])

    # Read remaining venues
    additions = []
    skipped = []

    with open(remaining_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip if already in main file
            if row['original_name'] in existing_originals:
                continue

            # Only add if has city/state (reviewed)
            if row['city'] and row['state'] and row['venue_type']:
                # Convert to main file format
                main_row = {
                    'original_name': row['original_name'],
                    'canonical_name': row['canonical_name'],
                    'short_name': row['canonical_name'].split()[0] if ' ' in row['canonical_name'] else row['canonical_name'][:15],
                    'city': row['city'],
                    'state': row['state'],
                    'venue_type': row['venue_type'],
                    'count': row['times_visited'],
                    'needs_review': 'NO',
                    'notes': row.get('notes', 'Added from remaining venues')
                }
                additions.append(main_row)
            else:
                skipped.append(row['original_name'])

    if not additions:
        print("=" * 80)
        print("NO VENUES TO ADD")
        print("=" * 80)
        print("\nNo completed venues found in the template.")
        print("Make sure you've filled in city, state, and venue_type columns.")
        if skipped:
            print(f"\nSkipped {len(skipped)} venues missing required fields:")
            for venue in skipped[:10]:
                print(f"  - {venue}")
            if len(skipped) > 10:
                print(f"  ... and {len(skipped) - 10} more")
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
    print("VENUE MERGE COMPLETE")
    print("=" * 80)
    print(f"\n✓ Added {len(additions)} new venue mappings")

    if skipped:
        print(f"⚠ Skipped {len(skipped)} venues (missing city/state/type)")

    print(f"\nTotal venue mappings: {len(merged)}")

    # Show breakdown by state
    from collections import Counter
    state_counts = Counter(row['state'] for row in additions if row['state'])

    print("\n\nAdded venues by state:")
    for state, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {state}: {count} venues")

    print("\n\nSample of added venues:")
    for row in additions[:20]:
        print(f"  ✓ {row['original_name']:35s} → {row['city']}, {row['state']}")

    if len(additions) > 20:
        print(f"  ... and {len(additions) - 20} more")

    print("\n" + "=" * 80)
    print("NEXT STEP")
    print("=" * 80)
    print("Run the pipeline to apply these changes:")
    print("  python3 scripts/run_all.py")

if __name__ == "__main__":
    merge_remaining_venues()
