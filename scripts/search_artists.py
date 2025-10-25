#!/usr/bin/env python3
"""
Search for artist records in Firestore.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'earplugs-and-memories'),
    })

db = firestore.client()

def search_artists(search_term):
    """Search for artists by name."""
    artists_ref = db.collection('artists')
    docs = artists_ref.stream()

    matches = []
    for doc in docs:
        data = doc.to_dict()
        canonical_name = data.get('canonical_name', '')

        # Case-insensitive search
        if search_term.lower() in canonical_name.lower():
            matches.append({
                'id': doc.id,
                'canonical_name': canonical_name,
                'aliases': data.get('aliases', []),
                'created_at': data.get('created_at')
            })

    return matches

def get_concerts_by_artist(artist_id, artist_name):
    """Get all concerts for a specific artist."""
    concerts_ref = db.collection('concerts')
    docs = concerts_ref.stream()

    concerts = []
    for doc in docs:
        data = doc.to_dict()
        artists = data.get('artists', [])

        # Check if this artist appears in the concert
        for artist in artists:
            if artist.get('artist_id') == artist_id or artist.get('artist_name') == artist_name:
                concerts.append({
                    'id': doc.id,
                    'date': data.get('date'),
                    'venue_name': data.get('venue_name'),
                    'city': data.get('city'),
                    'state': data.get('state'),
                    'artists': artists
                })
                break

    return concerts

if __name__ == '__main__':
    search_term = sys.argv[1] if len(sys.argv) > 1 else 'phil'

    print(f"\n🔍 Searching for artists matching: '{search_term}'")
    print("=" * 60)

    matches = search_artists(search_term)

    if not matches:
        print("No matches found.")
    else:
        for i, artist in enumerate(matches, 1):
            print(f"\n{i}. {artist['canonical_name']}")
            print(f"   ID: {artist['id']}")
            if artist['aliases']:
                print(f"   Aliases: {', '.join(artist['aliases'])}")

            # Get concert count
            concerts = get_concerts_by_artist(artist['id'], artist['canonical_name'])
            print(f"   Concerts: {len(concerts)}")

            if concerts and len(concerts) <= 5:
                print(f"   Shows:")
                for concert in concerts[:5]:
                    print(f"     - {concert['date']}: {concert['venue_name']}, {concert['city']}, {concert['state']}")

    print("\n" + "=" * 60)
