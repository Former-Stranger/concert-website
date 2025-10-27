#!/usr/bin/env python3
"""
Sync has_setlist flags in Firestore to match actual concert_details file existence.
This fixes the 379 concerts that are marked as having setlists but don't have data.
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

def sync_has_setlist_flags():
    """Set has_setlist based on actual existence of concert_details files."""

    print("\n🔧 Syncing has_setlist Flags with Actual Data Files")
    print("=" * 60)

    # Get list of concert IDs that have detail files (actual setlist data)
    details_dir = Path('website/data/concert_details')
    concert_ids_with_setlists = set()

    if details_dir.exists():
        for json_file in details_dir.glob('*.json'):
            concert_id = json_file.stem
            concert_ids_with_setlists.add(concert_id)

    print(f"Found {len(concert_ids_with_setlists)} concerts with actual setlist data files")

    # Get all concerts from Firestore
    concerts_ref = db.collection('concerts')
    all_concerts = list(concerts_ref.stream())

    print(f"Total concerts in database: {len(all_concerts)}")

    batch = db.batch()
    batch_count = 0
    set_to_false = 0
    already_correct = 0

    for concert_doc in all_concerts:
        concert_id = concert_doc.id
        data = concert_doc.to_dict()
        current_flag = data.get('has_setlist', False)

        # True only if detail file exists
        should_be_true = concert_id in concert_ids_with_setlists

        if current_flag and not should_be_true:
            # Currently marked as having setlist but doesn't - fix it
            batch.update(concert_doc.reference, {'has_setlist': False})
            batch_count += 1
            set_to_false += 1

            # Commit batch every 500 updates
            if batch_count >= 500:
                batch.commit()
                batch = db.batch()
                batch_count = 0
                print(f"  Progress: {set_to_false} set to False so far...")
        elif not current_flag and should_be_true:
            # Currently not marked but has data - fix it
            batch.update(concert_doc.reference, {'has_setlist': True})
            batch_count += 1
            print(f"  Found concert {concert_id} with data but not marked - fixing")
        else:
            already_correct += 1

    # Commit remaining
    if batch_count > 0:
        batch.commit()

    print(f"\n✅ Updated {set_to_false} concerts to has_setlist=False")
    print(f"   {already_correct} concerts were already correct")
    print(f"   Final state: {len(concert_ids_with_setlists)} with setlists, "
          f"{len(all_concerts) - len(concert_ids_with_setlists)} without")
    print("=" * 60)
    return set_to_false

if __name__ == '__main__':
    fixed = sync_has_setlist_flags()
    if fixed > 0:
        print("\nNext steps:")
        print("  1. Run: python3 scripts/export_to_web.py")
        print("  2. Deploy: firebase deploy --only hosting")
    else:
        print("\nNo fixes needed - all flags match actual data!")
