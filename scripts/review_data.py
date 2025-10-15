#!/usr/bin/env python3
"""
Interactive data review tool
Shows before/after comparisons and flags potential issues
"""

import sqlite3
import json
from pathlib import Path
from collections import defaultdict

def connect_db():
    """Connect to the database"""
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / "database" / "concerts.db"
    return sqlite3.connect(db_path)

def load_raw_data():
    """Load raw data for comparison"""
    script_dir = Path(__file__).parent
    raw_path = script_dir.parent / "data" / "raw_concerts.json"
    with open(raw_path, 'r') as f:
        return json.load(f)

def review_artist_mappings():
    """Show how artist names were standardized"""
    print("=" * 80)
    print("ARTIST NAME STANDARDIZATION REVIEW")
    print("=" * 80)

    conn = connect_db()
    cursor = conn.cursor()

    # Get all artists with their aliases
    cursor.execute('''
        SELECT a.canonical_name, GROUP_CONCAT(aa.alias, ' | ') as aliases
        FROM artists a
        LEFT JOIN artist_aliases aa ON a.id = aa.artist_id
        GROUP BY a.id
        HAVING aliases IS NOT NULL
        ORDER BY a.canonical_name
    ''')

    results = cursor.fetchall()

    if results:
        print(f"\nFound {len(results)} artists with alternate spellings:\n")
        for canonical, aliases in results:
            print(f"✓ {canonical}")
            for alias in aliases.split(' | '):
                print(f"  ← {alias}")
            print()
    else:
        print("\nNo artist variations found in database.")

    conn.close()
    return results

def review_venue_mappings():
    """Show how venue names were standardized"""
    print("=" * 80)
    print("VENUE NAME STANDARDIZATION REVIEW")
    print("=" * 80)

    raw_data = load_raw_data()
    conn = connect_db()
    cursor = conn.cursor()

    # Get venue mappings from raw data
    venue_variations = defaultdict(set)

    for record in raw_data:
        venue_original = record.get('VENUE')
        venue_canonical = record.get('venue_canonical')

        if venue_original and venue_canonical:
            venue_variations[venue_canonical].add(str(venue_original))

    # Get venue details from database
    cursor.execute('''
        SELECT canonical_name, short_name, city, state, venue_type
        FROM venues
        ORDER BY canonical_name
    ''')

    venue_details = {row[0]: row[1:] for row in cursor.fetchall()}

    # Show venues with variations
    variations_found = []
    for canonical, originals in sorted(venue_variations.items()):
        if len(originals) > 1 or (len(originals) == 1 and list(originals)[0] != canonical):
            variations_found.append((canonical, originals))

    if variations_found:
        print(f"\nFound {len(variations_found)} venues with alternate names:\n")
        for canonical, originals in variations_found[:20]:  # Show first 20
            details = venue_details.get(canonical)
            if details:
                short, city, state, vtype = details
                location = f"{city}, {state}" if city and state else ""
                print(f"✓ {canonical}")
                if location:
                    print(f"  Location: {location}")
                if vtype:
                    print(f"  Type: {vtype}")
                print(f"  Original names used:")
                for orig in sorted(originals):
                    if orig != canonical:
                        print(f"    ← {orig}")
            print()

        if len(variations_found) > 20:
            print(f"... and {len(variations_found) - 20} more venues with variations")
    else:
        print("\nNo venue variations found.")

    conn.close()

def review_unmapped_artists():
    """Show artists that weren't mapped"""
    print("=" * 80)
    print("UNMAPPED ARTISTS (Need Review)")
    print("=" * 80)

    raw_data = load_raw_data()

    # Count how many times each unmapped artist appears
    unmapped = defaultdict(int)

    for record in raw_data:
        headliner = record.get('headliner')
        headliner_canonical = record.get('headliner_canonical')

        if headliner and headliner == headliner_canonical:
            # Not mapped if original equals canonical (no change)
            # But check if it's in our mapping file
            pass

        opener = record.get('opener')
        opener_canonical = record.get('opener_canonical')

        if opener and opener == opener_canonical:
            pass

    conn = connect_db()
    cursor = conn.cursor()

    # Find artists seen multiple times (good candidates for mapping)
    cursor.execute('''
        SELECT a.canonical_name, COUNT(*) as times_seen
        FROM artists a
        JOIN concert_artists ca ON a.id = ca.artist_id
        WHERE ca.role = 'headliner'
        GROUP BY a.id
        HAVING times_seen >= 2
        ORDER BY times_seen DESC
        LIMIT 30
    ''')

    print("\nArtists seen 2+ times (candidates for mapping verification):\n")
    for artist, count in cursor.fetchall():
        print(f"  {count:3d}x - {artist}")

    conn.close()

def review_unmapped_venues():
    """Show venues that weren't mapped"""
    print("\n" + "=" * 80)
    print("UNMAPPED VENUES (Need Location Data)")
    print("=" * 80)

    conn = connect_db()
    cursor = conn.cursor()

    # Find venues without location data
    cursor.execute('''
        SELECT v.canonical_name, COUNT(*) as times_visited
        FROM venues v
        JOIN concerts c ON v.id = c.venue_id
        WHERE (v.city IS NULL OR v.city = '')
        AND c.attended = 1
        GROUP BY v.id
        HAVING times_visited >= 2
        ORDER BY times_visited DESC
        LIMIT 30
    ''')

    results = cursor.fetchall()

    if results:
        print(f"\nVenues visited 2+ times without location data ({len(results)}):\n")
        for venue, count in results:
            print(f"  {count:3d}x - {venue}")
        print("\nAdd these to mappings/venue_mapping.csv with city, state, and type")
    else:
        print("\nAll frequently-visited venues have location data!")

    conn.close()

