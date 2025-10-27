#!/usr/bin/env python3
"""
Revert has_setlist flags back to True for concerts that have concert_details JSON files.
This fixes the mistake where flags were incorrectly set to False.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
from pathlib import Path

if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'earplugs-and-memories'),
    })

db = firestore.client()

def revert_has_setlist_flags():
    """Set has_setlist=True for all concerts that have detail JSON files."""

    print("\n🔧 Reverting has_setlist Flags")
    print("=" * 60)

    # Get list of concert IDs that have detail files
    details_dir = Path('website/data/concert_details')
    concert_ids_with_details = set()

    if details_dir.exists():
        for json_file in details_dir.glob('*.json'):
            concert_id = json_file.stem
            concert_ids_with_details.add(concert_id)

    print(f"Found {len(concert_ids_with_details)} concerts with detail files")

    # Update Firestore
    batch = db.batch()
    count = 0
    reverted = 0

    for concert_id in concert_ids_with_details:
        concert_ref = db.collection('concerts').document(concert_id)
        concert_doc = concert_ref.get()

        if concert_doc.exists:
            data = concert_doc.to_dict()
            if not data.get('has_setlist', False):
                batch.update(concert_ref, {'has_setlist': True})
                reverted += 1
                count += 1

                # Commit batch every 500 updates
                if count >= 500:
                    batch.commit()
                    batch = db.batch()
                    count = 0
                    print(f"  Reverted {reverted} so far...")

    # Commit remaining
    if count > 0:
        batch.commit()

    print(f"\n✅ Reverted {reverted} concerts to has_setlist=True")
    print("=" * 60)
    return reverted

if __name__ == '__main__':
    reverted = revert_has_setlist_flags()
    if reverted > 0:
        print("\nNext steps:")
        print("  1. Run: python3 scripts/export_to_web.py")
        print("  2. Deploy: firebase deploy --only hosting")
