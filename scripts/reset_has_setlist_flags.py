#!/usr/bin/env python3
"""
Reset has_setlist flags to false for all concerts.

After deleting all setlists, we need to reset the has_setlist flag
on all concert documents so the stats and exports are accurate.
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

def reset_has_setlist_flags(dry_run=False):
    """
    Set has_setlist=false for all concerts

    Args:
        dry_run: If True, only report what would be changed without making changes
    """
    print("="*80)
    print("RESET HAS_SETLIST FLAGS")
    print("="*80)

    if dry_run:
        print("⚠️  DRY RUN MODE - No changes will be made")

    db = init_firebase()

    print("\n📊 Scanning concerts...")

    # Get all concerts
    all_concerts = list(db.collection('concerts').stream())

    concerts_with_setlist = []
    for doc in all_concerts:
        data = doc.to_dict()
        if data.get('has_setlist', False):
            concerts_with_setlist.append(doc.id)

    print(f"   Total concerts: {len(all_concerts)}")
    print(f"   Concerts with has_setlist=true: {len(concerts_with_setlist)}")

    if len(concerts_with_setlist) == 0:
        print("\n✅ All concerts already have has_setlist=false!")
        return

    # Show sample
    print("\n📋 Sample of concerts to update:")
    for concert_id in concerts_with_setlist[:10]:
        print(f"   Concert {concert_id}")

    if len(concerts_with_setlist) > 10:
        print(f"   ... and {len(concerts_with_setlist) - 10} more")

    # Confirm if not dry run
    if not dry_run:
        print(f"\n⚠️  About to set has_setlist=false for {len(concerts_with_setlist)} concerts.")
        response = input("\n   Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return

    # Update concerts
    print(f"\n🔄 Updating {len(concerts_with_setlist)} concerts...")

    batch = db.batch()
    batch_count = 0
    total_updated = 0

    for concert_id in concerts_with_setlist:
        concert_ref = db.collection('concerts').document(concert_id)

        if not dry_run:
            batch.update(concert_ref, {'has_setlist': False})
            batch_count += 1

            # Commit batch every 500 operations (Firestore limit)
            if batch_count >= 500:
                batch.commit()
                total_updated += batch_count
                print(f"   Updated: {total_updated}/{len(concerts_with_setlist)} concerts")
                batch = db.batch()
                batch_count = 0

    # Commit remaining
    if not dry_run and batch_count > 0:
        batch.commit()
        total_updated += batch_count

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    if dry_run:
        print(f"Would update: {len(concerts_with_setlist)} concerts")
        print("\n⚠️  This was a DRY RUN - no changes were made")
        print("   Run without --dry-run to actually update the flags")
    else:
        print(f"✅ Successfully updated: {total_updated} concerts")
        print("\n📝 Next steps:")
        print("   1. Run: python3 scripts/export_to_web.py")
        print("   2. Run: firebase deploy --only hosting")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Reset has_setlist flags to false')
    parser.add_argument('--dry-run', action='store_true', help='Test mode - don\'t make changes')

    args = parser.parse_args()

    reset_has_setlist_flags(dry_run=args.dry_run)
