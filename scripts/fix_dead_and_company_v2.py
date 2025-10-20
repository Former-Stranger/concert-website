#!/usr/bin/env python3
"""Fix Dead and Company multi-artist entries"""

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'earplugs-and-memories'
    })

db = firestore.client()

def fix_dead_and_company_concerts():
    """Fix concerts that have The Dead + Company as separate artists"""

    # Find all concerts with Company (artist 131) in the artists array
    all_concerts = db.collection('concerts').stream()

    concerts_to_fix = []
    for concert_doc in all_concerts:
        concert = concert_doc.to_dict()
        artists = concert.get('artists', [])

        if not isinstance(artists, list):
            continue

        # Check if this concert has both The Dead (162) and Company (131)
        has_the_dead = any(a.get('artist_id') == '162' for a in artists)
        has_company = any(a.get('artist_id') == '131' for a in artists)

        if has_the_dead and has_company:
            concerts_to_fix.append({
                'id': concert_doc.id,
                'date': concert.get('date'),
                'venue': concert.get('venue_name'),
                'artists': artists
            })

    print(f"Found {len(concerts_to_fix)} concerts to fix\n")

    if not concerts_to_fix:
        print("No concerts need fixing!")
        return

    # Show first few examples
    print("Examples:")
    for concert in concerts_to_fix[:3]:
        print(f"  Concert {concert['id']} ({concert['date']}) at {concert['venue']}")
        print(f"    Current artists: {concert['artists']}")

    # Ask for confirmation
    print(f"\nWill update {len(concerts_to_fix)} concerts to use single artist 'Dead and Company'")

    # Fix each concert
    for concert in concerts_to_fix:
        concert_ref = db.collection('concerts').document(concert['id'])

        # Update to single artist entry
        concert_ref.update({
            'artist_id': '131',
            'artist_name': 'Dead and Company',
            'artists': [{
                'artist_id': '131',
                'artist_name': 'Dead and Company',
                'role': 'headliner',
                'position': 1
            }],
            'festival_name': None  # Remove festival designation
        })

    print(f"✅ Updated {len(concerts_to_fix)} concerts")

    # Also check artist 131's name and canonical name
    artist_ref = db.collection('artists').document('131')
    artist_ref.update({
        'name': 'Dead and Company',
        'canonical_name': 'Dead and Company'
    })
    print("✅ Updated artist 131 metadata")

if __name__ == '__main__':
    print("=" * 60)
    print("Fixing Dead and Company concerts")
    print("=" * 60)
    print()

    fix_dead_and_company_concerts()
