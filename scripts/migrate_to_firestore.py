#!/usr/bin/env python3
"""
One-time migration script to copy all data from SQLite to Firestore.

This will:
1. Copy all artists to Firestore
2. Copy all venues to Firestore
3. Copy all concerts to Firestore (with denormalized artist/venue data)
4. Copy all setlists to Firestore (with inline songs)

Usage: python3 migrate_to_firestore.py [--dry-run]
"""

import sys
import sqlite3
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json

DB_PATH = "database/concerts.db"

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        firebase_admin.get_app()
    except ValueError:
        # Try to use application default credentials
        # This works if you've run: gcloud auth application-default login
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Could not use application default credentials: {e}")
            print("\nTo fix this, run:")
            print("  gcloud auth application-default login")
            print("\nOr download a service account key and set GOOGLE_APPLICATION_CREDENTIALS:")
            print("  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json")
            sys.exit(1)
    return firestore.client()

def migrate_artists(db_firestore, db_sqlite, dry_run=False):
    """Migrate artists from SQLite to Firestore"""
    print("\n" + "="*80)
    print("MIGRATING ARTISTS")
    print("="*80)

    cursor = db_sqlite.cursor()

    # Get all artists with their aliases
    cursor.execute("""
        SELECT
            a.id,
            a.canonical_name,
            GROUP_CONCAT(aa.alias, '|') as aliases
        FROM artists a
        LEFT JOIN artist_aliases aa ON a.id = aa.artist_id
        GROUP BY a.id
        ORDER BY a.canonical_name
    """)

    artists = cursor.fetchall()
    print(f"Found {len(artists)} artists to migrate")

    if dry_run:
        for row in artists[:5]:
            print(f"  Would migrate: {row[1]} (ID: {row[0]})")
        if len(artists) > 5:
            print(f"  ... and {len(artists) - 5} more")
        return

    # Migrate to Firestore
    batch = db_firestore.batch()
    count = 0

    for row in artists:
        artist_id, canonical_name, aliases_str = row

        # Use SQLite ID as Firestore document ID for easy referencing
        doc_ref = db_firestore.collection('artists').document(str(artist_id))

        data = {
            'canonical_name': canonical_name,
            'created_at': firestore.SERVER_TIMESTAMP
        }

        if aliases_str:
            data['aliases'] = aliases_str.split('|')

        batch.set(doc_ref, data)
        count += 1

        # Commit in batches of 500 (Firestore limit)
        if count % 500 == 0:
            batch.commit()
            print(f"  Committed {count} artists...")
            batch = db_firestore.batch()

    # Commit remaining
    if count % 500 != 0:
        batch.commit()

    print(f"✓ Migrated {count} artists")

def migrate_venues(db_firestore, db_sqlite, dry_run=False):
    """Migrate venues from SQLite to Firestore"""
    print("\n" + "="*80)
    print("MIGRATING VENUES")
    print("="*80)

    cursor = db_sqlite.cursor()
    cursor.execute("""
        SELECT id, canonical_name, short_name, city, state, venue_type
        FROM venues
        ORDER BY canonical_name
    """)

    venues = cursor.fetchall()
    print(f"Found {len(venues)} venues to migrate")

    if dry_run:
        for row in venues[:5]:
            print(f"  Would migrate: {row[1]} ({row[3]}, {row[4]})")
        if len(venues) > 5:
            print(f"  ... and {len(venues) - 5} more")
        return

    batch = db_firestore.batch()
    count = 0

    for row in venues:
        venue_id, canonical_name, short_name, city, state, venue_type = row

        doc_ref = db_firestore.collection('venues').document(str(venue_id))

        data = {
            'canonical_name': canonical_name,
            'city': city or '',
            'state': state or '',
            'created_at': firestore.SERVER_TIMESTAMP
        }

        if short_name:
            data['short_name'] = short_name
        if venue_type:
            data['venue_type'] = venue_type

        batch.set(doc_ref, data)
        count += 1

        if count % 500 == 0:
            batch.commit()
            print(f"  Committed {count} venues...")
            batch = db_firestore.batch()

    if count % 500 != 0:
        batch.commit()

    print(f"✓ Migrated {count} venues")

def migrate_concerts(db_firestore, db_sqlite, dry_run=False):
    """Migrate concerts from SQLite to Firestore"""
    print("\n" + "="*80)
    print("MIGRATING CONCERTS")
    print("="*80)

    cursor = db_sqlite.cursor()

    # Get all concerts with venue and artist info
    cursor.execute("""
        SELECT
            c.id,
            c.show_number,
            c.date,
            c.date_unknown,
            c.venue_id,
            v.canonical_name as venue_name,
            v.city,
            v.state,
            c.festival_name,
            c.opening_song,
            c.closing_song,
            c.notes,
            c.attended,
            CASE WHEN s.id IS NOT NULL THEN 1 ELSE 0 END as has_setlist
        FROM concerts c
        LEFT JOIN venues v ON c.venue_id = v.id
        LEFT JOIN setlists s ON c.id = s.concert_id
        ORDER BY c.date DESC
    """)

    concerts = cursor.fetchall()
    print(f"Found {len(concerts)} concerts to migrate")

    if dry_run:
        for row in concerts[:5]:
            print(f"  Would migrate: Concert {row[0]} on {row[2]} at {row[5]}")
        if len(concerts) > 5:
            print(f"  ... and {len(concerts) - 5} more")
        return

    batch = db_firestore.batch()
    count = 0

    for row in concerts:
        concert_id = row[0]

        # Get artists for this concert
        cursor.execute("""
            SELECT
                ca.artist_id,
                a.canonical_name,
                ca.role,
                ca.position
            FROM concert_artists ca
            JOIN artists a ON ca.artist_id = a.id
            WHERE ca.concert_id = ?
            ORDER BY ca.position
        """, (concert_id,))

        artists_data = []
        for artist_row in cursor.fetchall():
            artists_data.append({
                'artist_id': str(artist_row[0]),
                'artist_name': artist_row[1],
                'role': artist_row[2],
                'position': artist_row[3]
            })

        doc_ref = db_firestore.collection('concerts').document(str(concert_id))

        data = {
            'show_number': row[1],
            'date': row[2] or '',
            'date_unknown': bool(row[3]),
            'venue_id': str(row[4]) if row[4] else '',
            'venue_name': row[5] or '',
            'city': row[6] or '',
            'state': row[7] or '',
            'artists': artists_data,
            'attended': bool(row[12]),
            'has_setlist': bool(row[13]),
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }

        if row[8]:  # festival_name
            data['festival_name'] = row[8]
        if row[9]:  # opening_song
            data['opening_song'] = row[9]
        if row[10]:  # closing_song
            data['closing_song'] = row[10]
        if row[11]:  # notes
            data['notes'] = row[11]

        batch.set(doc_ref, data)
        count += 1

        if count % 500 == 0:
            batch.commit()
            print(f"  Committed {count} concerts...")
            batch = db_firestore.batch()

    if count % 500 != 0:
        batch.commit()

    print(f"✓ Migrated {count} concerts")

