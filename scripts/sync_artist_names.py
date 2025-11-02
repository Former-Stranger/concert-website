#!/usr/bin/env python3
"""
Sync artist names across all collections.

When an artist's canonical_name is changed in the artists collection,
this script updates all references in concerts and setlists to match.

This prevents data inconsistency where the same artist appears with
different names in different parts of the database.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys


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


def sync_artist_names(db, dry_run=True):
    """
    Sync artist names from artists collection to concerts and setlists.

    Args:
        db: Firestore client
        dry_run: If True, only report issues without fixing

    Returns:
        Tuple of (concerts_updated, setlists_updated)
    """
    print("Building artist ID → name mapping from artists collection...")

    # Build mapping of artist_id → canonical_name
    artists_ref = db.collection('artists')
    artist_docs = artists_ref.stream()

    artist_map = {}
    for doc in artist_docs:
        artist_map[doc.id] = doc.to_dict().get('canonical_name', '')

    print(f"  Found {len(artist_map)} artists")
    print()

    # Check concerts for mismatches
    print("Scanning concerts for artist name mismatches...")
    concerts_ref = db.collection('concerts')
    concerts_docs = concerts_ref.stream()

    concerts_to_update = []
    total_concerts = 0

    for doc in concerts_docs:
        total_concerts += 1
        concert_id = doc.id
        concert_data = doc.to_dict()
        artists = concert_data.get('artists', [])

        needs_update = False
        updated_artists = []

        for artist in artists:
            artist_id = artist.get('artist_id')
            current_name = artist.get('artist_name', '')
            canonical_name = artist_map.get(artist_id, '')

            if artist_id and canonical_name and current_name != canonical_name:
                needs_update = True
                print(f"\nConcert {concert_id} ({concert_data.get('date')}):")
                print(f"  ❌ Mismatch: \"{current_name}\" → \"{canonical_name}\"")

                # Create updated artist entry
                updated_artist = artist.copy()
                updated_artist['artist_name'] = canonical_name
                updated_artists.append(updated_artist)
            else:
                updated_artists.append(artist)

        if needs_update:
            concerts_to_update.append((concert_id, updated_artists))

    print(f"\nScanned {total_concerts} concerts")
    print(f"Found {len(concerts_to_update)} concerts needing updates")
    print()

    # Check setlists for mismatches
    print("Scanning setlists for artist name mismatches...")
    setlists_ref = db.collection('setlists')
    setlists_docs = setlists_ref.stream()

    setlists_to_update = []
    total_setlists = 0

    for doc in setlists_docs:
        total_setlists += 1
        setlist_id = doc.id
        setlist_data = doc.to_dict()

        artist_id = setlist_data.get('artist_id')
        current_name = setlist_data.get('artist_name', '')

        # Note: artist_id in setlists might be MusicBrainz ID, not Firestore ID
        # So we need to also check by name matching
        canonical_name = None

        # Try to find by Firestore ID first
        if artist_id and artist_id in artist_map:
            canonical_name = artist_map[artist_id]
        else:
            # Try to find by name (case-insensitive)
            for aid, aname in artist_map.items():
                if aname.lower() == current_name.lower():
                    canonical_name = aname
                    break

        if canonical_name and current_name != canonical_name:
            print(f"\nSetlist {setlist_id} (Concert {setlist_data.get('concert_id')}):")
            print(f"  ❌ Mismatch: \"{current_name}\" → \"{canonical_name}\"")
            setlists_to_update.append((setlist_id, canonical_name))

    print(f"\nScanned {total_setlists} setlists")
    print(f"Found {len(setlists_to_update)} setlists needing updates")
    print()

    if dry_run:
        return len(concerts_to_update), len(setlists_to_update)

    # Apply updates
    print("Applying updates...")

    # Update concerts
    concerts_updated = 0
    for concert_id, updated_artists in concerts_to_update:
        concert_ref = db.collection('concerts').document(concert_id)
        concert_ref.update({
            'artists': updated_artists,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        concerts_updated += 1
        print(f"  ✓ Updated concert {concert_id}")

    # Update setlists
    setlists_updated = 0
    for setlist_id, canonical_name in setlists_to_update:
        setlist_ref = db.collection('setlists').document(setlist_id)
        setlist_ref.update({
            'artist_name': canonical_name,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        setlists_updated += 1
        print(f"  ✓ Updated setlist {setlist_id}")

    return concerts_updated, setlists_updated


def main():
    """Main sync function"""
    import argparse

    parser = argparse.ArgumentParser(description='Sync artist names across all collections')
    parser.add_argument('--dry-run', action='store_true',
                       help='Report issues without fixing them')
    args = parser.parse_args()

    db = init_firebase()

    print("=" * 70)
    print("ARTIST NAME SYNC SCRIPT")
    print("=" * 70)

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made")
    else:
        print("\n⚠️  LIVE MODE - Changes will be written to Firestore")
        response = input("\nAre you sure you want to proceed? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return

    print()
    print("=" * 70)

    concerts_count, setlists_count = sync_artist_names(db, dry_run=args.dry_run)

    # Print summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if args.dry_run:
        print(f"Concerts that would be updated: {concerts_count}")
        print(f"Setlists that would be updated: {setlists_count}")
        print("\n💡 Run without --dry-run to apply fixes")
    else:
        print(f"Concerts updated: {concerts_count}")
        print(f"Setlists updated: {setlists_count}")
        print("\n✓ Sync complete!")

        if concerts_count > 0 or setlists_count > 0:
            print("\n💡 Run export_to_web.py to update the website with synced data")

    print("=" * 70)


if __name__ == '__main__':
    main()
