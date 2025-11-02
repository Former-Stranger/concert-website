#!/usr/bin/env python3
"""
Cleanup malformed artist entries across all concerts.

This script finds and removes artist entries that appear to be concatenations
of multiple artists (e.g., "Artist A with Artist B and Artist C") and were
likely artifacts from old data imports.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys
import re


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


def is_malformed_artist_name(name, all_artist_names):
    """
    Detect if an artist name is malformed (contains multiple artists).

    Args:
        name: The artist name to check
        all_artist_names: List of all artist names in the concert

    Returns:
        True if the name appears to be malformed
    """
    if not name:
        return False

    # Check for multiple "with/and" indicators (strong signal)
    multi_indicators = len(re.findall(r' with | and | \+ | \/ ', name, re.IGNORECASE))
    if multi_indicators >= 2:
        return True

    # Check if it contains "with/and" and the name includes another artist from the list
    if ' with ' in name.lower() or ' and ' in name.lower():
        # Check if any other artist name is contained in this name
        for other_name in all_artist_names:
            if other_name != name and other_name.lower() in name.lower():
                return True

    return False


def cleanup_concert_artists(db, concert_id, concert_data, dry_run=True):
    """
    Clean up malformed artists for a single concert.

    Args:
        db: Firestore client
        concert_id: Concert document ID
        concert_data: Concert data dict
        dry_run: If True, only report issues without fixing

    Returns:
        Tuple of (had_issues, was_fixed)
    """
    artists = concert_data.get('artists', [])

    if not artists:
        return False, False

    # Get all artist names
    artist_names = [a.get('artist_name', '') for a in artists]

    # Find malformed entries
    malformed = []
    for artist in artists:
        name = artist.get('artist_name', '')
        if is_malformed_artist_name(name, artist_names):
            malformed.append(artist)

    if not malformed:
        return False, False

    # Report issues
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Concert {concert_id}:")
    print(f"  Date: {concert_data.get('date')}")
    print(f"  Venue: {concert_data.get('venue_name')}")
    print(f"  Found {len(malformed)} malformed artist entries:")

    for artist in malformed:
        print(f"    ❌ \"{artist.get('artist_name')}\" (ID: {artist.get('artist_id')})")

    print(f"  Keeping {len(artists) - len(malformed)} valid artists:")
    for artist in artists:
        if artist not in malformed:
            print(f"    ✓ \"{artist.get('artist_name')}\" ({artist.get('role')})")

    if dry_run:
        return True, False

    # Fix the data
    cleaned_artists = [a for a in artists if a not in malformed]

    # Fix positions to be sequential
    for i, artist in enumerate(cleaned_artists, 1):
        artist['position'] = i

    # Update Firestore
    concert_ref = db.collection('concerts').document(concert_id)
    concert_ref.update({
        'artists': cleaned_artists,
        'updated_at': firestore.SERVER_TIMESTAMP
    })

    print(f"  ✓ Fixed concert {concert_id}")

    return True, True


def main():
    """Main cleanup function"""
    import argparse

    parser = argparse.ArgumentParser(description='Cleanup malformed artist entries')
    parser.add_argument('--dry-run', action='store_true',
                       help='Report issues without fixing them')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of concerts to check')
    args = parser.parse_args()

    db = init_firebase()

    print("=" * 70)
    print("MALFORMED ARTIST CLEANUP SCRIPT")
    print("=" * 70)

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made")
    else:
        print("\n⚠️  LIVE MODE - Changes will be written to Firestore")
        response = input("\nAre you sure you want to proceed? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return

    print("\nScanning concerts for malformed artist entries...")
    print("=" * 70)

    # Get all concerts
    concerts_ref = db.collection('concerts')
    query = concerts_ref.order_by('date', direction=firestore.Query.DESCENDING)

    if args.limit:
        query = query.limit(args.limit)

    concerts = query.stream()

    total_concerts = 0
    concerts_with_issues = 0
    concerts_fixed = 0

    for doc in concerts:
        total_concerts += 1
        concert_id = doc.id
        concert_data = doc.to_dict()

        had_issues, was_fixed = cleanup_concert_artists(
            db, concert_id, concert_data, dry_run=args.dry_run
        )

        if had_issues:
            concerts_with_issues += 1
        if was_fixed:
            concerts_fixed += 1

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total concerts scanned: {total_concerts}")
    print(f"Concerts with malformed artists: {concerts_with_issues}")

    if args.dry_run:
        print(f"Concerts that would be fixed: {concerts_with_issues}")
        print("\n💡 Run without --dry-run to apply fixes")
    else:
        print(f"Concerts fixed: {concerts_fixed}")
        print("\n✓ Cleanup complete!")

    print("=" * 70)


if __name__ == '__main__':
    main()
