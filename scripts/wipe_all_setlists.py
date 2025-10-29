#!/usr/bin/env python3
"""
Complete Setlist Database Wipe Script

This script performs a complete reset of all setlist data:
1. Deletes ALL setlist documents from Firestore
2. Resets has_setlist flag to false on all concerts
3. Optionally deletes exported JSON files

USE WITH CAUTION - This is destructive and cannot be undone!

Usage:
    # Dry run (preview what would be deleted)
    python3 wipe_all_setlists.py --dry-run

    # Execute the wipe
    python3 wipe_all_setlists.py --confirm

    # Wipe database and delete JSON files
    python3 wipe_all_setlists.py --confirm --delete-json
"""

import sys
import os
import argparse
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'earplugs-and-memories'),
            })
        except Exception as e:
            print(f"Error: Could not initialize Firebase: {e}")
            print("Make sure you're authenticated with: gcloud auth application-default login")
            sys.exit(1)
    return firestore.client()


def delete_all_setlists(db, dry_run=False):
    """
    Delete all setlist documents from Firestore

    Args:
        db: Firestore client
        dry_run: If True, only count and display, don't delete

    Returns:
        Number of setlists deleted/counted
    """
    print("\n" + "="*80)
    print("STEP 1: Delete all setlist documents")
    print("="*80)

    setlists_ref = db.collection('setlists')

    # Get all setlists
    print("\nFetching all setlist documents...")
    setlists = list(setlists_ref.stream())
    count = len(setlists)

    print(f"Found {count} setlist documents")

    if count == 0:
        print("✓ No setlists to delete")
        return 0

    if dry_run:
        print(f"\n[DRY RUN] Would delete {count} setlist documents:")
        for i, setlist in enumerate(setlists[:10], 1):
            data = setlist.to_dict()
            artist = data.get('artist_name', 'Unknown')
            concert_id = data.get('concert_id', 'Unknown')
            songs = data.get('song_count', 0)
            print(f"  {i}. {setlist.id} - {artist} (Concert {concert_id}, {songs} songs)")

        if count > 10:
            print(f"  ... and {count - 10} more")
        return count

    # Confirm before deleting
    print(f"\n⚠️  About to delete {count} setlist documents!")
    print("This action cannot be undone.")
    response = input("Type 'DELETE' to confirm: ")

    if response != 'DELETE':
        print("Aborted.")
        sys.exit(0)

    # Delete in batches
    batch_size = 500  # Firestore batch limit
    deleted = 0

    print(f"\nDeleting setlists in batches of {batch_size}...")

    for i in range(0, count, batch_size):
        batch = db.batch()
        batch_docs = setlists[i:i + batch_size]

        for doc in batch_docs:
            batch.delete(doc.reference)

        batch.commit()
        deleted += len(batch_docs)

        print(f"  Deleted {deleted}/{count} ({deleted*100//count}%)")

    print(f"\n✓ Successfully deleted {deleted} setlist documents")
    return deleted


def reset_has_setlist_flags(db, dry_run=False):
    """
    Reset has_setlist flag to false on all concerts

    Args:
        db: Firestore client
        dry_run: If True, only count and display, don't update

    Returns:
        Number of concerts updated
    """
    print("\n" + "="*80)
    print("STEP 2: Reset has_setlist flags on all concerts")
    print("="*80)

    concerts_ref = db.collection('concerts')

    # Get all concerts
    print("\nFetching all concerts...")
    concerts = list(concerts_ref.stream())
    count = len(concerts)

    print(f"Found {count} concerts")

    # Check how many have has_setlist = true
    concerts_with_flag = [c for c in concerts if c.to_dict().get('has_setlist', False)]
    flag_count = len(concerts_with_flag)

    if flag_count == 0:
        print("✓ No concerts have has_setlist flag set")
        return 0

    print(f"Found {flag_count} concerts with has_setlist = true")

    if dry_run:
        print(f"\n[DRY RUN] Would reset has_setlist flag on {flag_count} concerts:")
        for i, concert in enumerate(concerts_with_flag[:10], 1):
            data = concert.to_dict()
            date = data.get('date', 'Unknown')
            artists = data.get('artists', [])
            artist_names = ', '.join([a.get('artist_name', '') for a in artists])
            print(f"  {i}. Concert {concert.id} - {artist_names} ({date})")

        if flag_count > 10:
            print(f"  ... and {flag_count - 10} more")
        return flag_count

    # Update in batches
    batch_size = 500
    updated = 0

    print(f"\nResetting flags in batches of {batch_size}...")

    for i in range(0, len(concerts_with_flag), batch_size):
        batch = db.batch()
        batch_docs = concerts_with_flag[i:i + batch_size]

        for doc in batch_docs:
            batch.update(doc.reference, {'has_setlist': False})

        batch.commit()
        updated += len(batch_docs)

        print(f"  Updated {updated}/{flag_count} ({updated*100//flag_count}%)")

    print(f"\n✓ Successfully reset {updated} concert flags")
    return updated


