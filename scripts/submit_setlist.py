#!/usr/bin/env python3
"""
Script to submit a setlist from setlist.fm for admin approval.
Usage: python submit_setlist.py <concert_id> <setlistfm_url> [submitter_email] [submitter_name]
"""

import sys
import sqlite3
import requests
import json
import re
from datetime import datetime

SETLISTFM_API_KEY = "DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE"
DB_PATH = "database/concerts.db"

def extract_setlist_id(url):
    """Extract setlist ID from setlist.fm URL"""
    # URL format: https://www.setlist.fm/setlist/artist/year/venue-city-state-ID.html
    match = re.search(r'-([a-zA-Z0-9]+)\.html$', url)
    if match:
        return match.group(1)
    return None

def fetch_setlist_data(setlist_id):
    """Fetch setlist data from setlist.fm API"""
    url = f"https://api.setlist.fm/rest/1.0/setlist/{setlist_id}"
    headers = {
        "x-api-key": SETLISTFM_API_KEY,
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        print(f"Error: Setlist not found on setlist.fm (ID: {setlist_id})")
        return None
    else:
        print(f"Error fetching setlist: HTTP {response.status_code}")
        print(response.text)
        return None

def validate_concert(conn, concert_id):
    """Check if concert exists and doesn't already have a setlist"""
    cursor = conn.cursor()

    # Check if concert exists
    cursor.execute("SELECT id FROM concerts WHERE id = ?", (concert_id,))
    if not cursor.fetchone():
        print(f"Error: Concert ID {concert_id} not found")
        return False

    # Check if concert already has a setlist
    cursor.execute("SELECT id FROM setlists WHERE concert_id = ?", (concert_id,))
    if cursor.fetchone():
        print(f"Error: Concert ID {concert_id} already has a setlist")
        return False

    # Check if there's already a pending submission
    cursor.execute(
        "SELECT id FROM pending_setlist_submissions WHERE concert_id = ? AND status = 'pending'",
        (concert_id,)
    )
    if cursor.fetchone():
        print(f"Error: Concert ID {concert_id} already has a pending submission")
        return False

    return True

def store_pending_submission(conn, concert_id, setlistfm_url, setlistfm_id, setlist_data,
                            submitter_email=None, submitter_name=None):
    """Store the pending setlist submission in the database"""
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pending_setlist_submissions
        (concert_id, setlistfm_url, setlistfm_id, submitted_by_email, submitted_by_name, setlist_data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        concert_id,
        setlistfm_url,
        setlistfm_id,
        submitter_email,
        submitter_name,
        json.dumps(setlist_data)
    ))

    conn.commit()
    return cursor.lastrowid

def main():
    if len(sys.argv) < 3:
        print("Usage: python submit_setlist.py <concert_id> <setlistfm_url> [submitter_email] [submitter_name]")
        sys.exit(1)

    concert_id = int(sys.argv[1])
    setlistfm_url = sys.argv[2]
    submitter_email = sys.argv[3] if len(sys.argv) > 3 else None
    submitter_name = sys.argv[4] if len(sys.argv) > 4 else None

    # Extract setlist ID from URL
    setlist_id = extract_setlist_id(setlistfm_url)
    if not setlist_id:
        print(f"Error: Could not extract setlist ID from URL: {setlistfm_url}")
        sys.exit(1)

    print(f"Extracted setlist ID: {setlist_id}")

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    try:
        # Validate concert
        if not validate_concert(conn, concert_id):
            sys.exit(1)

        # Fetch setlist data
        print("Fetching setlist data from setlist.fm...")
        setlist_data = fetch_setlist_data(setlist_id)

        if not setlist_data:
            sys.exit(1)

        print(f"Successfully fetched setlist for {setlist_data['artist']['name']}")
        print(f"Date: {setlist_data['eventDate']}")
        print(f"Venue: {setlist_data['venue']['name']}")

        # Count songs
        song_count = 0
        if 'sets' in setlist_data and 'set' in setlist_data['sets']:
            for set_group in setlist_data['sets']['set']:
                if 'song' in set_group:
                    song_count += len(set_group['song'])

        print(f"Total songs: {song_count}")

        # Store pending submission
        submission_id = store_pending_submission(
            conn, concert_id, setlistfm_url, setlist_id, setlist_data,
            submitter_email, submitter_name
        )

        print(f"\n✓ Submission successful! Pending approval (ID: {submission_id})")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