def migrate_setlists(db_firestore, db_sqlite, dry_run=False):
    """Migrate setlists from SQLite to Firestore"""
    print("\n" + "="*80)
    print("MIGRATING SETLISTS")
    print("="*80)

    cursor = db_sqlite.cursor()

    # Get all setlists
    cursor.execute("""
        SELECT
            s.id,
            s.concert_id,
            s.setlistfm_id,
            s.setlistfm_url,
            s.song_count,
            s.has_encore,
            s.notes
        FROM setlists s
        ORDER BY s.concert_id
    """)

    setlists = cursor.fetchall()
    print(f"Found {len(setlists)} setlists to migrate")

    if dry_run:
        for row in setlists[:5]:
            print(f"  Would migrate: Setlist for concert {row[1]} ({row[4]} songs)")
        if len(setlists) > 5:
            print(f"  ... and {len(setlists) - 5} more")
        return

    batch = db_firestore.batch()
    count = 0

    for row in setlists:
        setlist_id, concert_id, setlistfm_id, setlistfm_url, song_count, has_encore, notes = row

        # Get all songs for this setlist
        cursor.execute("""
            SELECT
                position,
                song_name,
                set_name,
                encore,
                is_cover,
                cover_artist,
                is_tape,
                info
            FROM setlist_songs
            WHERE setlist_id = ?
            ORDER BY position
        """, (setlist_id,))

        songs_data = []
        for song_row in cursor.fetchall():
            song = {
                'position': song_row[0],
                'name': song_row[1],
                'set_name': song_row[2] or '',
                'encore': song_row[3] or 0,
                'is_cover': bool(song_row[4]),
                'is_tape': bool(song_row[6])
            }

            if song_row[5]:  # cover_artist
                song['cover_artist'] = song_row[5]
            if song_row[7]:  # info
                song['info'] = song_row[7]

            songs_data.append(song)

        # Use auto-generated ID for setlists (we don't need to preserve SQLite IDs here)
        doc_ref = db_firestore.collection('setlists').document()

        data = {
            'concert_id': str(concert_id),
            'song_count': song_count or 0,
            'has_encore': bool(has_encore),
            'songs': songs_data,
            'created_at': firestore.SERVER_TIMESTAMP
        }

        if setlistfm_id:
            data['setlistfm_id'] = setlistfm_id
        if setlistfm_url:
            data['setlistfm_url'] = setlistfm_url
        if notes:
            data['notes'] = notes

        batch.set(doc_ref, data)
        count += 1

        if count % 500 == 0:
            batch.commit()
            print(f"  Committed {count} setlists...")
            batch = db_firestore.batch()

    if count % 500 != 0:
        batch.commit()

    print(f"✓ Migrated {count} setlists")

def main():
    dry_run = '--dry-run' in sys.argv
    skip_confirm = '--yes' in sys.argv or '-y' in sys.argv

    if dry_run:
        print("\n" + "="*80)
        print("DRY RUN MODE - No data will be written to Firestore")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("MIGRATING DATA TO FIRESTORE")
        print("="*80)
        if not skip_confirm:
            response = input("\nThis will copy all data from SQLite to Firestore. Continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Migration cancelled.")
                sys.exit(0)

    print("\nInitializing Firebase...")
    db_firestore = init_firebase()

    print("Connecting to SQLite database...")
    db_sqlite = sqlite3.connect(DB_PATH)
    db_sqlite.row_factory = sqlite3.Row

    try:
        # Run migrations in order
        migrate_artists(db_firestore, db_sqlite, dry_run)
        migrate_venues(db_firestore, db_sqlite, dry_run)
        migrate_concerts(db_firestore, db_sqlite, dry_run)
        migrate_setlists(db_firestore, db_sqlite, dry_run)

        print("\n" + "="*80)
        if dry_run:
            print("DRY RUN COMPLETE")
            print("\nRun without --dry-run to perform the actual migration:")
            print("  python3 scripts/migrate_to_firestore.py")
        else:
            print("✓ MIGRATION COMPLETE!")
            print("\nAll data has been successfully migrated to Firestore.")
        print("="*80 + "\n")

    finally:
        db_sqlite.close()

if __name__ == "__main__":
    main()
