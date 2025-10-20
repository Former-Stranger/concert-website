#!/usr/bin/env python3
"""Fix artist 656 - another Dead and Company instance"""

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'earplugs-and-memories'
    })

db = firestore.client()

def fix_artist_656_concerts():
    """Fix concerts that have The Dead (162) + Company (656) as separate artists"""

    # Find all concerts with Company (artist 656) in the artists array
    all_concerts = db.collection('concerts').stream()

    concerts_to_fix = []
    for concert_doc in all_concerts:
        concert = concert_doc.to_dict()
        artists = concert.get('artists', [])

        if not isinstance(artists, list):
            continue

        # Check if this concert has both The Dead (162) and Company (656)
        has_the_dead = any(a.get('artist_id') == '162' for a in artists)
        has_company_656 = any(a.get('artist_id') == '656' for a in artists)

        if has_the_dead and has_company_656:
            concerts_to_fix.append({
                'id': concert_doc.id,
                'date': concert.get('date'),
                'venue': concert.get('venue_name'),
                'artists': artists
            })

    print(f"Found {len(concerts_to_fix)} concerts with artist 656 to fix\n")

    if concerts_to_fix:
        print("Concerts to fix:")
        for concert in concerts_to_fix:
            print(f"  Concert {concert['id']} ({concert['date']}) at {concert['venue']}")
            print(f"    Current artists: {concert['artists']}")

        print(f"\nWill update {len(concerts_to_fix)} concerts to use artist 131 'Dead and Company'")

        # Fix each concert
        for concert in concerts_to_fix:
            concert_ref = db.collection('concerts').document(concert['id'])

            # Update to single artist entry using artist 131
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

    # Delete artist 656 since it's a duplicate
    artist_ref = db.collection('artists').document('656')
    artist_ref.delete()
    print("✅ Deleted duplicate artist 656")

if __name__ == '__main__':
    print("=" * 60)
    print("Fixing artist 656 (Dead and Company duplicate)")
    print("=" * 60)
    print()

    fix_artist_656_concerts()
