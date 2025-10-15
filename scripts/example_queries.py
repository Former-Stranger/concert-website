#!/usr/bin/env python3
"""
Example queries to demonstrate the database capabilities
"""

import sqlite3
from pathlib import Path

def connect_db():
    """Connect to the database"""
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / "database" / "concerts.db"
    return sqlite3.connect(db_path)

def query_artist(artist_name):
    """Find all concerts for a specific artist"""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            c.date,
            v.canonical_name as venue,
            v.city,
            v.state,
            ca.role,
            c.opening_song,
            c.closing_song
        FROM concerts c
        JOIN concert_artists ca ON c.id = ca.concert_id
        JOIN artists a ON ca.artist_id = a.id
        LEFT JOIN venues v ON c.venue_id = v.id
        WHERE a.canonical_name LIKE ?
        AND c.attended = 1
        ORDER BY c.date
    ''', (f'%{artist_name}%',))

    results = cursor.fetchall()
    conn.close()

    return results

def query_venue_history(venue_name):
    """Find all concerts at a specific venue"""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            c.date,
            a.canonical_name as artist,
            ca.role
        FROM concerts c
        JOIN venues v ON c.venue_id = v.id
        JOIN concert_artists ca ON c.id = ca.concert_id
        JOIN artists a ON ca.artist_id = a.id
        WHERE v.canonical_name LIKE ? OR v.short_name LIKE ?
        AND c.attended = 1
        ORDER BY c.date DESC
        LIMIT 20
    ''', (f'%{venue_name}%', f'%{venue_name}%'))

    results = cursor.fetchall()
    conn.close()

    return results

def query_year(year):
    """Find all concerts in a specific year"""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            c.date,
            a.canonical_name as artist,
            v.canonical_name as venue,
            ca.role
        FROM concerts c
        JOIN concert_artists ca ON c.id = ca.concert_id
        JOIN artists a ON ca.artist_id = a.id
        LEFT JOIN venues v ON c.venue_id = v.id
        WHERE strftime('%Y', c.date) = ?
        AND c.attended = 1
        ORDER BY c.date
    ''', (str(year),))

    results = cursor.fetchall()
    conn.close()

    return results

def query_artist_venue_combo(artist_name, venue_name):
    """Find all concerts of a specific artist at a specific venue"""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            c.date,
            c.opening_song,
            c.closing_song
        FROM concerts c
        JOIN venues v ON c.venue_id = v.id
        JOIN concert_artists ca ON c.id = ca.concert_id
        JOIN artists a ON ca.artist_id = a.id
        WHERE a.canonical_name LIKE ?
        AND (v.canonical_name LIKE ? OR v.short_name LIKE ?)
        AND ca.role = 'headliner'
        AND c.attended = 1
        ORDER BY c.date
    ''', (f'%{artist_name}%', f'%{venue_name}%', f'%{venue_name}%'))

    results = cursor.fetchall()
    conn.close()

    return results

if __name__ == "__main__":
    import sys

    print("=" * 80)
    print("CONCERT DATABASE - EXAMPLE QUERIES")
    print("=" * 80)

    # Example 1: Bruce Springsteen concerts
    print("\n\nExample 1: All Bruce Springsteen concerts (showing first 10)")
    print("-" * 80)
    results = query_artist("Bruce Springsteen")
    for i, (date, venue, city, state, role, opening, closing) in enumerate(results[:10], 1):
        location = f"{city}, {state}" if city else ""
        print(f"{i:2d}. {date} - {venue:35s} ({role})")
        if opening:
            print(f"    Opened with: {opening}")
        if closing:
            print(f"    Closed with: {closing}")

    print(f"\n    ... and {len(results) - 10} more concerts")

    # Example 2: MSG history
    print("\n\nExample 2: Recent concerts at Madison Square Garden (last 20)")
    print("-" * 80)
    results = query_venue_history("MSG")
    for i, (date, artist, role) in enumerate(results[:20], 1):
        print(f"{i:2d}. {date} - {artist:40s} ({role})")

    # Example 3: 2024 concerts
    print("\n\nExample 3: All concerts in 2024 (showing first 15)")
    print("-" * 80)
    results = query_year(2024)
    for i, (date, artist, venue, role) in enumerate(results[:15], 1):
        print(f"{i:2d}. {date} - {artist:35s} @ {venue or 'TBD'}")

    print(f"\n    Total in 2024: {len(results)} concerts")

    # Example 4: Billy Joel at MSG
    print("\n\nExample 4: Billy Joel at Madison Square Garden")
    print("-" * 80)
    results = query_artist_venue_combo("Billy Joel", "MSG")
    print(f"Billy Joel has played MSG {len(results)} times!")
    print("\nFirst 5 shows:")
    for i, (date, opening, closing) in enumerate(results[:5], 1):
        print(f"{i}. {date}")
        if opening:
            print(f"   Opened: {opening}")
        if closing:
            print(f"   Closed: {closing}")

    print("\n\nLast 5 shows:")
    for i, (date, opening, closing) in enumerate(results[-5:], len(results)-4):
        print(f"{i}. {date}")
        if opening:
            print(f"   Opened: {opening}")
        if closing:
            print(f"   Closed: {closing}")

    print("\n" + "=" * 80)
    print("You can modify this script to create your own queries!")
    print("=" * 80)
