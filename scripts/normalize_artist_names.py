#!/usr/bin/env python3
"""
Normalize artist names in the concerts collection.
Fixes inconsistent capitalization and "the" usage.
"""

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

# Map of incorrect names -> correct names
ARTIST_NAME_FIXES = {
    # Wallflowers variations
    'Wallflowers': 'The Wallflowers',
    'the Wallflowers': 'The Wallflowers',

    # Mumford variations (keeping "Mumford and Sons with Dawes" as is - that's a special show)
    'Mumford': 'Mumford & Sons',
    'Marcus Mumford': 'Marcus Mumford',  # Keep as is - this is a solo artist

    # Other fixes found
    'Beach Boys': 'The Beach Boys',
    'Bob Seger & Silver Bullet Band': 'Bob Seger & the Silver Bullet Band',
    'company': 'Company',
    'the Coral Reefer Band': 'Coral Reefer Band',
    'Dead': 'The Dead',
    'Doobie Brothers': 'The Doobie Brothers',
    'Eagles': 'The Eagles',
    'Joe ely': 'Joe Ely',
    'Lee Dewyze': 'Lee DeWyze',
    'nash': 'Nash',
    'Nash & young': 'Nash & Young',
    'The News': 'the News',  # Huey Lewis and the News - lowercase 'the'
    'the Pretenders': 'The Pretenders',
    'the Retrotones': 'Retrotones',
    'Rolling Stones': 'The Rolling Stones',
    'Tom Petty & The Heartbreakers': 'Tom Petty & the Heartbreakers',  # lowercase 'the'
    'ZZTOP': 'ZZ Top',
    'ZZTop': 'ZZ Top',
}

def normalize_artist_names():
    """Fix artist names in concerts collection"""
    print("Normalizing artist names in concerts collection...")
    print("=" * 60)

    concerts_ref = db.collection('concerts')
    all_concerts = concerts_ref.stream()

    updated_count = 0
    fixed_artists = set()

    for doc in all_concerts:
        concert = doc.to_dict()
        artists = concert.get('artists', [])

        updated = False
        for i, artist in enumerate(artists):
            old_name = artist.get('artist_name', '')
            if old_name in ARTIST_NAME_FIXES:
                new_name = ARTIST_NAME_FIXES[old_name]
                artists[i]['artist_name'] = new_name
                updated = True
                fixed_artists.add(f"{old_name} → {new_name}")
                print(f"  Concert {doc.id}: '{old_name}' → '{new_name}'")

        if updated:
            doc.reference.update({'artists': artists})
            updated_count += 1

    print("\n" + "=" * 60)
    print(f"Updated {updated_count} concerts")
    print("\nArtist name changes made:")
    for fix in sorted(fixed_artists):
        print(f"  - {fix}")

    print("\n" + "=" * 60)
    print("Next steps:")
    print("1. Run: GOOGLE_CLOUD_PROJECT=earplugs-and-memories python3 scripts/export_to_web.py")
    print("2. Run: firebase deploy --only hosting")

if __name__ == '__main__':
    if '--confirm' not in sys.argv:
        print("This will modify artist names in the concerts collection.")
        print("Run with --confirm to proceed.")
        sys.exit(1)

    normalize_artist_names()
