#!/usr/bin/env python3
"""
Fetch setlist data from setlist.fm for all concerts in the database
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from setlistfm_client import SetlistFMClient


def fetch_and_store_setlists(db_path, api_key, limit=None, skip_existing=True):
    """
    Fetch setlists for concerts and store in database

    Args:
        db_path: Path to concerts database
        api_key: setlist.fm API key
        limit: Optional limit on number of concerts to process
        skip_existing: Skip concerts that already have setlists
    """

    print("=" * 80)
    print("FETCHING SETLISTS FROM SETLIST.FM")
    print("=" * 80)

    # Initialize API client
    client = SetlistFMClient(api_key)

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get concerts that need setlists (past concerts only)
    # Note: Using '2024-10-01' as cutoff to avoid future concerts
    if skip_existing:
        query = '''
            SELECT
                c.id,
                c.show_number,
                c.date,
                v.canonical_name as venue_name,
                v.city,
                v.state,
                a.canonical_name as artist_name,
                ca.role
            FROM concerts c
            JOIN venues v ON c.venue_id = v.id
            JOIN concert_artists ca ON c.id = ca.concert_id
            JOIN artists a ON ca.artist_id = a.id
            LEFT JOIN setlists s ON c.id = s.concert_id
            WHERE c.date IS NOT NULL
              AND c.date_unknown = 0
              AND c.date < '2024-10-01'
              AND s.id IS NULL
              AND ca.role IN ('headliner', 'festival_performer')
            ORDER BY c.date DESC
        '''
    else:
        query = '''
            SELECT
                c.id,
                c.show_number,
                c.date,
                v.canonical_name as venue_name,
                v.city,
                v.state,
                a.canonical_name as artist_name,
                ca.role
            FROM concerts c
            JOIN venues v ON c.venue_id = v.id
            JOIN concert_artists ca ON c.id = ca.concert_id
            JOIN artists a ON ca.artist_id = a.id
            WHERE c.date IS NOT NULL
              AND c.date_unknown = 0
              AND c.date < '2024-10-01'
              AND ca.role IN ('headliner', 'festival_performer')
            ORDER BY c.date DESC
        '''

    if limit:
        query += f' LIMIT {limit}'

    cursor.execute(query)
    concerts = cursor.fetchall()

    print(f"\nFound {len(concerts)} concerts to process")
    print(f"Rate limit: 2 requests/sec, 1440/day")
    print(f"Estimated time: {len(concerts) * 0.6 / 60:.1f} minutes (~{len(concerts) * 0.6 / 3600:.1f} hours)\n")

    # Statistics
    found = 0
    not_found = 0
    errors = 0

    # Process each concert
    for i, (concert_id, show_num, date_str, venue, city, state, artist, role) in enumerate(concerts, 1):
        try:
            # Parse date
            date = datetime.strptime(date_str, '%Y-%m-%d')

            # Progress
            if i % 10 == 0:
                print(f"Progress: {i}/{len(concerts)} ({i/len(concerts)*100:.1f}%) - "
                      f"Found: {found}, Not found: {not_found}, Errors: {errors}")

            # Search for setlist
            setlist_data = client.find_setlist_for_concert(
                artist_name=artist,
                date=date,
                venue_name=venue,
                city=city,
                state=state
            )

            if setlist_data:
                # Extract songs
                songs = client.extract_songs_from_setlist(setlist_data)

                if songs:
                    # Store setlist metadata
                    setlistfm_id = setlist_data.get('id')
                    setlistfm_url = f"https://www.setlist.fm/setlist/{setlistfm_id}.html" if setlistfm_id else None
                    has_encore = any(s['encore'] > 0 for s in songs)

                    cursor.execute('''
                        INSERT OR REPLACE INTO setlists
                        (concert_id, setlistfm_id, setlistfm_url, song_count, has_encore)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (concert_id, setlistfm_id, setlistfm_url, len(songs), has_encore))

                    setlist_id = cursor.lastrowid

                    # Store songs
                    for song in songs:
                        cursor.execute('''
                            INSERT INTO setlist_songs
                            (setlist_id, position, song_name, set_name, encore, is_cover, cover_artist, is_tape, info)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            setlist_id,
                            song['position'],
                            song['name'],
                            song['set_name'],
                            song['encore'],
                            1 if song['cover'] else 0,
                            song['cover'],
                            song['tape'],
                            song['info']
                        ))

                    conn.commit()
                    found += 1

                    print(f"  ✓ Show #{show_num}: {artist} - {date_str} ({len(songs)} songs)")
                else:
                    # Setlist exists but no songs - mark as checked
                    cursor.execute('''
                        INSERT OR REPLACE INTO setlists
                        (concert_id, setlistfm_id, setlistfm_url, song_count, has_encore, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (concert_id, None, None, 0, 0, 'No songs listed'))
                    conn.commit()
                    not_found += 1
            else:
                # No setlist found - mark as checked so we don't retry
                cursor.execute('''
                    INSERT OR REPLACE INTO setlists
                    (concert_id, setlistfm_id, setlistfm_url, song_count, has_encore, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (concert_id, None, None, 0, 0, 'Not found on setlist.fm'))
                conn.commit()
                not_found += 1

        except Exception as e:
            errors += 1
            print(f"  ✗ Show #{show_num}: Error - {e}")
            continue

    conn.close()

    # Final summary
    print("\n" + "=" * 80)
    print("SETLIST FETCH COMPLETE")
    print("=" * 80)
    print(f"\nResults:")
    print(f"  ✓ Found: {found} setlists")
    print(f"  ✗ Not found: {not_found} concerts")
    print(f"  ⚠ Errors: {errors}")

    if len(concerts) > 0:
        print(f"\nCoverage: {found}/{len(concerts)} ({found/len(concerts)*100:.1f}%)")
    else:
        print(f"\nNo concerts were processed (all already checked or no concerts match criteria)")


def show_stats(db_path):
    """Show statistics about setlist data"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("SETLIST STATISTICS")
    print("=" * 80)

    # Total setlists
    cursor.execute("SELECT COUNT(*) FROM setlists")
    total = cursor.fetchone()[0]
    print(f"\nTotal setlists: {total}")

    # Total songs
    cursor.execute("SELECT COUNT(*) FROM setlist_songs")
    songs = cursor.fetchone()[0]
    print(f"Total songs: {songs}")

    # Average songs per show
    if total > 0:
        print(f"Average songs per show: {songs/total:.1f}")

    # Encores
    cursor.execute("SELECT COUNT(*) FROM setlists WHERE has_encore = 1")
    encores = cursor.fetchone()[0]
    if total > 0:
        print(f"Shows with encores: {encores} ({encores/total*100:.1f}%)")
    else:
        print(f"Shows with encores: {encores}")

    # Most common closing songs
    print("\n" + "=" * 80)
    print("TOP 10 CLOSING SONGS (across all artists)")
    print("=" * 80)

    cursor.execute('''
        SELECT
            song_name,
            COUNT(*) as times
        FROM setlist_songs
        WHERE position = (
            SELECT MAX(position)
            FROM setlist_songs ss2
            WHERE ss2.setlist_id = setlist_songs.setlist_id
        )
        GROUP BY song_name
        ORDER BY times DESC
        LIMIT 10
    ''')

    for i, (song, count) in enumerate(cursor.fetchall(), 1):
        print(f"{i:2d}. {song:40s} - {count} times")

    conn.close()


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    db_path = project_root / "database" / "concerts.db"

    if len(sys.argv) < 2:
        print("=" * 80)
        print("SETLIST.FM DATA FETCHER")
        print("=" * 80)
        print("\nUsage:")
        print("  python3 fetch_setlists.py YOUR_API_KEY [options]")
        print("\nOptions:")
        print("  --limit N       Process only N concerts (for testing)")
        print("  --all           Fetch all, including existing setlists")
        print("  --stats-only    Only show statistics, don't fetch")
        print("\nExamples:")
        print("  # Fetch setlists for all concerts:")
        print("  python3 fetch_setlists.py your-api-key-here")
        print("\n  # Test with first 10 concerts:")
        print("  python3 fetch_setlists.py your-api-key-here --limit 10")
        print("\n  # Show statistics:")
        print("  python3 fetch_setlists.py your-api-key-here --stats-only")
        sys.exit(1)

    api_key = sys.argv[1]
    limit = None
    skip_existing = True
    stats_only = False

    # Parse options
    if '--limit' in sys.argv:
        idx = sys.argv.index('--limit')
        limit = int(sys.argv[idx + 1])

    if '--all' in sys.argv:
        skip_existing = False

    if '--stats-only' in sys.argv:
        stats_only = True

    if not stats_only:
        # Fetch setlists
        fetch_and_store_setlists(db_path, api_key, limit, skip_existing)

    # Show statistics
    show_stats(db_path)
