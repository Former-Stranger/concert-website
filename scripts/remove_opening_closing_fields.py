#!/usr/bin/env python3
"""
Remove opening_song and closing_song fields from concert documents.

These fields are no longer needed because:
1. They are not exported to the website (removed from export_to_web.py)
2. The songs page calculates opening/closing/encore songs from full setlist data
3. Setlist.fm is the single source of truth for song data

This script will:
- Find all concerts with opening_song or closing_song fields
- Remove those fields from the documents
- Report on progress
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

def remove_opening_closing_fields(dry_run=False):
    """
    Remove opening_song and closing_song fields from all concerts

    Args:
        dry_run: If True, only report what would be removed without making changes
    """
    print("="*80)
    print("REMOVE OPENING/CLOSING SONG FIELDS")
    print("="*80)

    if dry_run:
        print("⚠️  DRY RUN MODE - No changes will be made")

    db = init_firebase()

    print("\n📊 Scanning concerts...")

    # Get all concerts
    all_concerts = db.collection('concerts').stream()

    concerts_to_update = []

    for doc in all_concerts:
        data = doc.to_dict()
        has_opening = 'opening_song' in data
        has_closing = 'closing_song' in data

        if has_opening or has_closing:
            concerts_to_update.append({
                'id': doc.id,
                'has_opening': has_opening,
                'has_closing': has_closing,
                'opening_value': data.get('opening_song') if has_opening else None,
                'closing_value': data.get('closing_song') if has_closing else None
            })

    print(f"   Found {len(concerts_to_update)} concerts with opening/closing fields")

    if len(concerts_to_update) == 0:
        print("\n✅ No concerts have opening_song or closing_song fields!")
        return

    # Show sample
    print("\n📋 Sample of concerts to update:")
    for concert in concerts_to_update[:5]:
        fields = []
        if concert['has_opening']:
            fields.append(f"opening_song='{concert['opening_value']}'")
        if concert['has_closing']:
            fields.append(f"closing_song='{concert['closing_value']}'")
        print(f"   Concert {concert['id']}: {', '.join(fields)}")

    if len(concerts_to_update) > 5:
        print(f"   ... and {len(concerts_to_update) - 5} more")

    # Confirm if not dry run
    if not dry_run:
        print(f"\n⚠️  About to remove opening_song and closing_song fields from {len(concerts_to_update)} concerts.")
        print("   This action cannot be undone.")
        response = input("\n   Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return

    # Process updates
    print(f"\n🔄 Processing {len(concerts_to_update)} concerts...")

    batch = db.batch()
    batch_count = 0
    total_updated = 0

    for concert in concerts_to_update:
        concert_ref = db.collection('concerts').document(concert['id'])

        # Build update dict to remove fields
        updates = {}
        if concert['has_opening']:
            updates['opening_song'] = firestore.DELETE_FIELD
        if concert['has_closing']:
            updates['closing_song'] = firestore.DELETE_FIELD

        if not dry_run:
            batch.update(concert_ref, updates)
            batch_count += 1

            # Commit batch every 500 operations (Firestore limit)
            if batch_count >= 500:
                batch.commit()
                total_updated += batch_count
                print(f"   Committed batch: {total_updated}/{len(concerts_to_update)} concerts updated")
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
        print(f"Would remove fields from: {len(concerts_to_update)} concerts")
        print("\n⚠️  This was a DRY RUN - no changes were made")
        print("   Run without --dry-run to actually remove the fields")
    else:
        print(f"✅ Successfully removed fields from: {total_updated} concerts")
        print("\n📝 Fields removed:")
        opening_count = sum(1 for c in concerts_to_update if c['has_opening'])
        closing_count = sum(1 for c in concerts_to_update if c['has_closing'])
        print(f"   - opening_song: {opening_count} concerts")
        print(f"   - closing_song: {closing_count} concerts")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Remove opening_song and closing_song fields from concerts')
    parser.add_argument('--dry-run', action='store_true', help='Test mode - don\'t make changes')

    args = parser.parse_args()

    remove_opening_closing_fields(dry_run=args.dry_run)
