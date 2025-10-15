#!/usr/bin/env python3
"""
Script to review and approve/reject pending setlist submissions.
Usage:
  List pending: python review_setlist_submissions.py list
  View detail: python review_setlist_submissions.py view <submission_id>
  Approve: python review_setlist_submissions.py approve <submission_id> <reviewer_email>
  Reject: python review_setlist_submissions.py reject <submission_id> <reviewer_email> <reason>
"""

import sys
import sqlite3
import json
from datetime import datetime

DB_PATH = "database/concerts.db"

def list_pending_submissions(conn):
    """List all pending submissions"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            ps.id,
            ps.concert_id,
            ps.setlistfm_url,
            ps.submitted_by_email,
            ps.submitted_by_name,
            ps.submitted_at,
            c.date as concert_date,
            GROUP_CONCAT(a.canonical_name, ', ') as artists,
            v.canonical_name as venue
        FROM pending_setlist_submissions ps
        JOIN concerts c ON ps.concert_id = c.id
        JOIN venues v ON c.venue_id = v.id
        LEFT JOIN concert_artists ca ON c.id = ca.concert_id
        LEFT JOIN artists a ON ca.artist_id = a.id
        WHERE ps.status = 'pending'
        GROUP BY ps.id
        ORDER BY ps.submitted_at DESC
    """)

    submissions = cursor.fetchall()

    if not submissions:
        print("No pending submissions.")
        return

    print("\n" + "="*80)
    print("PENDING SETLIST SUBMISSIONS")
    print("="*80)

    for sub in submissions:
        print(f"\nSubmission ID: {sub[0]}")
        print(f"Concert ID: {sub[1]}")
        print(f"Concert: {sub[7]} @ {sub[8]} ({sub[6]})")
        print(f"Setlist.fm URL: {sub[2]}")
        print(f"Submitted by: {sub[4]} ({sub[3]})" if sub[3] else f"Submitted by: Anonymous")
        print(f"Submitted at: {sub[5]}")
        print("-" * 80)

    print(f"\nTotal pending: {len(submissions)}")

def view_submission_detail(conn, submission_id):
    """View detailed information about a specific submission"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            ps.id,
            ps.concert_id,
            ps.setlistfm_url,
            ps.setlistfm_id,
            ps.submitted_by_email,
            ps.submitted_by_name,
            ps.submitted_at,
            ps.status,
            ps.setlist_data,
            c.date as concert_date,
            GROUP_CONCAT(a.canonical_name, ', ') as artists,
            v.canonical_name as venue,
            v.city,
            v.state
        FROM pending_setlist_submissions ps
        JOIN concerts c ON ps.concert_id = c.id
        JOIN venues v ON c.venue_id = v.id
        LEFT JOIN concert_artists ca ON c.id = ca.concert_id
        LEFT JOIN artists a ON ca.artist_id = a.id
        WHERE ps.id = ?
        GROUP BY ps.id
    """, (submission_id,))

    row = cursor.fetchone()

    if not row:
        print(f"Submission ID {submission_id} not found.")
        return

    setlist_data = json.loads(row[8])  # setlist_data column

    print("\n" + "="*80)
    print(f"SUBMISSION DETAILS - ID: {submission_id}")
    print("="*80)
    print(f"\nConcert Information:")
    print(f"  Concert ID: {row[1]}")
    print(f"  Date: {row[9]}")
    print(f"  Artists: {row[10]}")
    print(f"  Venue: {row[11]}, {row[12]}, {row[13]}")

    print(f"\nSubmission Information:")
    print(f"  Setlist.fm URL: {row[2]}")
    print(f"  Setlist.fm ID: {row[3]}")
    print(f"  Submitted by: {row[5]} ({row[4]})" if row[4] else "  Submitted by: Anonymous")
    print(f"  Submitted at: {row[6]}")
    print(f"  Status: {row[7]}")

    print(f"\nSetlist from setlist.fm:")
    print(f"  Artist: {setlist_data['artist']['name']}")
    print(f"  Date: {setlist_data['eventDate']}")
    print(f"  Venue: {setlist_data['venue']['name']}, {setlist_data['venue']['city']['name']}")

    if 'sets' in setlist_data and 'set' in setlist_data['sets']:
        print(f"\n  Songs:")
        position = 1
        for set_group in setlist_data['sets']['set']:
            set_name = set_group.get('name', f"Set {position}")
            if set_group.get('encore'):
                set_name = f"Encore {set_group.get('encore')}"

            print(f"\n  {set_name}")

            if 'song' in set_group:
                for song in set_group['song']:
                    song_name = song['name']
                    extra_info = []

                    if song.get('info'):
                        extra_info.append(song['info'])
                    if song.get('cover'):
                        extra_info.append(f"cover of {song['cover']['name']}")
                    if song.get('tape'):
                        extra_info.append("(tape)")

                    suffix = f" ({', '.join(extra_info)})" if extra_info else ""
                    print(f"    {position}. {song_name}{suffix}")
                    position += 1

    print("\n" + "="*80)

