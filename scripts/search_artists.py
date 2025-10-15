#!/usr/bin/env python3
"""Search for artists by partial name match"""

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

def search_artists(search_term):
    """Search for artists containing the search term (case-insensitive)"""
    print(f"\nSearching for artists containing '{search_term}'...\n")

    artists_ref = db.collection('artists')
    all_artists = artists_ref.stream()

    found = []
    for doc in all_artists:
        artist = doc.to_dict()
        name = artist.get('name', '')
        if search_term.lower() in name.lower():
            found.append({
                'id': doc.id,
                'name': name
            })

    if found:
        print(f"Found {len(found)} artist(s):")
        for artist in sorted(found, key=lambda x: x['name']):
            print(f"  - {artist['name']} (ID: {artist['id']})")
    else:
        print(f"No artists found containing '{search_term}'")

    return found

def main():
    # Search for Wallflowers
    print("=" * 60)
    search_artists("wallflower")

    # Search for Mumford
    print("\n" + "=" * 60)
    search_artists("mumford")

if __name__ == '__main__':
    main()
