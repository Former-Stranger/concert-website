#!/usr/bin/env python3
"""
Initialize setlist_status field for all concerts based on their hasSetlist flag.
- has_setlist if hasSetlist is True
- not_researched if hasSetlist is False or missing
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

db = firestore.client()

def initialize_setlist_status():
    print("Initializing setlist_status for all concerts...")
    print("=" * 60)

    # Get all concerts
    concerts_ref = db.collection('concerts')
    concerts = concerts_ref.stream()

    updated_count = 0
    has_setlist_count = 0
    not_researched_count = 0

    for concert in concerts:
        concert_data = concert.to_dict()
        concert_id = concert.id

        # Skip if setlist_status already exists
        if 'setlist_status' in concert_data:
            continue

        # Determine status based on hasSetlist flag
        has_setlist = concert_data.get('hasSetlist', False) or concert_data.get('has_setlist', False)
        status = 'has_setlist' if has_setlist else 'not_researched'

        # Update concert
        concerts_ref.document(concert_id).update({
            'setlist_status': status
        })

        updated_count += 1
        if status == 'has_setlist':
            has_setlist_count += 1
        else:
            not_researched_count += 1

        if updated_count % 100 == 0:
            print(f"Processed {updated_count} concerts...")

    print("=" * 60)
    print(f"✅ Initialized {updated_count} concerts")
    print(f"   - {has_setlist_count} with 'has_setlist' status")
    print(f"   - {not_researched_count} with 'not_researched' status")
    print("=" * 60)

if __name__ == '__main__':
    try:
        initialize_setlist_status()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
