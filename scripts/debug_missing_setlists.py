#!/usr/bin/env python3
"""
Debug why specific concerts aren't being found on setlist.fm
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from setlistfm_client import SetlistFMClient

script_dir = Path(__file__).parent
project_root = script_dir.parent
db_path = project_root / "database" / "concerts.db"

# Test concerts that should exist
# Change this to test different shows
import sys
if len(sys.argv) > 1:
    test_show_numbers = [int(sys.argv[1])]
else:
    test_show_numbers = [1187]  # Default to first one

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

api_key = "DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE"
client = SetlistFMClient(api_key)

print("=" * 80)
print("DEBUGGING MISSING SETLISTS")
print("=" * 80)

for show_num in test_show_numbers:
    # Get concert details
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
        WHERE c.show_number = ?
        LIMIT 1
    ''', (show_num,))

    result = cursor.fetchone()
    if not result:
        print(f"\nShow #{show_num}: NOT FOUND IN DATABASE")
        continue

    concert_id, show_num, date_str, venue, city, state, artist = result
    date = datetime.strptime(date_str, '%Y-%m-%d')

    print(f"\n{'='*80}")
    print(f"SHOW #{show_num}")
    print(f"{'='*80}")
    print(f"Date: {date_str}")
    print(f"Artist: {artist}")
    print(f"Venue: {venue}")
    print(f"City: {city}, {state}")

    # Try 1: Full search
    print(f"\n--- Try 1: Full search (artist + date + venue + city + state) ---")
    date_api = date.strftime('%d-%m-%Y')
    print(f"Searching: artist='{artist}', date='{date_api}', venue='{venue}', city='{city}', state='{state}'")

    results = client.search_setlists(
        artist_name=artist,
        venue_name=venue,
        city_name=city,
        state=state,
        date=date_api
    )

    if results and 'setlist' in results and len(results['setlist']) > 0:
        print(f"✓ FOUND {len(results['setlist'])} result(s)")
        for i, r in enumerate(results['setlist'][:3], 1):
            print(f"  {i}. {r.get('eventDate')} - {r.get('artist', {}).get('name')} at {r.get('venue', {}).get('name')}")
    else:
        print(f"✗ No results")

    # Try 2: Without venue
    print(f"\n--- Try 2: Without venue (artist + date + city + state) ---")
    print(f"Searching: artist='{artist}', date='{date_api}', city='{city}', state='{state}'")

    results = client.search_setlists(
        artist_name=artist,
        city_name=city,
        state=state,
        date=date_api
    )

    if results and 'setlist' in results and len(results['setlist']) > 0:
        print(f"✓ FOUND {len(results['setlist'])} result(s)")
        for i, r in enumerate(results['setlist'][:3], 1):
            print(f"  {i}. {r.get('eventDate')} - {r.get('artist', {}).get('name')} at {r.get('venue', {}).get('name')}")
    else:
        print(f"✗ No results")

    # Try 3: Just artist and date
    print(f"\n--- Try 3: Just artist + date (most lenient) ---")
    print(f"Searching: artist='{artist}', date='{date_api}'")

    results = client.search_setlists(
        artist_name=artist,
        date=date_api
    )

    if results and 'setlist' in results and len(results['setlist']) > 0:
        print(f"✓ FOUND {len(results['setlist'])} result(s)")
        for i, r in enumerate(results['setlist'][:3], 1):
            print(f"  {i}. {r.get('eventDate')} - {r.get('artist', {}).get('name')} at {r.get('venue', {}).get('name')}")
    else:
        print(f"✗ No results")

    # Try 4: Strip everything after special characters in artist name
    if '(' in artist or 'w/' in artist or 'w.' in artist:
        # Clean artist name
        clean_artist = artist.split('(')[0].strip()
        clean_artist = clean_artist.split(' w/')[0].strip()
        clean_artist = clean_artist.split(' w.')[0].strip()

        print(f"\n--- Try 4: Cleaned artist name + date ---")
        print(f"Original artist: '{artist}'")
        print(f"Cleaned artist: '{clean_artist}'")
        print(f"Searching: artist='{clean_artist}', date='{date_api}'")

        results = client.search_setlists(
            artist_name=clean_artist,
            date=date_api
        )

        if results and 'setlist' in results and len(results['setlist']) > 0:
            print(f"✓ FOUND {len(results['setlist'])} result(s)")
            for i, r in enumerate(results['setlist'][:3], 1):
                print(f"  {i}. {r.get('eventDate')} - {r.get('artist', {}).get('name')} at {r.get('venue', {}).get('name')}")
        else:
            print(f"✗ No results")

conn.close()

print("\n" + "=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)
