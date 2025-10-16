#!/usr/bin/env python3
"""
Fix concert 512 to have Mumford & Sons as headliner and Dawes as opener
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Could not use application default credentials: {e}")
            sys.exit(1)
    return firestore.client()

def fix_concert_512():
    """Update concert 512 to have separate Mumford & Sons and Dawes artists"""
    db = init_firebase()

    print("Fixing concert 512...")
    print("=" * 60)

    # Get concert 512
    concert_ref = db.collection('concerts').document('512')
    concert = concert_ref.get()

    if not concert.exists:
        print("ERROR: Concert 512 not found!")
        return

    concert_data = concert.to_dict()
    print(f"\nCurrent concert data:")
    print(f"  Date: {concert_data.get('date')}")
    print(f"  Venue: {concert_data.get('venue_name')}")
    print(f"  Artists: {concert_data.get('artists')}")

    # Update the artists array
    new_artists = [
        {
            'artist_id': '390',
            'artist_name': 'Mumford & Sons',
            'role': 'headliner',
            'position': 1
        },
        {
            'artist_id': '161',
            'artist_name': 'Dawes',
            'role': 'opener',
            'position': 2
        }
    ]

    print(f"\nUpdating concert 512 artists...")
    concert_ref.update({
        'artists': new_artists,
        'updated_at': firestore.SERVER_TIMESTAMP
    })
    print("  ✓ Concert 512 updated")

    # Delete artist 391 (Mumford and Sons with Dawes) since it's only used here
    print(f"\nDeleting old artist 391 (Mumford and Sons with Dawes)...")
    artist_ref = db.collection('artists').document('391')
    if artist_ref.get().exists:
        artist_ref.delete()
        print("  ✓ Deleted artist 391")
    else:
        print("  Artist 391 not found (may have been deleted already)")

    print(f"\n{'=' * 60}")
    print(f"Fix complete!")
    print(f"  Concert 512 now has:")
    print(f"    - Mumford & Sons (headliner)")
    print(f"    - Dawes (opener)")
    print(f"\nNext step: Run ./deploy.sh to export and deploy the updated data")

if __name__ == "__main__":
    fix_concert_512()
