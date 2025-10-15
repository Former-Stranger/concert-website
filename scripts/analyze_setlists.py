#!/usr/bin/env python3
"""
Analyze setlist data to answer interesting questions
"""

import sqlite3
import sys
from pathlib import Path


class SetlistAnalyzer:
    """Analyze setlist patterns and statistics"""

    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()

    def most_common_closing_songs(self, artist_name=None, limit=10):
        """Find most common closing songs (overall or by artist)"""

        print("=" * 80)
        if artist_name:
            print(f"MOST COMMON CLOSING SONGS - {artist_name.upper()}")
        else:
            print("MOST COMMON CLOSING SONGS - ALL ARTISTS")
        print("=" * 80)

        query = '''
            SELECT
                ss.song_name,
                COUNT(*) as times,
                a.canonical_name as artist
            FROM setlist_songs ss
            JOIN setlists sl ON ss.setlist_id = sl.id
            JOIN concerts c ON sl.concert_id = c.id
            JOIN concert_artists ca ON c.id = ca.concert_id
            JOIN artists a ON ca.artist_id = a.id
            WHERE ss.position = (
                SELECT MAX(position)
                FROM setlist_songs ss2
                WHERE ss2.setlist_id = ss.setlist_id
            )
        '''

        if artist_name:
            query += ' AND LOWER(a.canonical_name) LIKE ?'
            self.cursor.execute(query + ' GROUP BY ss.song_name ORDER BY times DESC LIMIT ?',
                              (f'%{artist_name.lower()}%', limit))
        else:
            self.cursor.execute(query + ' GROUP BY ss.song_name, a.canonical_name ORDER BY times DESC LIMIT ?',
                              (limit,))

        results = self.cursor.fetchall()

        if not results:
            print("\nNo data found")
            return

        print()
        for i, (song, count, artist) in enumerate(results, 1):
            if artist_name:
                print(f"{i:2d}. {song:45s} - {count:2d} times")
            else:
                print(f"{i:2d}. {song:35s} by {artist:25s} - {count:2d} times")

    def most_common_opening_songs(self, artist_name=None, limit=10):
        """Find most common opening songs"""

        print("=" * 80)
        if artist_name:
            print(f"MOST COMMON OPENING SONGS - {artist_name.upper()}")
        else:
            print("MOST COMMON OPENING SONGS - ALL ARTISTS")
        print("=" * 80)

        query = '''
            SELECT
                ss.song_name,
                COUNT(*) as times,
                a.canonical_name as artist
            FROM setlist_songs ss
            JOIN setlists sl ON ss.setlist_id = sl.id
            JOIN concerts c ON sl.concert_id = c.id
            JOIN concert_artists ca ON c.id = ca.concert_id
            JOIN artists a ON ca.artist_id = a.id
            WHERE ss.position = 1
        '''

        if artist_name:
            query += ' AND LOWER(a.canonical_name) LIKE ?'
            self.cursor.execute(query + ' GROUP BY ss.song_name ORDER BY times DESC LIMIT ?',
                              (f'%{artist_name.lower()}%', limit))
        else:
            self.cursor.execute(query + ' GROUP BY ss.song_name, a.canonical_name ORDER BY times DESC LIMIT ?',
                              (limit,))

        results = self.cursor.fetchall()

        if not results:
            print("\nNo data found")
            return

        print()
        for i, (song, count, artist) in enumerate(results, 1):
            if artist_name:
                print(f"{i:2d}. {song:45s} - {count:2d} times")
            else:
                print(f"{i:2d}. {song:35s} by {artist:25s} - {count:2d} times")

    def most_common_encore_songs(self, artist_name=None, limit=10):
        """Find most common encore songs"""

        print("=" * 80)
        if artist_name:
            print(f"MOST COMMON ENCORE SONGS - {artist_name.upper()}")
        else:
            print("MOST COMMON ENCORE SONGS - ALL ARTISTS")
        print("=" * 80)

        query = '''
            SELECT
                ss.song_name,
                COUNT(*) as times,
                a.canonical_name as artist
            FROM setlist_songs ss
            JOIN setlists sl ON ss.setlist_id = sl.id
            JOIN concerts c ON sl.concert_id = c.id
            JOIN concert_artists ca ON c.id = ca.concert_id
            JOIN artists a ON ca.artist_id = a.id
            WHERE ss.encore > 0
        '''

        if artist_name:
            query += ' AND LOWER(a.canonical_name) LIKE ?'
            self.cursor.execute(query + ' GROUP BY ss.song_name ORDER BY times DESC LIMIT ?',
                              (f'%{artist_name.lower()}%', limit))
        else:
            self.cursor.execute(query + ' GROUP BY ss.song_name, a.canonical_name ORDER BY times DESC LIMIT ?',
                              (limit,))

        results = self.cursor.fetchall()

        if not results:
            print("\nNo data found")
            return

        print()
        for i, (song, count, artist) in enumerate(results, 1):
            if artist_name:
                print(f"{i:2d}. {song:45s} - {count:2d} times")
            else:
                print(f"{i:2d}. {song:35s} by {artist:25s} - {count:2d} times")

    def artist_setlist_stats(self, artist_name):
        """Show comprehensive stats for an artist"""

        print("=" * 80)
        print(f"SETLIST STATISTICS - {artist_name.upper()}")
        print("=" * 80)

        # Number of setlists
        self.cursor.execute('''
            SELECT COUNT(DISTINCT sl.id)
            FROM setlists sl
            JOIN concerts c ON sl.concert_id = c.id
            JOIN concert_artists ca ON c.id = ca.concert_id
            JOIN artists a ON ca.artist_id = a.id
            WHERE LOWER(a.canonical_name) LIKE ?
        ''', (f'%{artist_name.lower()}%',))

        setlist_count = self.cursor.fetchone()[0]

        if setlist_count == 0:
            print(f"\nNo setlist data found for {artist_name}")
            return

        print(f"\nSetlists available: {setlist_count}")

        # Average songs per show
        self.cursor.execute('''
            SELECT AVG(song_count)
            FROM setlists sl
            JOIN concerts c ON sl.concert_id = c.id
            JOIN concert_artists ca ON c.id = ca.concert_id
            JOIN artists a ON ca.artist_id = a.id
            WHERE LOWER(a.canonical_name) LIKE ?
        ''', (f'%{artist_name.lower()}%',))

        avg_songs = self.cursor.fetchone()[0]
        print(f"Average songs per show: {avg_songs:.1f}")

        # Encore percentage
        self.cursor.execute('''
            SELECT
                COUNT(CASE WHEN has_encore = 1 THEN 1 END) * 100.0 / COUNT(*) as encore_pct
            FROM setlists sl
            JOIN concerts c ON sl.concert_id = c.id
            JOIN concert_artists ca ON c.id = ca.concert_id
            JOIN artists a ON ca.artist_id = a.id
            WHERE LOWER(a.canonical_name) LIKE ?
        ''', (f'%{artist_name.lower()}%',))

        encore_pct = self.cursor.fetchone()[0]
        print(f"Shows with encores: {encore_pct:.0f}%")

        # Most played songs overall
        print("\n" + "=" * 80)
        print("MOST PLAYED SONGS")
        print("=" * 80)

        self.cursor.execute('''
            SELECT
                ss.song_name,
                COUNT(*) as times,
                COUNT(*) * 100.0 / ? as percentage
            FROM setlist_songs ss
            JOIN setlists sl ON ss.setlist_id = sl.id
            JOIN concerts c ON sl.concert_id = c.id
            JOIN concert_artists ca ON c.id = ca.concert_id
            JOIN artists a ON ca.artist_id = a.id
            WHERE LOWER(a.canonical_name) LIKE ?
            GROUP BY ss.song_name
            ORDER BY times DESC
            LIMIT 15
        ''', (setlist_count, f'%{artist_name.lower()}%'))

        print()
        for i, (song, count, pct) in enumerate(self.cursor.fetchall(), 1):
            print(f"{i:2d}. {song:45s} - {count:2d} times ({pct:5.1f}%)")

    def compare_opening_vs_closing(self, artist_name):
        """Compare songs that open vs close shows"""

        print("=" * 80)
        print(f"OPENING vs CLOSING SONGS - {artist_name.upper()}")
        print("=" * 80)

        # Songs that have opened shows
        self.cursor.execute('''
            SELECT
                ss.song_name,
                COUNT(*) as times
            FROM setlist_songs ss
            JOIN setlists sl ON ss.setlist_id = sl.id
            JOIN concerts c ON sl.concert_id = c.id
            JOIN concert_artists ca ON c.id = ca.concert_id
            JOIN artists a ON ca.artist_id = a.id
            WHERE LOWER(a.canonical_name) LIKE ?
              AND ss.position = 1
            GROUP BY ss.song_name
            ORDER BY times DESC
            LIMIT 5
        ''', (f'%{artist_name.lower()}%',))

        openers = self.cursor.fetchall()

        print("\nMost common opening songs:")
        for i, (song, count) in enumerate(openers, 1):
            print(f"  {i}. {song} ({count} times)")

        # Songs that have closed shows
        self.cursor.execute('''
            SELECT
                ss.song_name,
                COUNT(*) as times
            FROM setlist_songs ss
            JOIN setlists sl ON ss.setlist_id = sl.id
            JOIN concerts c ON sl.concert_id = c.id
            JOIN concert_artists ca ON c.id = ca.concert_id
            JOIN artists a ON ca.artist_id = a.id
            WHERE LOWER(a.canonical_name) LIKE ?
              AND ss.position = (
                  SELECT MAX(position)
                  FROM setlist_songs ss2
                  WHERE ss2.setlist_id = ss.setlist_id
              )
            GROUP BY ss.song_name
            ORDER BY times DESC
            LIMIT 5
        ''', (f'%{artist_name.lower()}%',))

        closers = self.cursor.fetchall()

        print("\nMost common closing songs:")
        for i, (song, count) in enumerate(closers, 1):
            print(f"  {i}. {song} ({count} times)")

    def most_covered_artists(self, limit=10):
        """Find which artists are covered most often"""

        print("=" * 80)
        print("MOST COVERED ARTISTS")
        print("=" * 80)

        self.cursor.execute('''
            SELECT
                cover_artist,
                COUNT(*) as times
            FROM setlist_songs
            WHERE is_cover = 1 AND cover_artist IS NOT NULL
            GROUP BY cover_artist
            ORDER BY times DESC
            LIMIT ?
        ''', (limit,))

        results = self.cursor.fetchall()

        if not results:
            print("\nNo cover data found")
            return

        print()
        for i, (artist, count) in enumerate(results, 1):
            print(f"{i:2d}. {artist:40s} - {count:2d} covers")


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    db_path = project_root / "database" / "concerts.db"

    analyzer = SetlistAnalyzer(db_path)

    if len(sys.argv) > 1:
        artist_name = ' '.join(sys.argv[1:])

        # Artist-specific analysis
        analyzer.artist_setlist_stats(artist_name)
        print()
        analyzer.most_common_opening_songs(artist_name)
        print()
        analyzer.most_common_closing_songs(artist_name)
        print()
        analyzer.most_common_encore_songs(artist_name)
        print()
        analyzer.compare_opening_vs_closing(artist_name)

    else:
        # Overall analysis
        analyzer.most_common_closing_songs()
        print()
        analyzer.most_common_opening_songs()
        print()
        analyzer.most_common_encore_songs()
        print()
        analyzer.most_covered_artists()

        print("\n" + "=" * 80)
        print("TIP: Run with artist name for artist-specific analysis")
        print("Example: python3 analyze_setlists.py 'Kip Moore'")
        print("=" * 80)

    analyzer.close()


if __name__ == "__main__":
    main()
