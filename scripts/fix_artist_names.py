#!/usr/bin/env python3
"""
Fix artist name issues:
1. Merge "Wallflowers" into "The Wallflowers"
2. Fix "Mumford, Sons" to "Mumford and Sons"
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

def merge_artists(old_name, new_name):
    """Merge an artist with incorrect name into the correct one"""
    print(f"\n=== Merging '{old_name}' into '{new_name}' ===")

    # Find the old artist
    old_artist_ref = None
    old_artist_id = None
    artists_ref = db.collection('artists')
    query = artists_ref.where('name', '==', old_name).limit(1)
    for doc in query.stream():
        old_artist_ref = doc.reference
        old_artist_id = doc.id
        print(f"Found old artist: {old_name} (ID: {old_artist_id})")
        break

    if not old_artist_ref:
        print(f"Artist '{old_name}' not found, skipping...")
        return

    # Find or create the new artist
    new_artist_ref = None
    new_artist_id = None
    query = artists_ref.where('name', '==', new_name).limit(1)
    for doc in query.stream():
        new_artist_ref = doc.reference
        new_artist_id = doc.id
        print(f"Found new artist: {new_name} (ID: {new_artist_id})")
        break

    if not new_artist_ref:
        # Create the new artist by renaming the old one
        print(f"Creating new artist: {new_name}")
        old_artist_ref.update({'name': new_name})
        print(f"Renamed '{old_name}' to '{new_name}'")
        return

    # Both artists exist, need to merge
    print(f"Both artists exist, merging...")

    # Find all concerts with the old artist
    concerts_ref = db.collection('concerts')
    query = concerts_ref.where('artist_ids', 'array_contains', old_artist_id)

    updated_count = 0
    for doc in query.stream():
        concert_data = doc.to_dict()

        # Update artist_ids array
        artist_ids = concert_data.get('artist_ids', [])
        if old_artist_id in artist_ids:
            artist_ids.remove(old_artist_id)
            if new_artist_id not in artist_ids:
                artist_ids.append(new_artist_id)

        # Update artists array (detailed info)
        artists = concert_data.get('artists', [])
        for i, artist in enumerate(artists):
            if artist.get('id') == old_artist_id or artist.get('name') == old_name:
                artists[i]['id'] = new_artist_id
                artists[i]['name'] = new_name

        # Update the concert
        doc.reference.update({
            'artist_ids': artist_ids,
            'artists': artists
        })
        updated_count += 1
        print(f"  Updated concert {doc.id}")

    print(f"Updated {updated_count} concerts")

    # Delete the old artist
    print(f"Deleting old artist '{old_name}'...")
    old_artist_ref.delete()
    print(f"Deleted old artist")

def rename_artist(old_name, new_name):
    """Simply rename an artist"""
    print(f"\n=== Renaming '{old_name}' to '{new_name}' ===")

    # Find the artist
    artists_ref = db.collection('artists')
    query = artists_ref.where('name', '==', old_name).limit(1)

    artist_ref = None
    artist_id = None
    for doc in query.stream():
        artist_ref = doc.reference
        artist_id = doc.id
        print(f"Found artist: {old_name} (ID: {artist_id})")
        break

    if not artist_ref:
        print(f"Artist '{old_name}' not found, skipping...")
        return

    # Check if new name already exists
    query = artists_ref.where('name', '==', new_name).limit(1)
    for doc in query.stream():
        print(f"WARNING: Artist '{new_name}' already exists! Need to merge instead.")
        merge_artists(old_name, new_name)
        return

    # Rename the artist
    print(f"Renaming artist...")
    artist_ref.update({'name': new_name})

    # Find and update all concerts with this artist
    concerts_ref = db.collection('concerts')
    query = concerts_ref.where('artist_ids', 'array_contains', artist_id)

    updated_count = 0
    for doc in query.stream():
        concert_data = doc.to_dict()

        # Update artists array (detailed info)
        artists = concert_data.get('artists', [])
        for i, artist in enumerate(artists):
            if artist.get('id') == artist_id or artist.get('name') == old_name:
                artists[i]['name'] = new_name

        # Update the concert
        doc.reference.update({
            'artists': artists
        })
        updated_count += 1
        print(f"  Updated concert {doc.id}")

    print(f"Updated {updated_count} concerts")

def main():
    print("Starting artist name fixes...")

    # Fix 1: Merge "Wallflowers" into "The Wallflowers"
    merge_artists("Wallflowers", "The Wallflowers")

    # Fix 2: Rename "Mumford, Sons" to "Mumford and Sons"
    rename_artist("Mumford, Sons", "Mumford and Sons")

    print("\n=== All fixes complete! ===")
    print("\nNext steps:")
    print("1. Run: GOOGLE_CLOUD_PROJECT=earplugs-and-memories python3 scripts/export_to_web.py")
    print("2. Run: firebase deploy --only hosting")

if __name__ == '__main__':
    main()
