#!/usr/bin/env python3
"""
Merge Phil Lesh artist variations into one canonical artist.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'earplugs-and-memories'),
    })

db = firestore.client()

# Artists to merge
ARTISTS_TO_MERGE = {
    '427': 'Phil',  # Radio City shows
    '429': 'Phil Lesh',
    '147': 'DEAD: Phil Lesh + Friends (w. Warren Haynes'
}

CANONICAL_NAME = 'Phil Lesh & Friends'
CANONICAL_ID = '429'  # Use existing Phil Lesh ID

def merge_artists():
    """Merge Phil Lesh artist variations."""
    
    print("\n🔧 Merging Phil Lesh Artists")
    print("=" * 60)
    print(f"Canonical Artist: {CANONICAL_NAME} (ID: {CANONICAL_ID})")
    print("\nMerging from:")
    for aid, name in ARTISTS_TO_MERGE.items():
        print(f"  - {name} (ID: {aid})")
    print()
    
    # Step 1: Update the canonical artist record
    print(f"Step 1: Updating canonical artist to '{CANONICAL_NAME}'...")
    canonical_artist_ref = db.collection('artists').document(CANONICAL_ID)
    canonical_artist_ref.update({
        'canonical_name': CANONICAL_NAME,
        'aliases': ['Phil Lesh', 'Phil', 'Phil Lesh and Friends', 'Phil Lesh + Friends']
    })
    print(f"✅ Updated artist {CANONICAL_ID}")
    
    # Step 2: Update all concerts that reference the old artists
    print("\nStep 2: Updating concert references...")
    concerts_ref = db.collection('concerts')
    updated_count = 0
    
    for doc in concerts_ref.stream():
        concert_data = doc.to_dict()
        artists = concert_data.get('artists', [])
        updated = False
        
        new_artists = []
        for artist in artists:
            artist_id = artist.get('artist_id')
            artist_name = artist.get('artist_name')
            
            # Check if this artist should be merged
            if artist_id in ARTISTS_TO_MERGE or artist_name in ARTISTS_TO_MERGE.values():
                # Replace with canonical artist
                new_artists.append({
                    'artist_id': CANONICAL_ID,
                    'artist_name': CANONICAL_NAME,
                    'role': artist.get('role', 'headliner'),
                    'position': artist.get('position', 0)
                })
                updated = True
                print(f"  - Concert {doc.id} ({concert_data.get('date')}): {artist_name} → {CANONICAL_NAME}")
            else:
                new_artists.append(artist)
        
        if updated:
            doc.reference.update({'artists': new_artists})
            updated_count += 1
    
    print(f"✅ Updated {updated_count} concerts")
    
    # Step 3: Delete old artist records
    print("\nStep 3: Deleting old artist records...")
    for artist_id, artist_name in ARTISTS_TO_MERGE.items():
        if artist_id != CANONICAL_ID:  # Don't delete the canonical one
            db.collection('artists').document(artist_id).delete()
            print(f"  ✅ Deleted artist {artist_id} ({artist_name})")
    
    print("\n" + "=" * 60)
    print("✨ Merge complete!")
    print(f"\nAll Phil Lesh shows are now under: '{CANONICAL_NAME}'")
    print("\nNext steps:")
    print("  1. Run: python3 scripts/export_to_web.py")
    print("  2. Deploy: firebase deploy --only hosting")
    print()

if __name__ == '__main__':
    confirm = input(f"\n⚠️  This will merge {len(ARTISTS_TO_MERGE)} artists into '{CANONICAL_NAME}'. Continue? (yes/no): ")
    if confirm.lower() == 'yes':
        merge_artists()
    else:
        print("Cancelled.")
