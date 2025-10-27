#!/usr/bin/env python3
"""
Fix only the false positive setlist flags - concerts marked as having setlists but don't.
This correctly identifies which concerts have detail files and updates flags accordingly.
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

def fix_setlist_flags():
    """Set has_setlist based on existence of concert_details JSON files."""

    print("\n🔧 Fixing Setlist Flags Based on Actual Data")
    print("=" * 60)

    # Get list of concert IDs that have detail files
    details_dir = Path('website/data/concert_details')
    concert_ids_with_setlists = set()

    if details_dir.exists():
        for json_file in details_dir.glob('*.json'):
            concert_id = json_file.stem
            concert_ids_with_setlists.add(concert_id)

    print(f"Found {len(concert_ids_with_setlists)} concerts with setlist data files")

    # Get all concerts
    concerts_ref = db.collection('concerts')
    all_concerts = list(concerts_ref.stream())

    print(f"Total concerts in database: {len(all_concerts)}")

    batch = db.batch()
    batch_count = 0
    set_to_true = 0
    set_to_false = 0

    for concert_doc in all_concerts:
        concert_id = concert_doc.id
        data = concert_doc.to_dict()
        current_flag = data.get('has_setlist', False)

        # Correct flag: True if detail file exists, False otherwise
        should_have_flag = concert_id in concert_ids_with_setlists

        if current_flag != should_have_flag:
            batch.update(concert_doc.reference, {'has_setlist': should_have_flag})
            batch_count += 1

            if should_have_flag:
                set_to_true += 1
            else:
                set_to_false += 1

            # Commit batch every 500 updates
            if batch_count >= 500:
                batch.commit()
                batch = db.batch()
                batch_count = 0
                print(f"  Progress: {set_to_true} set to True, {set_to_false} set to False")

    # Commit remaining
    if batch_count > 0:
        batch.commit()

    print(f"\n✅ Fixed {set_to_true + set_to_false} concerts total")
    print(f"   - Set {set_to_true} to True (have setlists)")
    print(f"   - Set {set_to_false} to False (no setlists)")
    print("=" * 60)
    return set_to_true + set_to_false

if __name__ == '__main__':
    fixed = fix_setlist_flags()
    if fixed > 0:
        print("\nNext steps:")
        print("  1. Run: python3 scripts/export_to_web.py")
        print("  2. Deploy: firebase deploy --only hosting")
    else:
        print("\nNo fixes needed - all flags are accurate!")
