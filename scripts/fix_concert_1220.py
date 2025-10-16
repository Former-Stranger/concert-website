#!/usr/bin/env python3
"""
Fix concert 1220 to have Dave Matthews Band as artist and SOULSHINE as festival name
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

def fix_concert_1220():
    """Update concert 1220 to have Dave Matthews Band and SOULSHINE festival"""
    db = init_firebase()

    print("Fixing concert 1220...")
    print("=" * 60)

    # Get concert 1220
    concert_ref = db.collection('concerts').document('1220')
    concert = concert_ref.get()

    if not concert.exists:
        print("ERROR: Concert 1220 not found!")
        return

    concert_data = concert.to_dict()
    print(f"\nCurrent concert data:")
    print(f"  Date: {concert_data.get('date')}")
    print(f"  Venue: {concert_data.get('venue_name')}")
    print(f"  Festival: {concert_data.get('festival_name')}")
    print(f"  Artists: {concert_data.get('artists')}")

    # Update the concert
    new_artists = [
        {
            'artist_id': '155',
            'artist_name': 'Dave Matthews Band',
            'role': 'headliner',
            'position': 1
        }
    ]

    print(f"\nUpdating concert 1220...")
    concert_ref.update({
        'artists': new_artists,
        'festival_name': 'SOULSHINE',
        'updated_at': firestore.SERVER_TIMESTAMP
    })
    print("  ✓ Concert 1220 updated")

    print(f"\n{'=' * 60}")
    print(f"Fix complete!")
    print(f"  Concert 1220 now has:")
    print(f"    - Artist: Dave Matthews Band")
    print(f"    - Festival: SOULSHINE")
    print(f"\nNext step: Run ./deploy.sh to export and deploy the updated data")

if __name__ == "__main__":
    fix_concert_1220()
