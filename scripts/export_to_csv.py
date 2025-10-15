#!/usr/bin/env python3
"""
Export cleaned data to CSV for easy review in Excel
"""

import sqlite3
import csv
from pathlib import Path

def connect_db():
    """Connect to the database"""
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / "database" / "concerts.db"
    return sqlite3.connect(db_path)

def export_concerts():
    """Export all concerts to CSV"""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            c.show_number,
            c.date,
            h.canonical_name as headliner,
            o.canonical_name as opener,
            v.canonical_name as venue,
            v.city || ', ' || v.state as location,
            v.venue_type,
            c.opening_song,
            c.closing_song,
            CASE WHEN c.attended = 1 THEN 'Yes' ELSE 'No' END as attended,
            CASE WHEN c.date_unknown = 1 THEN 'Issue' ELSE 'OK' END as date_status
        FROM concerts c
        LEFT JOIN concert_artists ca_h ON c.id = ca_h.concert_id AND ca_h.role = 'headliner'
        LEFT JOIN artists h ON ca_h.artist_id = h.id
        LEFT JOIN concert_artists ca_o ON c.id = ca_o.concert_id AND ca_o.role = 'opener'
        LEFT JOIN artists o ON ca_o.artist_id = o.id
        LEFT JOIN venues v ON c.venue_id = v.id
        ORDER BY c.date, c.show_number
    ''')

    rows = cursor.fetchall()

    # Write to CSV
    script_dir = Path(__file__).parent
    output_file = script_dir.parent / "data" / "concerts_cleaned.csv"

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Show #', 'Date', 'Headliner', 'Opener', 'Venue',
            'Location', 'Venue Type', 'Opening Song', 'Closing Song',
            'Attended', 'Date Status'
        ])
        writer.writerows(rows)

    conn.close()

    print(f"✓ Exported {len(rows)} concerts to: {output_file}")
    return output_file

def export_artist_stats():
    """Export artist statistics to CSV"""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            a.canonical_name as artist,
            COUNT(*) as times_seen,
            MIN(c.date) as first_concert,
            MAX(c.date) as last_concert,
            GROUP_CONCAT(DISTINCT v.canonical_name) as venues
        FROM artists a
        JOIN concert_artists ca ON a.id = ca.artist_id
        JOIN concerts c ON ca.concert_id = c.id
        LEFT JOIN venues v ON c.venue_id = v.id
        WHERE ca.role = 'headliner' AND c.attended = 1
        GROUP BY a.id
        ORDER BY times_seen DESC, artist
    ''')

    rows = cursor.fetchall()

    script_dir = Path(__file__).parent
    output_file = script_dir.parent / "data" / "artist_statistics.csv"

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Artist', 'Times Seen', 'First Concert', 'Last Concert', 'Venues (sample)'])

        for artist, times, first, last, venues in rows:
            # Limit venue list to first 5
            venue_list = venues.split(',')[:5] if venues else []
            venue_str = ', '.join(venue_list)
            if len(venue_list) < (len(venues.split(',')) if venues else 0):
                venue_str += '...'

            writer.writerow([artist, times, first, last, venue_str])

    conn.close()

    print(f"✓ Exported {len(rows)} artists to: {output_file}")
    return output_file

def export_venue_stats():
    """Export venue statistics to CSV"""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            v.canonical_name as venue,
            v.short_name,
            v.city,
            v.state,
            v.venue_type,
            COUNT(*) as times_visited,
            MIN(c.date) as first_visit,
            MAX(c.date) as last_visit
        FROM venues v
        JOIN concerts c ON v.id = c.venue_id
        WHERE c.attended = 1
        GROUP BY v.id
        ORDER BY times_visited DESC, venue
    ''')

    rows = cursor.fetchall()

    script_dir = Path(__file__).parent
    output_file = script_dir.parent / "data" / "venue_statistics.csv"

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Venue', 'Short Name', 'City', 'State', 'Type', 'Times Visited', 'First Visit', 'Last Visit'])
        writer.writerows(rows)

    conn.close()

    print(f"✓ Exported {len(rows)} venues to: {output_file}")
    return output_file

if __name__ == "__main__":
    print("=" * 80)
    print("EXPORTING DATA TO CSV")
    print("=" * 80)
    print()

    export_concerts()
    export_artist_stats()
    export_venue_stats()

    print()
    print("=" * 80)
    print("DONE! You can now open these files in Excel:")
    print("  - data/concerts_cleaned.csv (all concerts)")
    print("  - data/artist_statistics.csv (artist stats)")
    print("  - data/venue_statistics.csv (venue stats)")
    print("=" * 80)
