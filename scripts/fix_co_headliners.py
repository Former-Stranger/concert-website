#!/usr/bin/env python3
"""
Fix concerts with co-headliners that are currently stored as a single artist with "/" separator.

For example: "Rod Stewart/Cyndi Lauper" should be split into:
  - Rod Stewart (role: headliner, position: 1)
  - Cyndi Lauper (role: headliner, position: 2)
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys
import os
import re

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

def find_artist_id(db, artist_name):
    """Find artist ID by name"""
    # Try exact match first
    artists = db.collection('artists').where('canonical_name', '==', artist_name).limit(1).stream()
    for artist_doc in artists:
        return artist_doc.id

    # Try case-insensitive search
    all_artists = db.collection('artists').stream()
    for artist_doc in all_artists:
        data = artist_doc.to_dict()
        canonical = data.get('canonical_name', '').lower()
        aliases = [a.lower() for a in data.get('aliases', [])]

        if artist_name.lower() == canonical or artist_name.lower() in aliases:
            return artist_doc.id

    return None

def fix_concert_847():
    """Fix concert 847 - Rod Stewart/Cyndi Lauper co-headliner show"""

    print("\n" + "="*80)
    print("FIXING CONCERT 847 - ROD STEWART / CYNDI LAUPER CO-HEADLINERS")
    print("="*80)

    init_firebase()
    db = firestore.client()

    # Get concert 847
    concert_ref = db.collection('concerts').document('847')
    concert_doc = concert_ref.get()

    if not concert_doc.exists:
        print("ERROR: Concert 847 not found!")
        return

    data = concert_doc.to_dict()

    print("\nCurrent state:")
    print(f"  Date: {data.get('date')}")
    print(f"  Venue: {data.get('venue_name')}")
    for artist in data.get('artists', []):
        print(f"  Artist: {artist.get('artist_name')} ({artist.get('role')})")

    print("\nNew structure:")
    print(f"  Artist 1: Rod Stewart (headliner, position: 1)")
    print(f"  Artist 2: Cyndi Lauper (headliner, position: 2)")

    response = input("\nApply this fix? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return

    # Find artist IDs
    rod_id = find_artist_id(db, 'Rod Stewart')
    cyndi_id = find_artist_id(db, 'Cyndi Lauper')

    if not rod_id:
        print("  Creating Rod Stewart artist record...")
        rod_ref = db.collection('artists').document()
        rod_ref.set({'canonical_name': 'Rod Stewart', 'created_at': firestore.SERVER_TIMESTAMP})
        rod_id = rod_ref.id

    if not cyndi_id:
        print("  Creating Cyndi Lauper artist record...")
        cyndi_ref = db.collection('artists').document()
        cyndi_ref.set({'canonical_name': 'Cyndi Lauper', 'created_at': firestore.SERVER_TIMESTAMP})
        cyndi_id = cyndi_ref.id

    print(f"  Rod Stewart ID: {rod_id}")
    print(f"  Cyndi Lauper ID: {cyndi_id}")

    # Create new artists array
    new_artists = [
        {
            'artist_id': rod_id,
            'artist_name': 'Rod Stewart',
            'position': 1,
            'role': 'headliner'
        },
        {
            'artist_id': cyndi_id,
            'artist_name': 'Cyndi Lauper',
            'position': 2,
            'role': 'headliner'
        }
    ]

    # Update the concert
    concert_ref.update({'artists': new_artists})

    print("\n✓ Concert 847 updated successfully!")

    # Verify
    updated_doc = concert_ref.get()
    updated_data = updated_doc.to_dict()
    print("\nUpdated concert:")
    for artist in updated_data.get('artists', []):
        print(f"  - {artist.get('artist_name')} (ID: {artist.get('artist_id')}, {artist.get('role')}, pos: {artist.get('position')})")

    print("\n" + "="*80)
    print("HOW IT WILL DISPLAY")
    print("="*80)
    print("The website will show: 'Rod Stewart, Cyndi Lauper'")
    print("Both are listed as headliners (not opener)")

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("1. Run: python3 scripts/export_to_web.py")
    print("2. Check: https://earplugsandmemories.com/concert.html?id=847")
    print("3. Deploy: firebase deploy --only hosting")

if __name__ == '__main__':
    fix_concert_847()
