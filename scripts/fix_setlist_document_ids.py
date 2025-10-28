#!/usr/bin/env python3
"""
Fix setlist document IDs to use concert_id instead of random IDs.

This script will:
1. Read all current setlists (with random doc IDs)
2. Delete them
3. Re-create them using concert_id as the document ID
4. Update has_setlist flags to match reality
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

def fix_setlist_document_ids():
    """Fix setlist document IDs to use concert_id"""

    print("\n" + "="*80)
    print("FIXING SETLIST DOCUMENT IDS")
    print("="*80)
    print("\nThis will:")
    print("  1. Read all current setlists")
    print("  2. Keep only setlists with actual song data")
    print("  3. Delete all current setlists")
    print("  4. Re-create them using concert_id as document ID")
    print("  5. Update has_setlist flags")

    response = input("\nProceed? (yes/no): ")
    if response.lower() != 'yes':
        print("Operation cancelled.")
        return

    init_firebase()
    db = firestore.client()

    # Step 1: Read all current setlists
    print("\n" + "="*80)
    print("STEP 1: Reading current setlists")
    print("="*80)

    all_setlists = list(db.collection('setlists').stream())
    print(f"Found {len(all_setlists)} setlist documents")

    # Separate setlists with data from empty ones
    setlists_with_data = []
    empty_setlists = []
    invalid_setlists = []

    for doc in all_setlists:
        data = doc.to_dict()
        concert_id = data.get('concert_id')
        songs = data.get('songs', [])

        if not concert_id:
            invalid_setlists.append((doc.id, data))
            continue

        if songs and len(songs) > 0:
            setlists_with_data.append((concert_id, data))
        else:
            empty_setlists.append((concert_id, data))

    print(f"\nAnalysis:")
    print(f"  ✓ {len(setlists_with_data)} setlists with song data")
    print(f"  ✓ {len(empty_setlists)} empty setlists (will be discarded)")
    print(f"  ⚠ {len(invalid_setlists)} invalid setlists (no concert_id)")

    if invalid_setlists:
        print(f"\nInvalid setlists found:")
        for doc_id, data in invalid_setlists[:5]:
            print(f"  - Document ID: {doc_id}")

    # Step 2: Delete all current setlists
    print("\n" + "="*80)
    print("STEP 2: Deleting all current setlists")
    print("="*80)

    batch = db.batch()
    count = 0

    for doc in all_setlists:
        batch.delete(doc.reference)
        count += 1

        if count % 500 == 0:
            batch.commit()
            print(f"  Deleted {count} documents...")
            batch = db.batch()

    if count % 500 != 0:
        batch.commit()

    print(f"  ✓ Deleted all {len(all_setlists)} setlist documents")

    # Step 3: Re-create setlists with correct document IDs
    print("\n" + "="*80)
    print("STEP 3: Re-creating setlists with concert_id as document ID")
    print("="*80)

    batch = db.batch()
    count = 0
    skipped = 0

    for concert_id, data in setlists_with_data:
        # Use concert_id as the document ID (convert to string)
        doc_ref = db.collection('setlists').document(str(concert_id))
        batch.set(doc_ref, data)
        count += 1

        if count % 500 == 0:
            batch.commit()
            print(f"  Created {count} setlists...")
            batch = db.batch()

    if count % 500 != 0:
        batch.commit()

    print(f"  ✓ Created {count} setlists with correct document IDs")

    # Step 4: Update has_setlist flags
    print("\n" + "="*80)
    print("STEP 4: Updating has_setlist flags")
    print("="*80)

    # Get all concert IDs that now have setlists (as strings)
    setlist_concert_ids = set(str(concert_id) for concert_id, _ in setlists_with_data)
    print(f"  {len(setlist_concert_ids)} concerts have setlists")

    # Update concert flags
    concerts = list(db.collection('concerts').stream())
    print(f"  {len(concerts)} total concerts")

    batch = db.batch()
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
                print(f"  Progress: +{updated_to_true} true, +{updated_to_false} false...")
                batch = db.batch()
                batch_count = 0
        else:
            already_correct += 1

    if batch_count > 0:
        batch.commit()

    print(f"\n  ✓ Updated {updated_to_true} concerts to has_setlist=True")
    print(f"  ✓ Updated {updated_to_false} concerts to has_setlist=False")
    print(f"  ✓ {already_correct} concerts were already correct")

    # Final summary
    print("\n" + "="*80)
    print("✓ OPERATION COMPLETE!")
    print("="*80)
    print(f"\nResults:")
    print(f"  ✓ {count} setlists now using concert_id as document ID")
    print(f"  ✓ {updated_to_true + updated_to_false} concert flags updated")
    print(f"  ✓ {len(empty_setlists)} empty setlists removed")
    print(f"\nDatabase state:")
    print(f"  ✓ {len(setlist_concert_ids)} concerts with setlists")
    print(f"  ✓ {len(concerts) - len(setlist_concert_ids)} concerts without setlists")

    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Run: python3 scripts/export_to_web.py")
    print("2. Deploy: firebase deploy --only hosting")
    print("   OR use: ./deploy.sh")

if __name__ == '__main__':
    fix_setlist_document_ids()
