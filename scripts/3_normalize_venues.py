#!/usr/bin/env python3
"""
Step 3: Normalize venue names using the mapping file
"""

import json
import csv
from pathlib import Path
from collections import defaultdict

def load_venue_mapping(mapping_path):
    """Load venue mappings from CSV"""
    mapping = {}

    with open(mapping_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            original = row['original_name']
            venue_data = {
                'canonical_name': row['canonical_name'],
                'short_name': row['short_name'],
                'city': row['city'],
                'state': row['state'],
                'venue_type': row['venue_type']
            }
            mapping[original] = venue_data

    return mapping

def normalize_venues(input_path, mapping_path, output_path):
    """Normalize all venue names using the mapping"""

    print("=" * 80)
    print("STEP 3: NORMALIZING VENUE NAMES")
    print("=" * 80)

    # Load data
    with open(input_path, 'r', encoding='utf-8') as f:
        records = json.load(f)

    # Load mapping
    venue_mapping = load_venue_mapping(mapping_path)
    print(f"\nLoaded {len(venue_mapping)} venue mappings")

    # Track unmapped venues
    unmapped = defaultdict(int)
    mapped_count = 0

    # Process each record
    for record in records:
        venue_original = record.get('VENUE')

        if not venue_original or (isinstance(venue_original, float) and pd.isna(venue_original)):
            record['venue_canonical'] = None
            record['venue_city'] = None
            record['venue_state'] = None
            record['venue_type'] = None
            continue

        venue_original = str(venue_original)

        # Map venue
        if venue_original in venue_mapping:
            venue_data = venue_mapping[venue_original]
            record['venue_canonical'] = venue_data['canonical_name']
            record['venue_short'] = venue_data['short_name']
            record['venue_city'] = venue_data['city']
            record['venue_state'] = venue_data['state']
            record['venue_type'] = venue_data['venue_type']
            mapped_count += 1
        else:
            # Try trimmed version
            trimmed = venue_original.strip()
            if trimmed in venue_mapping:
                venue_data = venue_mapping[trimmed]
                record['venue_canonical'] = venue_data['canonical_name']
                record['venue_short'] = venue_data['short_name']
                record['venue_city'] = venue_data['city']
                record['venue_state'] = venue_data['state']
                record['venue_type'] = venue_data['venue_type']
                mapped_count += 1
            else:
                # Unmapped - keep original
                record['venue_canonical'] = trimmed
                record['venue_short'] = ''
                record['venue_city'] = ''
                record['venue_state'] = ''
                record['venue_type'] = ''
                unmapped[trimmed] += 1

    # Save normalized data
    output_file = Path(output_path)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, default=str)

    print(f"\nNormalization complete:")
    print(f"  Mapped venues: {mapped_count}")
    print(f"  Unmapped venue variations: {len(unmapped)}")

    if unmapped:
        print(f"\nTop 20 unmapped venues:")
        for venue, count in sorted(unmapped.items(), key=lambda x: x[1], reverse=True)[:20]:
            print(f"  {count:3d}x - {venue}")

        print("\nYou can add these to venue_mapping.csv for complete coverage")

    print(f"\nSaved normalized data to: {output_file}")

    return records

if __name__ == "__main__":
    import pandas as pd
    from pathlib import Path

    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    input_path = project_root / "data" / "normalized_artists.json"
    mapping_path = project_root / "mappings" / "venue_mapping.csv"
    output_path = project_root / "data" / "normalized_venues.json"

    records = normalize_venues(input_path, mapping_path, output_path)
    print("\n✓ Step 3 complete!")