def approve_submission(conn, submission_id, reviewer_email):
    """Approve a submission and import setlist into database"""
    cursor = conn.cursor()

    # Get submission data
    cursor.execute("""
        SELECT concert_id, setlistfm_url, setlistfm_id, setlist_data
        FROM pending_setlist_submissions
        WHERE id = ? AND status = 'pending'
    """, (submission_id,))

    row = cursor.fetchone()

    if not row:
        print(f"Submission ID {submission_id} not found or not pending.")
        return False

    concert_id, setlistfm_url, setlistfm_id, setlist_data_json = row
    setlist_data = json.loads(setlist_data_json)

    try:
        # Insert into setlists table
        song_count = 0
        has_encore = False

        if 'sets' in setlist_data and 'set' in setlist_data['sets']:
            for set_group in setlist_data['sets']['set']:
                if set_group.get('encore'):
                    has_encore = True
                if 'song' in set_group:
                    song_count += len(set_group['song'])

        cursor.execute("""
            INSERT INTO setlists (concert_id, setlistfm_id, setlistfm_url, song_count, has_encore)
            VALUES (?, ?, ?, ?, ?)
        """, (concert_id, setlistfm_id, setlistfm_url, song_count, has_encore))

        setlist_id = cursor.lastrowid

        # Insert songs
        position = 1
        if 'sets' in setlist_data and 'set' in setlist_data['sets']:
            for set_group in setlist_data['sets']['set']:
                set_name = set_group.get('name', '')
                encore = set_group.get('encore', 0)

                if 'song' in set_group:
                    for song in set_group['song']:
                        song_name = song['name']
                        is_cover = 'cover' in song
                        cover_artist = song['cover']['name'] if is_cover else None
                        is_tape = song.get('tape', False)
                        info = song.get('info', None)

                        cursor.execute("""
                            INSERT INTO setlist_songs
                            (setlist_id, position, song_name, set_name, encore, is_cover, cover_artist, is_tape, info)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (setlist_id, position, song_name, set_name, encore, is_cover, cover_artist, is_tape, info))

                        position += 1

        # Update submission status
        cursor.execute("""
            UPDATE pending_setlist_submissions
            SET status = 'approved',
                reviewed_by_email = ?,
                reviewed_at = ?
            WHERE id = ?
        """, (reviewer_email, datetime.now().isoformat(), submission_id))

        conn.commit()

        print(f"\n✓ Submission {submission_id} approved!")
        print(f"  Imported {song_count} songs into setlist for concert ID {concert_id}")
        return True

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Error approving submission: {e}")
        return False

def reject_submission(conn, submission_id, reviewer_email, reason):
    """Reject a submission"""
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE pending_setlist_submissions
        SET status = 'rejected',
            reviewed_by_email = ?,
            reviewed_at = ?,
            review_notes = ?
        WHERE id = ? AND status = 'pending'
    """, (reviewer_email, datetime.now().isoformat(), reason, submission_id))

    if cursor.rowcount == 0:
        print(f"Submission ID {submission_id} not found or not pending.")
        return False

    conn.commit()
    print(f"\n✓ Submission {submission_id} rejected.")
    print(f"  Reason: {reason}")
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  List pending: python review_setlist_submissions.py list")
        print("  View detail: python review_setlist_submissions.py view <submission_id>")
        print("  Approve: python review_setlist_submissions.py approve <submission_id> <reviewer_email>")
        print("  Reject: python review_setlist_submissions.py reject <submission_id> <reviewer_email> <reason>")
        sys.exit(1)

    command = sys.argv[1]
    conn = sqlite3.connect(DB_PATH)

    try:
        if command == "list":
            list_pending_submissions(conn)

        elif command == "view":
            if len(sys.argv) < 3:
                print("Error: submission_id required")
                sys.exit(1)
            submission_id = int(sys.argv[2])
            view_submission_detail(conn, submission_id)

        elif command == "approve":
            if len(sys.argv) < 4:
                print("Error: submission_id and reviewer_email required")
                sys.exit(1)
            submission_id = int(sys.argv[2])
            reviewer_email = sys.argv[3]
            approve_submission(conn, submission_id, reviewer_email)

        elif command == "reject":
            if len(sys.argv) < 5:
                print("Error: submission_id, reviewer_email, and reason required")
                sys.exit(1)
            submission_id = int(sys.argv[2])
            reviewer_email = sys.argv[3]
            reason = " ".join(sys.argv[4:])
            reject_submission(conn, submission_id, reviewer_email, reason)

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    finally:
        conn.close()

if __name__ == "__main__":
    main()
