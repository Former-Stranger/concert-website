#!/usr/bin/env python3
"""
Fix Mumford & Sons artist name in Firestore
The artist was incorrectly stored as "Mumford" instead of "Mumford & Sons"
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

def fix_mumford_artist():
    """Fix the Mumford artist name in Firestore"""
    db = init_firebase()

    print("Fixing Mumford & Sons artist name...")
    print("=" * 60)

    # 1. Find the Mumford artist (ID 390)
    artist_ref = db.collection('artists').document('390')
    artist_doc = artist_ref.get()

    if not artist_doc.exists:
        print("ERROR: Artist 390 not found!")
        return

    artist_data = artist_doc.to_dict()
    print(f"\nCurrent artist data:")
    print(f"  ID: 390")
    print(f"  Name: {artist_data.get('canonical_name')}")

    # 2. Update the artist canonical name
    print(f"\nUpdating artist canonical name to 'Mumford & Sons'...")
    artist_ref.update({
        'canonical_name': 'Mumford & Sons'
    })
    print("  ✓ Artist updated")

    # 3. Find all concerts with artist 522 ("Sons") and remove it from the artists array
    print(f"\nFinding concerts with 'Sons' artist (ID 522) and removing...")
    concerts_ref = db.collection('concerts')
    concerts = concerts_ref.stream()

    updated_concerts = 0
    for concert_doc in concerts:
        concert_data = concert_doc.to_dict()
        artists = concert_data.get('artists', [])

        # Check if this concert has artist 522 (Sons) - remove it
        updated_artists = []
        needs_update = False

        for artist in artists:
            # Skip artist 522 (Sons) - it's a duplicate/error
            if artist.get('artist_id') == '522':
                needs_update = True
                print(f"  Removing 'Sons' artist from concert {concert_doc.id}")
                continue
            updated_artists.append(artist)

        if needs_update:
            concert_doc.reference.update({
                'artists': updated_artists
            })
            updated_concerts += 1
            print(f"  ✓ Updated concert {concert_doc.id}")

    # 4. Delete the "Sons" artist (ID 522)
    print(f"\nDeleting 'Sons' artist (ID 522)...")
    sons_artist_ref = db.collection('artists').document('522')
    if sons_artist_ref.get().exists:
        sons_artist_ref.delete()
        print(f"  ✓ Deleted artist 522")
    else:
        print(f"  Artist 522 not found (may have been deleted already)")

    print(f"\n{'=' * 60}")
    print(f"Fix complete!")
    print(f"  Updated 'Mumford & Sons' artist: 390")
    print(f"  Removed 'Sons' from concerts: {updated_concerts}")
    print(f"  Deleted 'Sons' artist: 522")
    print(f"\nNext step: Run ./deploy.sh to export and deploy the updated data")

if __name__ == "__main__":
    fix_mumford_artist()
