#!/usr/bin/env python3
"""
Test the exact example from the documentation:
Kip Moore at Ridgefield Playhouse on May 9, 2019
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

# Look for Kip Moore concerts from 2019
print("Looking for Kip Moore concerts in 2019...")
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
    WHERE LOWER(a.canonical_name) LIKE '%kip moore%'
      AND c.date >= '2019-01-01'
      AND c.date <= '2019-12-31'
    ORDER BY c.date
''')

concerts = cursor.fetchall()

if concerts:
    print(f"\nFound {len(concerts)} Kip Moore concerts in 2019:")
    for concert in concerts:
        concert_id, show_num, date, venue, city, state, artist = concert
        print(f"  Show #{show_num}: {date} at {venue} ({city}, {state})")

    # Test with the Ridgefield show if it exists
    for concert in concerts:
        concert_id, show_num, date_str, venue, city, state, artist = concert
        if 'Ridgefield' in venue or 'Ridgefield' in city:
            print(f"\n{'='*80}")
            print(f"Testing Ridgefield Playhouse concert:")
            print(f"  Date: {date_str}")
            print(f"  Venue: {venue}")
            print(f"  City: {city}, {state}")
            print(f"{'='*80}\n")

            date = datetime.strptime(date_str, '%Y-%m-%d')

            # Initialize API client
            api_key = "DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE"
            client = SetlistFMClient(api_key)

            # Try exact search
            print("Searching with full details...")
            setlist_data = client.find_setlist_for_concert(
                artist_name="Kip Moore",
                date=date,
                venue_name="Ridgefield Playhouse",
                city="Ridgefield",
                state="CT"
            )

            if setlist_data:
                print("✓ Found with full search!")
                songs = client.extract_songs_from_setlist(setlist_data)
                print(f"  Songs: {len(songs)}")
                if songs:
                    print(f"  Opening: {songs[0]['name']}")
                    print(f"  Closing: {songs[-1]['name']}")
            else:
                print("✗ Not found with full search")

                # Try simpler search
                print("\nTrying simpler search (just artist and date)...")
                results = client.search_setlists(
                    artist_name="Kip Moore",
                    date=date.strftime('%d-%m-%Y')
                )

                if results and 'setlist' in results:
                    print(f"  Found {len(results['setlist'])} results")
                    for i, result in enumerate(results['setlist'][:3], 1):
                        print(f"    {i}. {result.get('eventDate')} at {result.get('venue', {}).get('name')}")
                else:
                    print("  No results")
            break
else:
    print("\nNo Kip Moore concerts found in 2019")

    # Show all Kip Moore concerts
    print("\nLooking for ANY Kip Moore concerts...")
    cursor.execute('''
        SELECT
            c.date,
            v.canonical_name as venue,
            v.city,
            v.state
        FROM concerts c
        JOIN venues v ON c.venue_id = v.id
        JOIN concert_artists ca ON c.id = ca.concert_id
        JOIN artists a ON ca.artist_id = a.id
        WHERE LOWER(a.canonical_name) LIKE '%kip moore%'
        ORDER BY c.date DESC
        LIMIT 10
    ''')

    all_concerts = cursor.fetchall()
    if all_concerts:
        print(f"Found {len(all_concerts)} Kip Moore concerts:")
        for date, venue, city, state in all_concerts:
            print(f"  {date}: {venue} ({city}, {state})")

conn.close()
