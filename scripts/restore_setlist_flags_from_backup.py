#!/usr/bin/env python3
"""
Restore has_setlist flags in Firestore from the backup concerts.json file.
This undoes the incorrect changes that removed setlist flags from 379 concerts.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json
from pathlib import Path
import os

if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'earplugs-and-memories'),
    })

db = firestore.client()

def restore_setlist_flags():
    """Restore has_setlist flags from concerts.json backup."""

    print("\n🔄 Restoring has_setlist Flags from Backup")
    print("=" * 60)

    # Load the restored concerts.json
    concerts_file = Path('website/data/concerts.json')
    with open(concerts_file) as f:
        concerts_data = json.load(f)

    print(f"Loaded {len(concerts_data)} concerts from backup")

    # Create a mapping of concert ID to hasSetlist flag
    setlist_flags = {c['id']: c.get('hasSetlist', False) for c in concerts_data}

    # Count what we expect
    expected_true = sum(1 for v in setlist_flags.values() if v)
    expected_false = len(setlist_flags) - expected_true
    print(f"Expected: {expected_true} with setlists, {expected_false} without")

    # Update Firestore
    batch = db.batch()
    batch_count = 0
    updated = 0
    set_to_true = 0
    set_to_false = 0

    for concert_id, should_have_setlist in setlist_flags.items():
        concert_ref = db.collection('concerts').document(concert_id)
        concert_doc = concert_ref.get()

        if concert_doc.exists:
            current_data = concert_doc.to_dict()
            current_flag = current_data.get('has_setlist', False)

            if current_flag != should_have_setlist:
                batch.update(concert_ref, {'has_setlist': should_have_setlist})
                batch_count += 1
                updated += 1

                if should_have_setlist:
                    set_to_true += 1
                else:
                    set_to_false += 1

                # Commit batch every 500 updates
                if batch_count >= 500:
                    batch.commit()
                    batch = db.batch()
                    batch_count = 0
                    print(f"  Progress: {updated} updated so far...")

    # Commit remaining
    if batch_count > 0:
        batch.commit()

    print(f"\n✅ Restored {updated} concerts")
    print(f"   - Set {set_to_true} to True (restored setlist flags)")
    print(f"   - Set {set_to_false} to False")
    print("=" * 60)
    return updated

if __name__ == '__main__':
    restored = restore_setlist_flags()
    if restored > 0:
        print("\nData restored successfully!")
        print("Changes have been applied to Firestore.")
        print("\nThe website should now show setlists correctly.")
    else:
        print("\nNo changes needed - database already matches backup!")
