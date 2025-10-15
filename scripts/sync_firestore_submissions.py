#!/usr/bin/env python3
"""
Script to sync pending setlist submissions from Firestore to SQLite database.
This allows the review_setlist_submissions.py script to work with web submissions.

Usage: python sync_firestore_submissions.py
"""

import sys
import sqlite3
import json
import requests
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

DB_PATH = "database/concerts.db"
SETLISTFM_API_KEY = "DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE"

def init_firebase():
    """Initialize Firebase Admin SDK"""
    # Check if already initialized
    try:
        firebase_admin.get_app()
    except ValueError:
        # Initialize with default credentials (looks for GOOGLE_APPLICATION_CREDENTIALS env var
        # or uses Application Default Credentials)
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)

    return firestore.client()

def fetch_setlist_data(setlist_id):
    """Fetch setlist data from setlist.fm API"""
    url = f"https://api.setlist.fm/rest/1.0/setlist/{setlist_id}"
    headers = {
        "x-api-key": SETLISTFM_API_KEY,
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"    Warning: Could not fetch setlist data (HTTP {response.status_code})")
            return None
    except Exception as e:
        print(f"    Warning: Error fetching setlist data: {e}")
        return None

def sync_submissions():
    """Sync submissions from Firestore to SQLite"""
    print("Initializing Firebase...")
    db_firestore = init_firebase()

    print("Connecting to SQLite database...")
    db_sqlite = sqlite3.connect(DB_PATH)
    cursor = db_sqlite.cursor()

    try:
        # Get all pending submissions from Firestore
        print("Fetching pending submissions from Firestore...")
        submissions_ref = db_firestore.collection('pending_setlist_submissions')
        submissions = submissions_ref.where('status', '==', 'pending').get()

        if not submissions:
            print("No pending submissions found in Firestore.")
            return

        print(f"Found {len(submissions)} pending submissions in Firestore")

        synced_count = 0
        skipped_count = 0

        for doc in submissions:
            data = doc.to_dict()

            concert_id = data.get('concertId')
            setlistfm_url = data.get('setlistfmUrl')
            setlistfm_id = data.get('setlistfmId')
            submitted_by_email = data.get('submittedByEmail', 'anonymous')
            submitted_by_name = data.get('submittedByName', 'Anonymous')
            submitted_at = data.get('submittedAt')

            # Fetch setlist data from API if not already in Firestore
            setlist_data = data.get('setlistData')
            if not setlist_data:
                print(f"  Fetching setlist data for {setlistfm_id}...")
                setlist_data = fetch_setlist_data(setlistfm_id)
                if not setlist_data:
                    print(f"  ⚠ Skipping concert {concert_id} - could not fetch setlist data")
                    skipped_count += 1
                    continue

            # Convert Firestore timestamp to ISO string
            if hasattr(submitted_at, 'isoformat'):
                submitted_at_str = submitted_at.isoformat()
            elif isinstance(submitted_at, datetime):
                submitted_at_str = submitted_at.isoformat()
            else:
                submitted_at_str = datetime.now().isoformat()

            # Check if already exists in SQLite
            cursor.execute("""
                SELECT id FROM pending_setlist_submissions
                WHERE concert_id = ? AND setlistfm_id = ?
            """, (concert_id, setlistfm_id))

            if cursor.fetchone():
                print(f"  Skipping concert {concert_id} - already in SQLite")
                skipped_count += 1
                continue

            # Insert into SQLite
            cursor.execute("""
                INSERT INTO pending_setlist_submissions
                (concert_id, setlistfm_url, setlistfm_id, submitted_by_email,
                 submitted_by_name, submitted_at, status, setlist_data)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
            """, (
                concert_id,
                setlistfm_url,
                setlistfm_id,
                submitted_by_email,
                submitted_by_name,
                submitted_at_str,
                json.dumps(setlist_data) if isinstance(setlist_data, dict) else setlist_data
            ))

            print(f"  ✓ Synced submission for concert {concert_id} from {submitted_by_name}")
            synced_count += 1

        db_sqlite.commit()

        print(f"\n✓ Sync complete!")
        print(f"  Synced: {synced_count}")
        print(f"  Skipped (already exists): {skipped_count}")

    except Exception as e:
        db_sqlite.rollback()
        print(f"\n✗ Error during sync: {e}")
        raise

    finally:
        db_sqlite.close()

if __name__ == "__main__":
    try:
        sync_submissions()
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
