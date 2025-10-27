#!/usr/bin/env python3
"""
Fix has_setlist flags in concerts collection to match actual setlist existence.
This resolves the issue where concerts show setlist indicators but have no setlist data.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os

if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'earplugs-and-memories'),
    })

db = firestore.client()

def fix_has_setlist_flags():
    """Update has_setlist flags to match actual setlist existence."""

    print("\n🔧 Fixing has_setlist Flags")
    print("=" * 60)

    # Get all concerts
    concerts_ref = db.collection('concerts')
    concerts = list(concerts_ref.stream())

    # Get all setlists
    setlists_ref = db.collection('setlists')
    setlists = {doc.id: doc.to_dict() for doc in setlists_ref.stream()}

    fixed_count = 0
    false_positives = []  # Concerts marked as having setlists but don't
    false_negatives = []  # Concerts not marked but do have setlists

    for concert_doc in concerts:
        concert_id = concert_doc.id
        concert_data = concert_doc.to_dict()
        current_flag = concert_data.get('has_setlist', False)

        # Check if setlist actually exists with songs
        has_actual_setlist = False
        if concert_id in setlists:
            songs = setlists[concert_id].get('songs', [])
            has_actual_setlist = len(songs) > 0

        # Fix if mismatch
        if current_flag != has_actual_setlist:
            concert_doc.reference.update({'has_setlist': has_actual_setlist})
            fixed_count += 1

            if current_flag and not has_actual_setlist:
                false_positives.append({
                    'id': concert_id,
                    'date': concert_data.get('date'),
                    'venue': concert_data.get('venue_name'),
                    'artists': ', '.join([a.get('artist_name', '') for a in concert_data.get('artists', [])])
                })
            elif not current_flag and has_actual_setlist:
                false_negatives.append({
                    'id': concert_id,
                    'date': concert_data.get('date'),
                    'venue': concert_data.get('venue_name')
                })

    print(f"\n✅ Fixed {fixed_count} concerts")

    if false_positives:
        print(f"\n📉 False Positives (marked as having setlist but don't): {len(false_positives)}")
        for concert in false_positives[:10]:  # Show first 10
            print(f"  - {concert['id']}: {concert['date']} - {concert['artists']} at {concert['venue']}")
        if len(false_positives) > 10:
            print(f"  ... and {len(false_positives) - 10} more")

    if false_negatives:
        print(f"\n📈 False Negatives (not marked but have setlist): {len(false_negatives)}")
        for concert in false_negatives[:10]:  # Show first 10
            print(f"  - {concert['id']}: {concert['date']} at {concert['venue']}")
        if len(false_negatives) > 10:
            print(f"  ... and {len(false_negatives) - 10} more")

    print("\n" + "=" * 60)
    return fixed_count

if __name__ == '__main__':
    fixed = fix_has_setlist_flags()
    if fixed > 0:
        print("\nNext steps:")
        print("  1. Run: python3 scripts/export_to_web.py")
        print("  2. Deploy: firebase deploy --only hosting")
    else:
        print("\nNo fixes needed - all flags are accurate!")
