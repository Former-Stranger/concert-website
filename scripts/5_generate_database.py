#!/usr/bin/env python3
"""
Step 5: Generate SQLite database from cleaned data
"""

import json
import sqlite3
from pathlib import Path
from collections import defaultdict

def create_schema(conn):
    """Create database schema"""

    cursor = conn.cursor()

    # Artists table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Artist aliases table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artist_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artist_id INTEGER NOT NULL,
            alias TEXT NOT NULL UNIQUE,
            FOREIGN KEY (artist_id) REFERENCES artists(id)
        )
    ''')

    # Venues table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS venues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_name TEXT NOT NULL UNIQUE,
            short_name TEXT,
            city TEXT,
            state TEXT,
            venue_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Concerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS concerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            show_number INTEGER,
            date DATE,
            date_unknown BOOLEAN DEFAULT 0,
            venue_id INTEGER,
            festival_name TEXT,
            opening_song TEXT,
            closing_song TEXT,
            notes TEXT,
            attended BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (venue_id) REFERENCES venues(id)
        )
    ''')

    # Concert-Artist relationship table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS concert_artists (
            concert_id INTEGER NOT NULL,
            artist_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            position INTEGER DEFAULT 1,
            PRIMARY KEY (concert_id, artist_id, role),
            FOREIGN KEY (concert_id) REFERENCES concerts(id),
            FOREIGN KEY (artist_id) REFERENCES artists(id)
        )
    ''')

    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_concerts_date ON concerts(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_concerts_venue ON concerts(venue_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_concert_artists_artist ON concert_artists(artist_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_concert_artists_concert ON concert_artists(concert_id)')

    conn.commit()

def insert_artists(conn, records):
    """Insert artists and their aliases"""

    cursor = conn.cursor()

    # Collect all unique canonical artists and their aliases
    artists_set = set()
    aliases = defaultdict(set)

    for record in records:
        # Get the artists array from the normalized data
        artists_list = record.get('artists', [])

        for artist_info in artists_list:
            canonical = artist_info.get('canonical')
            original = artist_info.get('original')

            if canonical:
                artists_set.add(canonical)
                if original and original != canonical:
                    aliases[canonical].add(original)

    # Insert artists
    artist_id_map = {}
    for artist in sorted(artists_set):
        cursor.execute(
            'INSERT OR IGNORE INTO artists (canonical_name) VALUES (?)',
            (artist,)
        )
        cursor.execute('SELECT id FROM artists WHERE canonical_name = ?', (artist,))
        artist_id = cursor.fetchone()[0]
        artist_id_map[artist] = artist_id

        # Insert aliases
        for alias in aliases[artist]:
            cursor.execute(
                'INSERT OR IGNORE INTO artist_aliases (artist_id, alias) VALUES (?, ?)',
                (artist_id, alias)
            )

    conn.commit()
    print(f"Inserted {len(artists_set)} artists with {sum(len(a) for a in aliases.values())} aliases")

    return artist_id_map

def insert_venues(conn, records):
    """Insert venues"""

    cursor = conn.cursor()

    # Collect unique venues
    venues = {}
    for record in records:
        canonical = record.get('venue_canonical')
        if canonical:
            venues[canonical] = {
                'short_name': record.get('venue_short', ''),
                'city': record.get('venue_city', ''),
                'state': record.get('venue_state', ''),
                'venue_type': record.get('venue_type', '')
            }

    # Insert venues
    venue_id_map = {}
    for canonical, data in sorted(venues.items()):
        cursor.execute(
            '''INSERT OR IGNORE INTO venues
               (canonical_name, short_name, city, state, venue_type)
               VALUES (?, ?, ?, ?, ?)''',
            (canonical, data['short_name'], data['city'], data['state'], data['venue_type'])
        )
        cursor.execute('SELECT id FROM venues WHERE canonical_name = ?', (canonical,))
        venue_id = cursor.fetchone()[0]
        venue_id_map[canonical] = venue_id

    conn.commit()
    print(f"Inserted {len(venues)} venues")

    return venue_id_map

def insert_concerts(conn, records, artist_id_map, venue_id_map):
    """Insert concerts and relationships"""

    cursor = conn.cursor()

    concerts_inserted = 0
    relationships_inserted = 0

    for record in records:
        # Get concert data
        show_number = record.get('# SHOW')
        date = record.get('date_clean')
        date_unknown = 1 if record.get('date_has_issue') else 0
        venue_canonical = record.get('venue_canonical')
        festival_name = record.get('festival_name')
        opening_song = record.get('OPENING SONG')
        closing_song = record.get('CLOSING SONG')
        attended = record.get('attended', True)

        venue_id = venue_id_map.get(venue_canonical) if venue_canonical else None

        # Insert concert
        cursor.execute(
            '''INSERT INTO concerts
               (show_number, date, date_unknown, venue_id, festival_name, opening_song, closing_song, attended)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (show_number, date, date_unknown, venue_id, festival_name, opening_song, closing_song, attended)
        )
        concert_id = cursor.lastrowid
        concerts_inserted += 1

        # Insert artist relationships
        artists_list = record.get('artists', [])
        for position, artist_info in enumerate(artists_list, start=1):
            canonical = artist_info.get('canonical')
            role = artist_info.get('role', 'headliner')

            if canonical and canonical in artist_id_map:
                artist_id = artist_id_map[canonical]
                cursor.execute(
                    '''INSERT INTO concert_artists
                       (concert_id, artist_id, role, position)
                       VALUES (?, ?, ?, ?)''',
                    (concert_id, artist_id, role, position)
                )
                relationships_inserted += 1

    conn.commit()
    print(f"Inserted {concerts_inserted} concerts")
    print(f"Created {relationships_inserted} artist-concert relationships")

def generate_database(input_path, db_path):
    """Generate SQLite database from cleaned JSON data"""

    print("=" * 80)
    print("STEP 5: GENERATING DATABASE")
    print("=" * 80)

    # Load cleaned data
    with open(input_path, 'r', encoding='utf-8') as f:
        records = json.load(f)

    # Create database
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing database
    if db_file.exists():
        db_file.unlink()

    conn = sqlite3.connect(db_file)

    try:
        # Create schema
        print("\nCreating database schema...")
        create_schema(conn)

        # Insert data
        print("\nInserting artists...")
        artist_id_map = insert_artists(conn, records)

        print("\nInserting venues...")
        venue_id_map = insert_venues(conn, records)

        print("\nInserting concerts...")
        insert_concerts(conn, records, artist_id_map, venue_id_map)

        print(f"\n✓ Database generated successfully: {db_file}")

    finally:
        conn.close()

if __name__ == "__main__":
    from pathlib import Path

    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    input_path = project_root / "data" / "cleaned_concerts.json"
    db_path = project_root / "database" / "concerts.db"

    generate_database(input_path, db_path)
    print("\n✓ Step 5 complete!")
