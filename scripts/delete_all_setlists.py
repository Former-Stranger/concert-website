#!/usr/bin/env python3
"""
Delete all setlist documents from Firestore.

This will clear all setlists so they can be re-fetched from setlist.fm
with the enhanced fetcher that captures:
- Cover artist names
- Tour names
- Guest artists
- Proper co-headliner handling

After running this, use fetch_setlists_enhanced.py to re-populate.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys
import os

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'earplugs-and-memories'),
            })
        except Exception as e:
            print(f"Could not use application default credentials: {e}")
            sys.exit(1)
    return firestore.client()

def delete_all_setlists(dry_run=False):
    """
    Delete all documents from the setlists collection

    Args:
        dry_run: If True, only report what would be deleted without making changes
    """
    print("="*80)
    print("DELETE ALL SETLISTS")
    print("="*80)

    if dry_run:
        print("⚠️  DRY RUN MODE - No changes will be made")

    db = init_firebase()

    print("\n📊 Scanning setlists collection...")

    # Get all setlists
    all_setlists = list(db.collection('setlists').stream())

    print(f"   Found {len(all_setlists)} setlist documents")

    if len(all_setlists) == 0:
        print("\n✅ No setlists found - collection is already empty!")
        return

    # Count by type
    single_format = 0  # Document ID is just concert_id (e.g., "847")
    multi_format = 0   # Document ID is concert_id-artist_slug (e.g., "847-rod-stewart")

    for doc in all_setlists:
        if '-' in doc.id:
            multi_format += 1
        else:
            single_format += 1

    print(f"   - Single setlists: {single_format}")
    print(f"   - Co-headliner setlists: {multi_format}")

    # Show sample
    print("\n📋 Sample of setlists to delete:")
    for doc in all_setlists[:10]:
        data = doc.to_dict()
        artist = data.get('artist_name', 'Unknown')
        song_count = data.get('song_count', 0)
        print(f"   {doc.id}: {artist} ({song_count} songs)")

    if len(all_setlists) > 10:
        print(f"   ... and {len(all_setlists) - 10} more")

    # Confirm if not dry run
    if not dry_run:
        print(f"\n⚠️  About to DELETE ALL {len(all_setlists)} setlist documents.")
        print("   This action cannot be undone.")
        print("   You will need to run fetch_setlists_enhanced.py to re-populate.")
        response = input("\n   Type 'DELETE' to confirm: ")
        if response != 'DELETE':
            print("Cancelled.")
            return

    # Delete all setlists
    print(f"\n🗑️  Deleting {len(all_setlists)} setlists...")

    batch = db.batch()
    batch_count = 0
    total_deleted = 0

    for doc in all_setlists:
        if not dry_run:
            batch.delete(doc.reference)
            batch_count += 1

            # Commit batch every 500 operations (Firestore limit)
            if batch_count >= 500:
                batch.commit()
                total_deleted += batch_count
                print(f"   Deleted: {total_deleted}/{len(all_setlists)} setlists")
                batch = db.batch()
                batch_count = 0

    # Commit remaining
    if not dry_run and batch_count > 0:
        batch.commit()
        total_deleted += batch_count

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    if dry_run:
        print(f"Would delete: {len(all_setlists)} setlist documents")
        print(f"   - Single format: {single_format}")
        print(f"   - Co-headliner format: {multi_format}")
        print("\n⚠️  This was a DRY RUN - no changes were made")
        print("   Run without --dry-run to actually delete the setlists")
    else:
        print(f"✅ Successfully deleted: {total_deleted} setlist documents")
        print(f"   - Single format: {single_format}")
        print(f"   - Co-headliner format: {multi_format}")
        print("\n📝 Next steps:")
        print("   1. Clean up artist information in concert documents")
        print("   2. Run: python3 scripts/fetch_setlists_enhanced.py")
        print("   3. Run: python3 scripts/export_to_web.py")
        print("   4. Run: firebase deploy --only hosting")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Delete all setlist documents from Firestore')
    parser.add_argument('--dry-run', action='store_true', help='Test mode - don\'t make changes')

    args = parser.parse_args()

    delete_all_setlists(dry_run=args.dry_run)
