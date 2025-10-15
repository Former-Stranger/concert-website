#!/usr/bin/env python3
"""
Review results of setlist fetching - show what was found and what wasn't
"""

import sqlite3
from pathlib import Path


def review_results(db_path):
    """Show comprehensive results of setlist fetching"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 80)
    print("SETLIST FETCH RESULTS")
    print("=" * 80)

    # Overall statistics - count DISTINCT concerts, not artist relationships
    cursor.execute('''
        SELECT COUNT(DISTINCT c.id) FROM concerts c
        JOIN concert_artists ca ON c.id = ca.concert_id
        WHERE c.date IS NOT NULL
          AND c.date_unknown = 0
          AND c.date < '2024-10-01'
          AND ca.role IN ('headliner', 'festival_performer')
    ''')
    total_concerts = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM setlists')
    checked_concerts = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM setlists WHERE song_count > 0')
    found_concerts = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM setlists WHERE song_count = 0')
    not_found_concerts = cursor.fetchone()[0]

    unchecked = total_concerts - checked_concerts

    print(f"\nOverall Progress:")
    print(f"  Total past concerts: {total_concerts}")
    print(f"  Checked: {checked_concerts} ({checked_concerts/total_concerts*100:.1f}%)")
    print(f"  Not yet checked: {unchecked}")
    print(f"\nResults:")
    print(f"  ✓ Setlists found: {found_concerts} ({found_concerts/checked_concerts*100:.1f}% of checked)")
    print(f"  ✗ Not found: {not_found_concerts} ({not_found_concerts/checked_concerts*100:.1f}% of checked)")

    # Total songs
    cursor.execute('SELECT COUNT(*) FROM setlist_songs')
    total_songs = cursor.fetchone()[0]
    if found_concerts > 0:
        print(f"\nTotal songs collected: {total_songs} ({total_songs/found_concerts:.1f} per setlist)")

    # Show setlists found
    print("\n" + "=" * 80)
    print("SETLISTS FOUND (with songs)")
    print("=" * 80)

    cursor.execute('''
        SELECT
            c.show_number,
            c.date,
            a.canonical_name,
            v.canonical_name,
            sl.song_count
        FROM setlists sl
        JOIN concerts c ON sl.concert_id = c.id
        JOIN concert_artists ca ON c.id = ca.concert_id
        JOIN artists a ON ca.artist_id = a.id
        JOIN venues v ON c.venue_id = v.id
        WHERE sl.song_count > 0
        ORDER BY c.date DESC
        LIMIT 50
    ''')

    results = cursor.fetchall()
    if results:
        print(f"\nShowing first {min(50, len(results))} of {found_concerts} found:\n")
        for show_num, date, artist, venue, songs in results:
            print(f"  ✓ Show #{show_num}: {date} - {artist} at {venue} ({songs} songs)")
    else:
        print("\n(No setlists found yet)")

    # Show concerts not found
    print("\n" + "=" * 80)
    print("CONCERTS CHECKED BUT NOT FOUND")
    print("=" * 80)

    cursor.execute('''
        SELECT
            c.show_number,
            c.date,
            a.canonical_name,
            v.canonical_name,
            sl.notes
        FROM setlists sl
        JOIN concerts c ON sl.concert_id = c.id
        JOIN concert_artists ca ON c.id = ca.concert_id
        JOIN artists a ON ca.artist_id = a.id
        JOIN venues v ON c.venue_id = v.id
        WHERE sl.song_count = 0
        ORDER BY c.date DESC
        LIMIT 50
    ''')

    results = cursor.fetchall()
    if results:
        print(f"\nShowing first {min(50, len(results))} of {not_found_concerts} not found:\n")
        for show_num, date, artist, venue, notes in results:
            print(f"  ✗ Show #{show_num}: {date} - {artist} at {venue}")
    else:
        print("\n(All checked concerts had setlists)")

    # Show what's left to check
    if unchecked > 0:
        print("\n" + "=" * 80)
        print(f"CONCERTS NOT YET CHECKED: {unchecked}")
        print("=" * 80)
        print(f"\nRun the fetch script again to continue checking remaining concerts")

    conn.close()


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    db_path = project_root / "database" / "concerts.db"

    review_results(db_path)
