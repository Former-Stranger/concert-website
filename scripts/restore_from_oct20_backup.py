#!/usr/bin/env python3
"""
Restore data from October 20th backup database to fix data corruption.

This script will:
1. Restore concerts collection from backup
2. Restore artists collection from backup
3. Restore venues collection from backup
4. Fix setlists to use concert_id as document ID (not random IDs)
5. Update has_setlist flags to match actual data
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
            print("\nTo fix this, run:")
            print("  gcloud auth application-default login")
            sys.exit(1)

def restore_collection(backup_db, default_db, collection_name, clear_first=True):
    """Restore a collection from backup to default database"""

    print(f"\n{'='*80}")
    print(f"RESTORING {collection_name.upper()} COLLECTION")
    print(f"{'='*80}")

    # Get backup data
    print(f"\n1. Fetching {collection_name} from backup database...")
    backup_docs = list(backup_db.collection(collection_name).stream())
    print(f"   Found {len(backup_docs)} documents in backup")

    if clear_first:
        # Clear existing data
        print(f"\n2. Clearing existing {collection_name} in default database...")
        existing_docs = list(default_db.collection(collection_name).stream())
        print(f"   Found {len(existing_docs)} existing documents to delete")

        batch = default_db.batch()
        count = 0
        for doc in existing_docs:
            batch.delete(doc.reference)
            count += 1
            if count % 500 == 0:
                batch.commit()
                print(f"   Deleted {count} documents...")
                batch = default_db.batch()

        if count % 500 != 0:
            batch.commit()
        print(f"   ✓ Cleared {len(existing_docs)} documents")

    # Copy from backup
    print(f"\n3. Copying {collection_name} from backup to default database...")
    batch = default_db.batch()
    count = 0

    for doc in backup_docs:
        data = doc.to_dict()
        # Use the same document ID as in backup
        doc_ref = default_db.collection(collection_name).document(doc.id)
        batch.set(doc_ref, data)
        count += 1

        if count % 500 == 0:
            batch.commit()
            print(f"   Copied {count} documents...")
            batch = default_db.batch()

    if count % 500 != 0:
        batch.commit()

    print(f"   ✓ Restored {count} documents")
    return count

def restore_setlists_with_correct_ids(backup_db, default_db):
    """Restore setlists using concert_id as document ID"""

    print(f"\n{'='*80}")
    print(f"RESTORING SETLISTS WITH CORRECT DOCUMENT IDS")
    print(f"{'='*80}")

    # Get backup setlists
    print(f"\n1. Fetching setlists from backup database...")
    backup_setlists = list(backup_db.collection('setlists').stream())
    print(f"   Found {len(backup_setlists)} setlists in backup")

    # Count setlists with actual data
    setlists_with_songs = []
    setlists_empty = []

    for doc in backup_setlists:
        data = doc.to_dict()
        songs = data.get('songs', [])
        if songs and len(songs) > 0:
            setlists_with_songs.append((doc, data))
        else:
            setlists_empty.append((doc, data))

    print(f"   - {len(setlists_with_songs)} setlists with songs")
    print(f"   - {len(setlists_empty)} setlists empty/placeholder")

    # Clear existing setlists
    print(f"\n2. Clearing existing setlists in default database...")
    existing_setlists = list(default_db.collection('setlists').stream())
    print(f"   Found {len(existing_setlists)} existing setlists to delete")

    batch = default_db.batch()
    count = 0
    for doc in existing_setlists:
        batch.delete(doc.reference)
        count += 1
        if count % 500 == 0:
            batch.commit()
            print(f"   Deleted {count} setlists...")
            batch = default_db.batch()

    if count % 500 != 0:
        batch.commit()
    print(f"   ✓ Cleared {len(existing_setlists)} setlists")

    # Copy setlists using concert_id as document ID
    print(f"\n3. Copying setlists with concert_id as document ID...")
    batch = default_db.batch()
    count = 0
    skipped = 0

    for doc, data in setlists_with_songs:
        concert_id = data.get('concert_id')
        if not concert_id:
            print(f"   WARNING: Setlist {doc.id} has no concert_id - skipping")
            skipped += 1
            continue

        # Use concert_id as document ID (convert to string)
        doc_ref = default_db.collection('setlists').document(str(concert_id))
        batch.set(doc_ref, data)
        count += 1

        if count % 500 == 0:
            batch.commit()
            print(f"   Copied {count} setlists...")
            batch = default_db.batch()

    if count % 500 != 0:
        batch.commit()

    print(f"   ✓ Restored {count} setlists with correct document IDs")
    if skipped > 0:
        print(f"   ⚠ Skipped {skipped} setlists without concert_id")

    return count

def update_has_setlist_flags(default_db):
    """Update has_setlist flags based on actual setlist existence"""

    print(f"\n{'='*80}")
    print(f"UPDATING HAS_SETLIST FLAGS")
    print(f"{'='*80}")

    # Get all setlist IDs (now these are concert_ids)
    print("\n1. Getting setlist concert IDs...")
    setlist_concert_ids = set()
    for doc in default_db.collection('setlists').stream():
        setlist_concert_ids.add(doc.id)

    print(f"   Found {len(setlist_concert_ids)} concerts with setlists")

    # Update concert flags
    print("\n2. Updating concert has_setlist flags...")
    concerts = list(default_db.collection('concerts').stream())

    batch = default_db.batch()
    batch_count = 0
    updated_to_true = 0
    updated_to_false = 0
    already_correct = 0

    for concert_doc in concerts:
        concert_id = concert_doc.id
        data = concert_doc.to_dict()
        current_flag = data.get('has_setlist', False)
        should_be_true = concert_id in setlist_concert_ids

        if current_flag != should_be_true:
            batch.update(concert_doc.reference, {'has_setlist': should_be_true})
            batch_count += 1

            if should_be_true:
                updated_to_true += 1
            else:
                updated_to_false += 1

            if batch_count >= 500:
                batch.commit()
                batch = default_db.batch()
                batch_count = 0
                print(f"   Progress: +{updated_to_true} true, +{updated_to_false} false...")
        else:
            already_correct += 1

    if batch_count > 0:
        batch.commit()

    print(f"\n   ✓ Updated {updated_to_true} concerts to has_setlist=True")
    print(f"   ✓ Updated {updated_to_false} concerts to has_setlist=False")
    print(f"   ✓ {already_correct} concerts already correct")

    return updated_to_true, updated_to_false

def main():
    """Main restoration process"""

    print("\n" + "="*80)
    print("CONCERT DATABASE RESTORATION FROM OCTOBER 20TH BACKUP")
    print("="*80)
    print("\nThis will restore:")
    print("  - Concerts collection (all concert data)")
    print("  - Artists collection (all artist data)")
    print("  - Venues collection (all venue data)")
    print("  - Setlists collection (with concert_id as document ID)")
    print("\nThis will NOT touch:")
    print("  - concert_notes")
    print("  - concert_comments")
    print("  - concert_photos")
    print("  - pending_setlist_submissions")

    response = input("\nProceed with restoration? (yes/no): ")
    if response.lower() != 'yes':
        print("Restoration cancelled.")
        return

    # Initialize Firebase
    init_firebase()

    # Get database references
    default_db = firestore.client()

    # Try both possible backup database names
    backup_db = None
    for db_name in ['restored-oct20-v2', 'restored-oct20']:
        try:
            backup_db = firestore.client(database_id=db_name)
            # Test if we can access it
            list(backup_db.collection('concerts').limit(1).stream())
            print(f"\n✓ Connected to backup database: {db_name}")
            break
        except Exception as e:
            print(f"Cannot access {db_name}: {e}")

    if not backup_db:
        print("\nERROR: Cannot access backup database!")
        print("Available databases should include 'restored-oct20-v2' or 'restored-oct20'")
        sys.exit(1)

    # Restore collections
    concerts_count = restore_collection(backup_db, default_db, 'concerts')
    artists_count = restore_collection(backup_db, default_db, 'artists')
    venues_count = restore_collection(backup_db, default_db, 'venues')
    setlists_count = restore_setlists_with_correct_ids(backup_db, default_db)

    # Update flags
    updated_true, updated_false = update_has_setlist_flags(default_db)

    # Final summary
    print("\n" + "="*80)
    print("✓ RESTORATION COMPLETE!")
    print("="*80)
    print(f"\nRestored from October 20th backup:")
    print(f"  ✓ {concerts_count} concerts")
    print(f"  ✓ {artists_count} artists")
    print(f"  ✓ {venues_count} venues")
    print(f"  ✓ {setlists_count} setlists (now using concert_id as document ID)")
    print(f"\nUpdated has_setlist flags:")
    print(f"  ✓ {updated_true} concerts set to has_setlist=true")
    print(f"  ✓ {updated_false} concerts set to has_setlist=false")

    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Run: python3 scripts/export_to_web.py")
    print("2. Deploy: firebase deploy --only hosting")
    print("   OR use: ./deploy.sh")
    print("\nThis will regenerate all JSON files with the restored data.")

if __name__ == '__main__':
    main()
