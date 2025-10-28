#!/usr/bin/env python3
"""
Copy setlists from the restored-oct20 database to the default database.
This restores the complete setlist data from the October 20th backup.
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

def copy_setlists():
    """Copy all setlists from restored-oct20 to default database"""

    print("\n" + "=" * 80)
    print("COPYING SETLISTS FROM OCTOBER 20TH BACKUP")
    print("=" * 80)

    # Initialize Firebase
    init_firebase()

    # Get both databases
    default_db = firestore.client()
    restored_db = firestore.client(database='restored-oct20')

    print("\n1. Fetching setlists from restored backup...")
    restored_setlists = list(restored_db.collection('setlists').stream())
    print(f"   Found {len(restored_setlists)} setlists in backup")

    # Check how many have songs
    with_songs = sum(1 for doc in restored_setlists if len(doc.to_dict().get('songs', [])) > 0)
    print(f"   - {with_songs} setlists with songs")
    print(f"   - {len(restored_setlists) - with_songs} setlists without songs")

    print("\n2. Clearing existing setlists in default database...")
    existing = list(default_db.collection('setlists').stream())
    print(f"   Found {existing} existing setlists to delete")

    batch = default_db.batch()
    count = 0
    for doc in existing:
        batch.delete(doc.reference)
        count += 1
        if count % 500 == 0:
            batch.commit()
            print(f"   Deleted {count} setlists...")
            batch = default_db.batch()

    if count % 500 != 0:
        batch.commit()
    print(f"   ✓ Deleted {len(existing)} existing setlists")

    print("\n3. Copying setlists from backup to default database...")
    batch = default_db.batch()
    count = 0

    for doc in restored_setlists:
        data = doc.to_dict()
        # Create new document with same data
        new_ref = default_db.collection('setlists').document()
        batch.set(new_ref, data)
        count += 1

        if count % 500 == 0:
            batch.commit()
            print(f"   Copied {count} setlists...")
            batch = default_db.batch()

    if count % 500 != 0:
        batch.commit()

    print(f"   ✓ Copied {count} setlists")

    print("\n4. Updating has_setlist flags in concerts collection...")
    # Get all concerts
    concerts_ref = default_db.collection('concerts')
    all_concerts = list(concerts_ref.stream())

    # Build map of concert_id -> has songs
    setlist_map = {}
    for doc in restored_setlists:
        data = doc.to_dict()
        concert_id = data.get('concert_id')
        has_songs = len(data.get('songs', [])) > 0
        if concert_id:
            setlist_map[concert_id] = has_songs

    batch = default_db.batch()
    count = 0
    updated = 0

    for concert_doc in all_concerts:
        concert_id = concert_doc.id
        current_flag = concert_doc.to_dict().get('has_setlist', False)
        should_have = setlist_map.get(concert_id, False)

        if current_flag != should_have:
            batch.update(concert_doc.reference, {'has_setlist': should_have})
            count += 1
            updated += 1

            if count % 500 == 0:
                batch.commit()
                print(f"   Updated {updated} concerts...")
                batch = default_db.batch()
                count = 0

    if count > 0:
        batch.commit()

    print(f"   ✓ Updated {updated} concert has_setlist flags")

    print("\n" + "=" * 80)
    print("✓ SETLIST RESTORATION COMPLETE!")
    print("=" * 80)
    print(f"\nRestored {len(restored_setlists)} setlists from October 20th backup")
    print(f"  - {with_songs} setlists with complete song data")
    print(f"  - {len(restored_setlists) - with_songs} empty setlist placeholders")
    print(f"\nUpdated {updated} concert records with correct has_setlist flags")
    print("\nNext steps:")
    print("  1. Run: python3 scripts/export_to_web.py")
    print("  2. Deploy: firebase deploy --only hosting")
    print("  3. Delete temp database: gcloud firestore databases delete restored-oct20")

if __name__ == '__main__':
    copy_setlists()
