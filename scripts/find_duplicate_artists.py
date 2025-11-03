#!/usr/bin/env python3
"""
Find and merge duplicate artists in Firestore
Handles cases like "The Wild Feathers" vs "Wild Feathers"
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys
from collections import defaultdict


def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Could not use application default credentials: {e}")
            print("\nTo fix this, run:")
            print("  gcloud auth application-default login")
            sys.exit(1)
    return firestore.client()


def normalize_artist_name(name):
    """
    Normalize artist name for comparison
    - Lowercase
    - Remove special characters
    - Remove leading articles (The, A, An)
    """
    normalized = name.lower()
    # Remove special characters
    normalized = ''.join(c if c.isalnum() or c.isspace() else '' for c in normalized)
    # Normalize whitespace
    normalized = ' '.join(normalized.split())
    # Remove leading articles
    for article in ['the ', 'a ', 'an ']:
        if normalized.startswith(article):
            normalized = normalized[len(article):]
            break
    return normalized.strip()


def find_duplicates(db):
    """Find duplicate artists based on normalized names"""
    print("Scanning artists collection for duplicates...")

    artists_ref = db.collection('artists')
    artists_docs = artists_ref.stream()

    # Group artists by normalized name
    normalized_groups = defaultdict(list)

    for doc in artists_docs:
        data = doc.to_dict()
        canonical_name = data.get('canonical_name', '')
        if canonical_name:
            normalized = normalize_artist_name(canonical_name)
            normalized_groups[normalized].append({
                'id': doc.id,
                'name': canonical_name,
                'created_at': data.get('created_at')
            })

    # Find groups with multiple artists (duplicates)
    duplicates = {}
    for normalized, artists in normalized_groups.items():
        if len(artists) > 1:
            # Sort by creation date (oldest first)
            artists.sort(key=lambda x: x.get('created_at') or 0)
            duplicates[normalized] = artists

    return duplicates


def count_concerts_for_artist(db, artist_id):
    """Count how many concerts reference this artist"""
    concerts_ref = db.collection('concerts')
    concerts = concerts_ref.stream()

    count = 0
    concert_ids = []

    for concert_doc in concerts:
        concert_data = concert_doc.to_dict()
        for artist in concert_data.get('artists', []):
            if artist.get('artist_id') == artist_id:
                count += 1
                concert_ids.append(concert_doc.id)
                break

    return count, concert_ids


def merge_artists(db, keep_id, keep_name, merge_id, merge_name, dry_run=True):
    """
    Merge two artist documents
    - Update all concerts that reference merge_id to use keep_id
    - Delete merge_id artist document
    """
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Merging artists:")
    print(f"  KEEP:   {keep_id} - '{keep_name}'")
    print(f"  MERGE:  {merge_id} - '{merge_name}'")

    # Find concerts that reference the artist being merged
    concerts_ref = db.collection('concerts')
    concerts_to_update = []

    print(f"\nScanning concerts for references to '{merge_name}'...")
    for concert_doc in concerts_ref.stream():
        concert_data = concert_doc.to_dict()
        artists = concert_data.get('artists', [])

        needs_update = False
        updated_artists = []

        for artist in artists:
            if artist.get('artist_id') == merge_id:
                needs_update = True
                # Update to use the kept artist
                updated_artist = artist.copy()
                updated_artist['artist_id'] = keep_id
                updated_artist['artist_name'] = keep_name
                updated_artists.append(updated_artist)
                print(f"  Concert {concert_doc.id}: '{merge_name}' → '{keep_name}'")
            else:
                updated_artists.append(artist)

        if needs_update:
            concerts_to_update.append({
                'id': concert_doc.id,
                'ref': concert_doc.reference,
                'artists': updated_artists
            })

    if not concerts_to_update:
        print(f"  No concerts reference '{merge_name}'")
        return

    print(f"\nFound {len(concerts_to_update)} concerts to update")

    if dry_run:
        print("\n[DRY RUN] No changes made. Run with --execute to apply changes.")
        return

    # Execute updates
    print("\nUpdating concerts...")
    batch = db.batch()
    batch_count = 0

    for concert in concerts_to_update:
        batch.update(concert['ref'], {
            'artists': concert['artists'],
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        batch_count += 1

        # Commit in batches of 500 (Firestore limit)
        if batch_count >= 500:
            batch.commit()
            print(f"  Committed batch of {batch_count} updates")
            batch = db.batch()
            batch_count = 0

    if batch_count > 0:
        batch.commit()
        print(f"  Committed final batch of {batch_count} updates")

    # Delete the merged artist document
    print(f"\nDeleting artist '{merge_name}' ({merge_id})...")
    db.collection('artists').document(merge_id).delete()

    print(f"\n✅ Successfully merged '{merge_name}' into '{keep_name}'")


def interactive_mode(db):
    """Interactive duplicate resolution"""
    duplicates = find_duplicates(db)

    if not duplicates:
        print("\n✅ No duplicate artists found!")
        return

    print(f"\n⚠️  Found {len(duplicates)} groups of duplicate artists:\n")

    for i, (normalized, artists) in enumerate(duplicates.items(), 1):
        print(f"{i}. Normalized name: '{normalized}'")
        for artist in artists:
            count, concert_ids = count_concerts_for_artist(db, artist['id'])
            created = artist.get('created_at')
            created_str = created.strftime('%Y-%m-%d') if created else 'Unknown'
            print(f"   - {artist['id'][:8]}... - '{artist['name']}' ({count} concerts, created {created_str})")
        print()

    print("\nOptions:")
    print("1. Merge specific duplicate")
    print("2. Show concert details for an artist")
    print("q. Quit")

    while True:
        choice = input("\nEnter choice: ").strip()

        if choice == 'q':
            break
        elif choice == '1':
            merge_duplicate(db, duplicates)
        elif choice == '2':
            show_artist_concerts(db)
        else:
            print("Invalid choice!")


def merge_duplicate(db, duplicates):
    """Interactive merge of a specific duplicate"""
    print("\nEnter artist IDs to merge:")
    keep_id = input("  ID to KEEP: ").strip()
    merge_id = input("  ID to MERGE (will be deleted): ").strip()

    # Find artist names
    keep_doc = db.collection('artists').document(keep_id).get()
    merge_doc = db.collection('artists').document(merge_id).get()

    if not keep_doc.exists:
        print(f"Error: Artist {keep_id} not found!")
        return
    if not merge_doc.exists:
        print(f"Error: Artist {merge_id} not found!")
        return

    keep_name = keep_doc.to_dict().get('canonical_name')
    merge_name = merge_doc.to_dict().get('canonical_name')

    # Show preview
    merge_artists(db, keep_id, keep_name, merge_id, merge_name, dry_run=True)

    confirm = input("\nExecute merge? (yes/no): ").strip().lower()
    if confirm == 'yes':
        merge_artists(db, keep_id, keep_name, merge_id, merge_name, dry_run=False)
        print("\n✅ Merge complete!")
    else:
        print("Cancelled.")


def show_artist_concerts(db):
    """Show concert details for an artist"""
    artist_id = input("Enter artist ID: ").strip()

    doc = db.collection('artists').document(artist_id).get()
    if not doc.exists:
        print(f"Artist {artist_id} not found!")
        return

    artist_name = doc.to_dict().get('canonical_name')
    count, concert_ids = count_concerts_for_artist(db, artist_id)

    print(f"\nArtist: {artist_name}")
    print(f"Concerts: {count}")

    if concert_ids:
        print("\nConcert IDs:")
        for cid in concert_ids:
            concert_doc = db.collection('concerts').document(cid).get()
            if concert_doc.exists:
                data = concert_doc.to_dict()
                print(f"  {cid}: {data.get('date')} @ {data.get('venue_name')}")


if __name__ == '__main__':
    db = init_firebase()

    if len(sys.argv) > 1 and sys.argv[1] == '--auto-merge':
        # Auto-merge mode (for scripting)
        if len(sys.argv) < 4:
            print("Usage: find_duplicate_artists.py --auto-merge <keep_id> <merge_id>")
            sys.exit(1)

        keep_id = sys.argv[2]
        merge_id = sys.argv[3]

        keep_doc = db.collection('artists').document(keep_id).get()
        merge_doc = db.collection('artists').document(merge_id).get()

        if not keep_doc.exists or not merge_doc.exists:
            print("Error: One or both artist IDs not found!")
            sys.exit(1)

        keep_name = keep_doc.to_dict().get('canonical_name')
        merge_name = merge_doc.to_dict().get('canonical_name')

        merge_artists(db, keep_id, keep_name, merge_id, merge_name, dry_run=False)
    else:
        # Interactive mode
        interactive_mode(db)
