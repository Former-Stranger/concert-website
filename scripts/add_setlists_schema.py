#!/usr/bin/env python3
"""
Add setlist tables to the database
"""

import sqlite3
from pathlib import Path

def add_setlist_schema(db_path):
    """Add tables for storing setlist data"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 80)
    print("ADDING SETLIST SCHEMA TO DATABASE")
    print("=" * 80)

    # Table for storing setlist metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS setlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concert_id INTEGER NOT NULL UNIQUE,
            setlistfm_id TEXT,
            setlistfm_url TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            song_count INTEGER,
            has_encore BOOLEAN DEFAULT 0,
            notes TEXT,
            FOREIGN KEY (concert_id) REFERENCES concerts(id)
        )
    ''')

    # Table for storing individual songs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS setlist_songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setlist_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            song_name TEXT NOT NULL,
            set_name TEXT,
            encore INTEGER DEFAULT 0,
            is_cover BOOLEAN DEFAULT 0,
            cover_artist TEXT,
            is_tape BOOLEAN DEFAULT 0,
            info TEXT,
            FOREIGN KEY (setlist_id) REFERENCES setlists(id)
        )
    ''')

    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_setlists_concert ON setlists(concert_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_setlist_songs_setlist ON setlist_songs(setlist_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_setlist_songs_name ON setlist_songs(song_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_setlist_songs_position ON setlist_songs(position)')

    conn.commit()
    conn.close()

    print("\n✓ Setlist tables added successfully!")
    print("\nTables created:")
    print("  - setlists: Stores setlist metadata for each concert")
    print("  - setlist_songs: Stores individual songs with position and details")
    print("\nIndexes created for optimal query performance")


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    db_path = project_root / "database" / "concerts.db"

    add_setlist_schema(db_path)
    print("\n" + "=" * 80)
    print("Schema update complete!")
