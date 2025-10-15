#!/usr/bin/env python3
"""
Step 2: Normalize artist names using the mapping file
Enhanced to parse festivals and multi-artist shows
"""

import json
import csv
import re
from pathlib import Path
from collections import defaultdict
import sys

# Import festival parser
sys.path.insert(0, str(Path(__file__).parent))
from parse_festivals import FestivalParser

def load_artist_mapping(mapping_path):
    """Load artist name mappings from CSV"""
    mapping = {}

    with open(mapping_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            original = row['original_name']
            canonical = row['canonical_name']
            mapping[original] = canonical

    return mapping

def parse_artist_entry(artist_string, festival_parser):
    """
    Parse artist entry to handle:
    1. Openers (w/ notation)
    2. Festivals and multi-artist shows

    Returns:
        (festival_name, [(artist, role), ...])
    """
    if not artist_string:
        return None, []

    artist_string = str(artist_string)

    # Check for "w/" pattern first (opener notation)
    if ' w/' in artist_string or ' w/ ' in artist_string:
        parts = re.split(r'\s+w/\s*', artist_string, maxsplit=1)
        if len(parts) == 2:
            headliner = parts[0].strip()
            opener = parts[1].strip()
            return None, [(headliner, 'headliner'), (opener, 'opener')]

    # Check for festival/multi-artist shows
    festival_name, artists = festival_parser.parse_artist_entry(artist_string)

    if festival_name:
        # Multi-artist show or festival
        return festival_name, [(artist, 'festival_performer') for artist in artists]
    elif artists:
        # Single artist
        return None, [(artists[0], 'headliner')]
    else:
        return None, []

def normalize_artists(raw_data_path, mapping_path, output_path):
    """Normalize all artist names using the mapping"""

    print("=" * 80)
    print("STEP 2: NORMALIZING ARTIST NAMES")
    print("=" * 80)

    # Load raw data
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        records = json.load(f)

    # Load mapping
    artist_mapping = load_artist_mapping(mapping_path)
    print(f"\nLoaded {len(artist_mapping)} artist mappings")

    # Initialize festival parser
    festival_parser = FestivalParser()

    # Track statistics
    unmapped = defaultdict(int)
    mapped_count = 0
    opener_count = 0
    festival_count = 0
    multi_artist_count = 0

    # Process each record
    for record in records:
        artist_entry = record.get('ARTISTS')

        if not artist_entry:
            record['festival_name'] = None
            record['artists'] = []
            continue

        # Parse the artist entry
        festival_name, artists_with_roles = parse_artist_entry(artist_entry, festival_parser)

        # Store festival name if it exists
        record['festival_name'] = festival_name
        if festival_name:
            festival_count += 1

        # Process each artist
        normalized_artists = []
        for artist_name, role in artists_with_roles:
            # Apply artist mapping if available
            if artist_name in artist_mapping:
                canonical_name = artist_mapping[artist_name]
                mapped_count += 1
            else:
                canonical_name = artist_name
                unmapped[artist_name] += 1

            normalized_artists.append({
                'original': artist_name,
                'canonical': canonical_name,
                'role': role
            })

            if role == 'opener':
                opener_count += 1

        record['artists'] = normalized_artists

        if len(normalized_artists) > 1:
            multi_artist_count += 1

    # Save normalized data
    output_file = Path(output_path)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, default=str)

    print(f"\nNormalization complete:")
    print(f"  Total artist entries processed: {mapped_count + len(unmapped)}")
    print(f"  Mapped to canonical names: {mapped_count}")
    print(f"  Concerts with openers: {opener_count}")
    print(f"  Festivals/multi-artist shows: {festival_count}")
    print(f"  Total multi-artist concerts: {multi_artist_count}")
    print(f"  Unmapped artist variations: {len(unmapped)}")

    if unmapped:
        print(f"\nTop 20 unmapped artists:")
        for artist, count in sorted(unmapped.items(), key=lambda x: x[1], reverse=True)[:20]:
            print(f"  {count:3d}x - {artist}")

    print(f"\nSaved normalized data to: {output_file}")

    return records

if __name__ == "__main__":
    from pathlib import Path

    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    raw_data_path = project_root / "data" / "raw_concerts.json"
    mapping_path = project_root / "mappings" / "artist_mapping.csv"
    output_path = project_root / "data" / "normalized_artists.json"

    records = normalize_artists(raw_data_path, mapping_path, output_path)
    print("\n✓ Step 2 complete!")