def delete_json_files(dry_run=False):
    """
    Delete exported JSON files

    Args:
        dry_run: If True, only list files, don't delete

    Returns:
        Number of files deleted
    """
    print("\n" + "="*80)
    print("STEP 3: Delete exported JSON files")
    print("="*80)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_dir = os.path.join(project_root, 'website', 'data')

    files_to_delete = []

    # Find concert_details/*.json files
    concert_details_dir = os.path.join(data_dir, 'concert_details')
    if os.path.exists(concert_details_dir):
        for filename in os.listdir(concert_details_dir):
            if filename.endswith('.json'):
                files_to_delete.append(os.path.join(concert_details_dir, filename))

    # Also check songs.json (will be regenerated with 0 songs)
    songs_file = os.path.join(data_dir, 'songs.json')
    if os.path.exists(songs_file):
        files_to_delete.append(songs_file)

    count = len(files_to_delete)

    if count == 0:
        print("✓ No JSON files to delete")
        return 0

    print(f"Found {count} JSON files to delete")

    if dry_run:
        print(f"\n[DRY RUN] Would delete {count} files:")
        for i, filepath in enumerate(files_to_delete[:10], 1):
            filename = os.path.basename(filepath)
            print(f"  {i}. {filename}")

        if count > 10:
            print(f"  ... and {count - 10} more")
        return count

    # Delete files
    deleted = 0
    for filepath in files_to_delete:
        try:
            os.remove(filepath)
            deleted += 1
        except Exception as e:
            print(f"  ⚠️  Error deleting {filepath}: {e}")

    print(f"\n✓ Successfully deleted {deleted} JSON files")
    return deleted


def main():
    parser = argparse.ArgumentParser(
        description="Completely wipe all setlist data from database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Preview what would be deleted (safe)
    python3 wipe_all_setlists.py --dry-run

    # Wipe database only
    python3 wipe_all_setlists.py --confirm

    # Wipe database and delete JSON files
    python3 wipe_all_setlists.py --confirm --delete-json
        """
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be deleted without making changes'
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Actually execute the wipe (required for non-dry-run)'
    )
    parser.add_argument(
        '--delete-json',
        action='store_true',
        help='Also delete exported JSON files'
    )

    args = parser.parse_args()

    # Safety check
    if not args.dry_run and not args.confirm:
        print("Error: Must use either --dry-run or --confirm")
        print("Run with --dry-run first to preview what would be deleted")
        sys.exit(1)

    print("="*80)
    print("SETLIST DATABASE WIPE SCRIPT")
    print("="*80)
    print(f"\nTimestamp: {datetime.now().isoformat()}")

    if args.dry_run:
        print("Mode: DRY RUN (no changes will be made)")
    else:
        print("Mode: LIVE (changes will be made)")
        print("\n⚠️  WARNING: This will delete all setlist data!")
        print("This action cannot be undone.")

        response = input("\nType 'I UNDERSTAND' to continue: ")
        if response != 'I UNDERSTAND':
            print("Aborted.")
            sys.exit(0)

    # Initialize Firebase
    db = init_firebase()

    # Execute steps
    start_time = time.time()

    # Step 1: Delete setlists
    setlists_deleted = delete_all_setlists(db, dry_run=args.dry_run)

    # Step 2: Reset flags
    flags_reset = reset_has_setlist_flags(db, dry_run=args.dry_run)

    # Step 3: Delete JSON files (optional)
    json_deleted = 0
    if args.delete_json:
        json_deleted = delete_json_files(dry_run=args.dry_run)

    # Summary
    elapsed = time.time() - start_time

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nSetlist documents deleted: {setlists_deleted}")
    print(f"Concert flags reset: {flags_reset}")
    if args.delete_json:
        print(f"JSON files deleted: {json_deleted}")
    print(f"\nElapsed time: {elapsed:.1f} seconds")

    if args.dry_run:
        print("\n⚠️  This was a DRY RUN - no changes were made")
        print("Run with --confirm to execute the wipe")
    else:
        print("\n✅ Wipe completed successfully!")
        print("\nNext steps:")
        print("1. Run fetch_setlists_enhanced.py to fetch fresh setlists")
        print("2. Run export_to_web.py to regenerate JSON files")
        print("3. Deploy to Firebase hosting")


if __name__ == '__main__':
    main()