def review_date_issues():
    """Show concerts with date problems"""
    print("\n" + "=" * 80)
    print("DATE ISSUES (Need Manual Review)")
    print("=" * 80)

    conn = connect_db()
    cursor = conn.cursor()

    # Find concerts with date issues
    cursor.execute('''
        SELECT c.show_number, a.canonical_name, v.canonical_name, c.date
        FROM concerts c
        LEFT JOIN concert_artists ca ON c.id = ca.concert_id AND ca.role = 'headliner'
        LEFT JOIN artists a ON ca.artist_id = a.id
        LEFT JOIN venues v ON c.venue_id = v.id
        WHERE c.date_unknown = 1
        ORDER BY c.show_number
    ''')

    results = cursor.fetchall()

    if results:
        print(f"\nFound {len(results)} concerts with date issues:\n")
        for show_num, artist, venue, date in results:
            print(f"  Show #{show_num if show_num else '?'}: {artist or 'Unknown Artist'}")
            print(f"    Venue: {venue or 'Unknown'}")
            print(f"    Date: {date or 'Unknown'}")
            print()
    else:
        print("\nNo date issues found!")

    conn.close()

def review_opening_acts():
    """Show concerts with opening acts"""
    print("=" * 80)
    print("OPENING ACTS DETECTED")
    print("=" * 80)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            c.date,
            h.canonical_name as headliner,
            o.canonical_name as opener,
            v.canonical_name as venue
        FROM concerts c
        JOIN concert_artists ca_h ON c.id = ca_h.concert_id AND ca_h.role = 'headliner'
        JOIN artists h ON ca_h.artist_id = h.id
        JOIN concert_artists ca_o ON c.id = ca_o.concert_id AND ca_o.role = 'opener'
        JOIN artists o ON ca_o.artist_id = o.id
        LEFT JOIN venues v ON c.venue_id = v.id
        WHERE c.attended = 1
        ORDER BY c.date DESC
        LIMIT 20
    ''')

    results = cursor.fetchall()

    if results:
        print(f"\nFound {len(results)} concerts with opening acts (showing 20 most recent):\n")
        for date, headliner, opener, venue in results:
            print(f"  {date} - {headliner}")
            print(f"    w/ {opener}")
            print(f"    @ {venue or 'Unknown venue'}")
            print()
    else:
        print("\nNo concerts with opening acts found.")

    cursor.execute('''
        SELECT COUNT(DISTINCT concert_id)
        FROM concert_artists
        WHERE role = 'opener'
    ''')

    total = cursor.fetchone()[0]
    print(f"Total concerts with openers: {total}")

    conn.close()

def review_summary():
    """Show overall data quality summary"""
    print("=" * 80)
    print("DATA QUALITY SUMMARY")
    print("=" * 80)

    conn = connect_db()
    cursor = conn.cursor()

    # Total stats
    cursor.execute('SELECT COUNT(*) FROM concerts WHERE attended = 1')
    total_concerts = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM concerts WHERE date_unknown = 0 AND attended = 1')
    good_dates = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM concerts WHERE date_unknown = 1')
    bad_dates = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT venue_id) FROM concerts WHERE venue_id IS NOT NULL')
    venues_used = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM venues WHERE city IS NOT NULL AND city != ""')
    venues_with_location = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM artist_aliases')
    aliases_mapped = cursor.fetchone()[0]

    print(f"\n✓ Concerts with clean dates: {good_dates}/{total_concerts} ({good_dates*100//total_concerts}%)")
    print(f"✗ Concerts with date issues: {bad_dates}")
    print(f"\n✓ Venues with location data: {venues_with_location}/{venues_used} ({venues_with_location*100//venues_used}%)")
    print(f"✓ Artist name variations mapped: {aliases_mapped}")

    # Most common data quality issues
    cursor.execute('''
        SELECT v.canonical_name, COUNT(*) as times
        FROM concerts c
        JOIN venues v ON c.venue_id = v.id
        WHERE (v.city IS NULL OR v.city = '')
        GROUP BY v.id
        ORDER BY times DESC
        LIMIT 5
    ''')

    unmapped_venues = cursor.fetchall()
    if unmapped_venues:
        print(f"\nTop venues needing location data:")
        for venue, times in unmapped_venues:
            print(f"  {times:3d}x - {venue}")

    conn.close()

if __name__ == "__main__":
    print("\n")
    review_summary()
    print("\n")

    review_artist_mappings()
    print("\n")

    review_venue_mappings()
    print("\n")

    review_unmapped_artists()

    review_unmapped_venues()

    review_date_issues()
    print("\n")

    review_opening_acts()

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("""
1. Review the unmapped artists and venues above
2. Add frequently-seen ones to the mapping CSV files:
   - mappings/artist_mapping.csv
   - mappings/venue_mapping.csv
3. Re-run the pipeline: python3 scripts/run_all.py
4. Run this review script again to check improvements
""")
