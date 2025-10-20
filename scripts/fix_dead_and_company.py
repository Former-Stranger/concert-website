#!/usr/bin/env python3
"""Fix Dead and Company artist name"""

import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'earplugs-and-memories'
    })

db = firestore.client()

def check_artist_131():
    """Check what artist ID 131 is"""
    artist_ref = db.collection('artists').document('131')
    artist = artist_ref.get()

    if artist.exists:
        data = artist.to_dict()
        print(f"Artist 131 current name: {data.get('name')}")
        return data
    else:
        print("Artist 131 does not exist")
        return None

def search_dead_and_company():
    """Search for Dead and Company artists"""
    print("\nSearching for 'Dead' artists...\n")

    artists_ref = db.collection('artists')
    all_artists = artists_ref.stream()

    found = []
    for doc in all_artists:
        artist = doc.to_dict()
        name = artist.get('name', '')
        if 'dead' in name.lower():
            found.append({
                'id': doc.id,
                'name': name
            })

    if found:
        print(f"Found {len(found)} artist(s) with 'Dead':")
        for artist in sorted(found, key=lambda x: x['name']):
            print(f"  - {artist['name']} (ID: {artist['id']})")

    return found

def fix_artist_131():
    """Fix artist 131 to be Dead and Company"""
    artist_ref = db.collection('artists').document('131')
    artist = artist_ref.get()

    if not artist.exists:
        print("Artist 131 does not exist!")
        return

    old_name = artist.to_dict().get('name')
    new_name = 'Dead and Company'

    print(f"\nUpdating artist 131:")
    print(f"  Old name: {old_name}")
    print(f"  New name: {new_name}")

    # Update the artist name
    artist_ref.update({'name': new_name})
    print("  ✓ Artist updated")

    # Find all concerts with this artist
    concerts_ref = db.collection('concerts')
    concerts = concerts_ref.where('artist_id', '==', '131').stream()

    concert_count = 0
    for concert in concerts:
        concert_ref = db.collection('concerts').document(concert.id)
        concert_ref.update({'artist_name': new_name})
        concert_count += 1

    print(f"  ✓ Updated {concert_count} concerts")

    print("\n✅ Fix complete!")

if __name__ == '__main__':
    print("=" * 60)
    print("Checking artist 131...")
    print("=" * 60)

    check_artist_131()
    search_dead_and_company()

    print("\n" + "=" * 60)
    print("Fixing artist 131...")
    print("=" * 60)

    fix_artist_131()
