#!/usr/bin/env python3
"""
Test fetching setlists for multiple concerts to see success rate
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from setlistfm_client import SetlistFMClient

script_dir = Path(__file__).parent
project_root = script_dir.parent
db_path = project_root / "database" / "concerts.db"

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Find concerts from 2019 with well-known artists
print("Looking for concerts from 2019...")
cursor.execute('''
    SELECT
        c.id,
        c.show_number,
        c.date,
        v.canonical_name as venue,
        v.city,
        v.state,
        a.canonical_name as artist
    FROM concerts c
    JOIN venues v ON c.venue_id = v.id
    JOIN concert_artists ca ON c.id = ca.concert_id
    JOIN artists a ON ca.artist_id = a.id
    WHERE c.date >= '2019-01-01'
      AND c.date <= '2019-12-31'
      AND ca.role IN ('headliner', 'festival_performer')
    ORDER BY c.date DESC
    LIMIT 10
''')

concerts = cursor.fetchall()

print(f"\nFound {len(concerts)} concerts from 2019")
print(f"{'='*80}\n")

# Initialize API client
api_key = "DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE"
client = SetlistFMClient(api_key)

# Test each concert
found_count = 0
for idx, concert in enumerate(concerts, 1):
    concert_id, show_num, date_str, venue, city, state, artist = concert
    date = datetime.strptime(date_str, '%Y-%m-%d')

    print(f"Test {idx}/{len(concerts)}: {artist} at {venue} ({date_str})")

    # Search for setlist
    setlist_data = client.find_setlist_for_concert(
        artist_name=artist,
        date=date,
        venue_name=venue,
        city=city,
        state=state
    )

    if setlist_data:
        songs = client.extract_songs_from_setlist(setlist_data)
        if songs:
            found_count += 1
            print(f"  ✓ Found! {len(songs)} songs")
            print(f"    Opener: {songs[0]['name']}")
            print(f"    Closer: {songs[-1]['name']}")
        else:
            print(f"  ✓ Found but no songs listed")
    else:
        print(f"  ✗ Not found")

    print()

print(f"{'='*80}")
print(f"Summary: Found {found_count}/{len(concerts)} setlists ({found_count/len(concerts)*100:.1f}%)")

conn.close()
