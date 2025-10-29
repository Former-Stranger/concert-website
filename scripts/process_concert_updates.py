#!/usr/bin/env python3
"""
Process concert updates from reviewed CSV file

Reads the concerts_for_review.csv (after manual edits) and applies changes to Firestore.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import csv
import sys
from datetime import datetime


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
            sys.exit(1)
    return firestore.client()


def process_updates(csv_file, dry_run=False):
    """
    Process updates from CSV file

    Args:
        csv_file: Path to reviewed CSV file
        dry_run: If True, show what would be updated without making changes
    """

    print("=" * 80)
    print("PROCESSING CONCERT UPDATES")
    print("=" * 80)

    if dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made to Firestore\n")

    # Read CSV
    print(f"\nReading CSV: {csv_file}")
    updates = []

    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Only process rows with ACTION set
                action = row.get('ACTION', '').strip().upper()
                if action in ['UPDATE', 'DELETE']:
                    updates.append(row)
    except FileNotFoundError:
        print(f"✗ Error: File not found: {csv_file}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error reading CSV: {e}")
        sys.exit(1)

    print(f"Found {len(updates)} concerts to process")

    if len(updates) == 0:
        print("\n✓ No updates to process (no rows with ACTION=UPDATE or ACTION=DELETE)")
        return

    # Initialize Firebase
    db = init_firebase()

    # Statistics
    stats = {
        'updated': 0,
        'deleted': 0,
        'errors': 0,
        'skipped': 0
    }

    # Process each update
    print("\n" + "=" * 80)
    print("PROCESSING UPDATES")
    print("=" * 80 + "\n")

    for i, row in enumerate(updates, 1):
        concert_id = row['concert_id']
        action = row.get('ACTION', '').strip().upper()

        print(f"[{i}/{len(updates)}] Concert {concert_id}: {row.get('date')} - {row.get('artists_list', '')[:50]}")

        if action == 'DELETE':
            print(f"  ⚠️  DELETE requested")
            if not dry_run:
                try:
                    db.collection('concerts').document(concert_id).delete()
                    print(f"  ✓ Deleted from Firestore")
                    stats['deleted'] += 1
                except Exception as e:
                    print(f"  ✗ Error deleting: {e}")
                    stats['errors'] += 1
            else:
                print(f"  [DRY RUN] Would delete concert {concert_id}")

        elif action == 'UPDATE':
            # Build update data
            update_data = {}
            changes = []

            # Check NEW_event_type
            new_event_type = row.get('NEW_event_type', '').strip()
            if new_event_type:
                # Note: This adds a NEW field - we'll track it but not store yet
                # until schema migration is complete
                changes.append(f"event_type → {new_event_type}")

            # Check NEW_event_name
            new_event_name = row.get('NEW_event_name', '').strip()
            if new_event_name:
                # For now, store in festival_name field (legacy)
                update_data['festival_name'] = new_event_name
                changes.append(f"festival_name → {new_event_name}")
            elif row.get('current_festival_name', '').strip() != new_event_name:
                # User cleared the field
                update_data['festival_name'] = None
                changes.append(f"festival_name → NULL")

            # Check NEW_tour_name
            new_tour_name = row.get('NEW_tour_name', '').strip()
            if new_tour_name:
                # Note: tour_name doesn't exist yet in schema
                # We'll note it but not store
                changes.append(f"tour_name → {new_tour_name} (NOTE ONLY)")

            # Check NEW_notes
            new_notes = row.get('NEW_notes', '').strip()
            if new_notes:
                changes.append(f"notes → {new_notes}")

            if not changes:
                print(f"  ⚠️  No changes specified")
                stats['skipped'] += 1
                continue

            # Display changes
            for change in changes:
                print(f"    • {change}")

            # Apply updates
            if update_data and not dry_run:
                try:
                    update_data['updated_at'] = firestore.SERVER_TIMESTAMP
                    db.collection('concerts').document(concert_id).update(update_data)
                    print(f"  ✓ Updated in Firestore")
                    stats['updated'] += 1
                except Exception as e:
                    print(f"  ✗ Error updating: {e}")
                    stats['errors'] += 1
            elif dry_run:
                print(f"  [DRY RUN] Would update concert {concert_id}")
                stats['updated'] += 1
            else:
                print(f"  ⚠️  No Firestore updates (only notes)")
                stats['skipped'] += 1

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Updated:  {stats['updated']}")
    print(f"Deleted:  {stats['deleted']}")
    print(f"Errors:   {stats['errors']}")
    print(f"Skipped:  {stats['skipped']}")

    if dry_run:
        print("\n⚠️  This was a DRY RUN - no changes were made")
        print("   Run without --dry-run to apply changes")
    else:
        print("\n✓ Updates applied to Firestore")
        print("   Run: python3 scripts/export_to_web.py")
        print("   Then: firebase deploy --only hosting")

    print("=" * 80)

    # Log tour_name entries for manual review
    tour_entries = [row for row in updates if row.get('NEW_tour_name', '').strip()]
    if tour_entries:
        print("\n" + "=" * 80)
        print("TOUR NAMES TO ADD MANUALLY (Schema doesn't have tour_name field yet)")
        print("=" * 80)
        for row in tour_entries:
            print(f"Concert {row['concert_id']}: tour_name = \"{row['NEW_tour_name']}\"")
        print("\nThese need to be added after schema migration.")
        print("=" * 80)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Process concert updates from CSV')
    parser.add_argument('csv_file', help='Path to reviewed CSV file')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying them')

    args = parser.parse_args()

    process_updates(args.csv_file, dry_run=args.dry_run)
