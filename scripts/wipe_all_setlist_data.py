#!/usr/bin/env python3
"""
Complete wipe of all setlist data from Firestore database.
This script will:
1. Delete all documents from the 'setlists' collection
2. Delete all documents from the 'pending_setlist_submissions' collection
3. Set has_setlist=False for all concerts
4. Clear opening_song and closing_song fields from all concerts

WARNING: This is destructive and cannot be undone!
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


def delete_collection(db, collection_name, batch_size=100):
    """Delete all documents in a collection"""
    collection_ref = db.collection(collection_name)
    deleted = 0

    while True:
        docs = collection_ref.limit(batch_size).stream()
        docs_list = list(docs)

        if not docs_list:
            break

        batch = db.batch()
        for doc in docs_list:
            batch.delete(doc.reference)
            deleted += 1

        batch.commit()
        print(f"   Deleted {deleted} documents from {collection_name}...")

    return deleted


def clear_concert_setlist_flags(db):
    """Set has_setlist=False and clear opening/closing song for all concerts"""
    concerts_ref = db.collection('concerts')
    concerts = concerts_ref.stream()

    updated = 0
    batch = db.batch()
    batch_count = 0

    for concert_doc in concerts:
        concert_data = concert_doc.to_dict()

        # Check if any setlist-related fields exist
        needs_update = (
            concert_data.get('has_setlist', False) or
            concert_data.get('opening_song') is not None or
            concert_data.get('closing_song') is not None
        )

        if needs_update:
            batch.update(concert_doc.reference, {
                'has_setlist': False,
                'opening_song': firestore.DELETE_FIELD,
                'closing_song': firestore.DELETE_FIELD
            })
            updated += 1
            batch_count += 1

            # Commit in batches of 500 (Firestore limit)
            if batch_count >= 500:
                batch.commit()
                print(f"   Updated {updated} concerts...")
                batch = db.batch()
                batch_count = 0

    # Commit remaining
    if batch_count > 0:
        batch.commit()

    return updated


def main():
    print("=" * 70)
    print("SETLIST DATA WIPE SCRIPT")
    print("=" * 70)
    print("\nWARNING: This will permanently delete:")
    print("  - All setlist documents")
    print("  - All pending setlist submissions")
    print("  - All has_setlist flags")
    print("  - All opening_song and closing_song fields")
    print("\nThis action CANNOT be undone!")
    print("=" * 70)

    response = input("\nType 'DELETE ALL SETLISTS' to proceed: ")
    if response != "DELETE ALL SETLISTS":
        print("\nAborted. No changes made.")
        sys.exit(0)

    print("\nInitializing Firebase...")
    db = init_firebase()

    # 1. Delete all setlists
    print("\n1. Deleting all setlist documents...")
    setlists_deleted = delete_collection(db, 'setlists')
    print(f"   ✓ Deleted {setlists_deleted} setlist documents")

    # 2. Delete all pending submissions
    print("\n2. Deleting all pending setlist submissions...")
    submissions_deleted = delete_collection(db, 'pending_setlist_submissions')
    print(f"   ✓ Deleted {submissions_deleted} pending submissions")

    # 3. Clear concert flags
    print("\n3. Clearing has_setlist flags and opening/closing songs...")
    concerts_updated = clear_concert_setlist_flags(db)
    print(f"   ✓ Updated {concerts_updated} concerts")

    print("\n" + "=" * 70)
    print("WIPE COMPLETE!")
    print("=" * 70)
    print("\nSummary:")
    print(f"  - Setlists deleted: {setlists_deleted}")
    print(f"  - Submissions deleted: {submissions_deleted}")
    print(f"  - Concerts updated: {concerts_updated}")
    print("\nNext steps:")
    print("  1. Run: python3 scripts/export_to_web.py")
    print("  2. Deploy to Firebase: firebase deploy --only hosting")
    print("=" * 70)


if __name__ == '__main__':
    main()
