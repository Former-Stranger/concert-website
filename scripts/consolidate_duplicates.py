#!/usr/bin/env python3
"""
Consolidate duplicate canonical venue names
"""

import csv
from pathlib import Path
from collections import defaultdict

def consolidate_duplicates():
    """Consolidate venues that have different canonical names but are the same place"""

    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    venue_file = project_root / "mappings" / "venue_mapping.csv"

    # Define consolidation mappings
    # Format: {old_canonical_name: new_canonical_name}
    consolidations = {
        "Daryls House": "Daryl's House",  # Both spellings → apostrophe version
        "Met Life Stadium": "MetLife Stadium",  # Both spellings → one word version
    }

    # Read all venues
    venues = []
    with open(venue_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Apply consolidation
            if row['canonical_name'] in consolidations:
                old_name = row['canonical_name']
                new_name = consolidations[old_name]
                print(f"  Consolidating: '{old_name}' → '{new_name}'")
                print(f"    Original: '{row['original_name']}'")
                row['canonical_name'] = new_name
                # Update short_name if it matches the old canonical
                if row['short_name'] == old_name.split()[0]:
                    row['short_name'] = new_name.split()[0]
            venues.append(row)

    # Write back
    with open(venue_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['original_name', 'canonical_name', 'short_name', 'city', 'state', 'venue_type', 'count', 'needs_review', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(venues)

    print("\n✓ Consolidation complete!")

    # Show summary
    venues_by_canonical = defaultdict(list)
    for row in venues:
        venues_by_canonical[row['canonical_name']].append(row)

    print("\nUpdated venues with multiple variations:")
    for canonical in sorted(consolidations.values()):
        if canonical in venues_by_canonical:
            rows = venues_by_canonical[canonical]
            total = sum(int(r['count']) for r in rows)
            print(f"\n{canonical}: {total} total visits")
            for row in rows:
                print(f"  - '{row['original_name']}' ({row['count']} visits)")

if __name__ == "__main__":
    print("=" * 80)
    print("CONSOLIDATING DUPLICATE CANONICAL VENUE NAMES")
    print("=" * 80)
    print()
    consolidate_duplicates()
