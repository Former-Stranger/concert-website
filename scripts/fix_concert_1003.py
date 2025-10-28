#!/usr/bin/env python3
"""
Fix Concert 1003 - John Henry's Friends Benefit

This concert currently has all artists in one field:
  "Bruce Springsteen + Earle + Nile + Cash (7th Annual J. Henry)"

Should be split into:
  Festival: John Henry's Friends
  Artists:
    - Bruce Springsteen
    - Steve Earle
    - Willie Nile
    - Rosanne Cash
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys
import os

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'earplugs-and-memories'),
            })
        except Exception as e:
            print(f"Could not use application default credentials: {e}")
            sys.exit(1)

def fix_concert_1003():
    """Fix concert 1003 structure"""

    print("\n" + "="*80)
    print("FIXING CONCERT 1003 - JOHN HENRY'S FRIENDS BENEFIT")
    print("="*80)

    init_firebase()
    db = firestore.client()

    # Get concert 1003
    concert_ref = db.collection('concerts').document('1003')
    concert_doc = concert_ref.get()

    if not concert_doc.exists:
        print("ERROR: Concert 1003 not found!")
        return

    data = concert_doc.to_dict()

    print("\nCurrent state:")
    print(f"  Festival Name: {data.get('festival_name')}")
    print(f"  Artists: {data.get('artists')}")

    print("\nNew structure:")
    print(f"  Festival Name: John Henry's Friends")
    print(f"  Artists:")
    print(f"    1. Bruce Springsteen (festival_performer)")
    print(f"    2. Steve Earle (festival_performer)")
    print(f"    3. Willie Nile (festival_performer)")
    print(f"    4. Rosanne Cash (festival_performer)")

    response = input("\nApply this fix? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return

    # Get artist IDs from the artists collection
    artists_lookup = {
        'Bruce Springsteen': None,
        'Steve Earle': None,
        'Willie Nile': None,
        'Rosanne Cash': None
    }

    # Find artist IDs
    for artist_name in artists_lookup.keys():
        # Try to find by canonical name
        artists_query = db.collection('artists').where('canonical_name', '==', artist_name).limit(1).stream()
        for artist_doc in artists_query:
            artists_lookup[artist_name] = artist_doc.id
            print(f"  Found {artist_name}: ID {artist_doc.id}")
            break

    # If we didn't find some artists, search by aliases
    for artist_name, artist_id in artists_lookup.items():
        if artist_id is None:
            # Search in aliases
            all_artists = db.collection('artists').stream()
            for artist_doc in all_artists:
                artist_data = artist_doc.to_dict()
                canonical = artist_data.get('canonical_name', '')
                aliases = artist_data.get('aliases', [])

                if artist_name.lower() in canonical.lower() or \
                   any(artist_name.lower() in alias.lower() for alias in aliases):
                    artists_lookup[artist_name] = artist_doc.id
                    print(f"  Found {artist_name}: ID {artist_doc.id}")
                    break

    # Create new artists array
    new_artists = []
    position = 1

    for artist_name in ['Bruce Springsteen', 'Steve Earle', 'Willie Nile', 'Rosanne Cash']:
        artist_id = artists_lookup.get(artist_name)
        if not artist_id:
            print(f"\n  WARNING: Could not find artist ID for {artist_name}")
            print(f"  Will use placeholder - you may need to fix this manually")
            artist_id = "0"  # Placeholder

        new_artists.append({
            'artist_id': artist_id,
            'artist_name': artist_name,
            'position': position,
            'role': 'festival_performer'
        })
        position += 1

    # Update the concert
    concert_ref.update({
        'festival_name': "John Henry's Friends",
        'artists': new_artists
    })

    print("\n✓ Concert 1003 updated successfully!")
    print("\nNew data:")
    updated_doc = concert_ref.get()
    updated_data = updated_doc.to_dict()
    print(f"  Festival Name: {updated_data.get('festival_name')}")
    print(f"  Artists:")
    for artist in updated_data.get('artists', []):
        print(f"    - {artist.get('artist_name')} (ID: {artist.get('artist_id')}, {artist.get('role')})")

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("1. Run: python3 scripts/export_to_web.py")
    print("2. Deploy: firebase deploy --only hosting")

if __name__ == '__main__':
    fix_concert_1003()
