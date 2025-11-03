#!/usr/bin/env python3
"""
Execute artist merge plan
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json
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
            sys.exit(1)
    return firestore.client()


def merge_artists(db, keep_id, keep_name, merge_id, merge_name):
    """Merge two artist documents"""
    print(f"\nMerging: '{merge_name}' → '{keep_name}'")

    # Find concerts that reference the artist being merged
    concerts_ref = db.collection('concerts')
    concerts_to_update = []

    for concert_doc in concerts_ref.stream():
        concert_data = concert_doc.to_dict()
        artists = concert_data.get('artists', [])

        needs_update = False
        updated_artists = []

        for artist in artists:
            if artist.get('artist_id') == merge_id:
                needs_update = True
                updated_artist = artist.copy()
                updated_artist['artist_id'] = keep_id
                updated_artist['artist_name'] = keep_name
                updated_artists.append(updated_artist)
                print(f"  Concert {concert_doc.id}: Updated")
            else:
                updated_artists.append(artist)

        if needs_update:
            concerts_to_update.append({
                'ref': concert_doc.reference,
                'artists': updated_artists
            })

    if not concerts_to_update:
        print(f"  No concerts to update")
    else:
        print(f"  Updating {len(concerts_to_update)} concerts...")
        batch = db.batch()
        batch_count = 0

        for concert in concerts_to_update:
            batch.update(concert['ref'], {
                'artists': concert['artists'],
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            batch_count += 1

            if batch_count >= 500:
                batch.commit()
                print(f"    Committed batch of {batch_count}")
                batch = db.batch()
                batch_count = 0

        if batch_count > 0:
            batch.commit()
            print(f"    Committed batch of {batch_count}")

    # Delete the merged artist document
    print(f"  Deleting duplicate artist document...")
    db.collection('artists').document(merge_id).delete()

    print(f"  ✅ Merged successfully")


def execute_merge_plan(db, plan_file):
    """Execute all merges in the plan"""
    with open(plan_file, 'r') as f:
        plan = json.load(f)

    print(f"{'='*80}")
    print(f"EXECUTING MERGE PLAN")
    print(f"{'='*80}")
    print(f"Total merges to perform: {len(plan)}\n")

    for i, merge in enumerate(plan, 1):
        print(f"\n[{i}/{len(plan)}] {merge.get('comment', '')}")
        merge_artists(
            db,
            merge['keep_id'],
            merge['keep_name'],
            merge['merge_id'],
            merge['merge_name']
        )

    print(f"\n{'='*80}")
    print(f"✅ ALL MERGES COMPLETE!")
    print(f"{'='*80}")
    print(f"Merged {len(plan)} duplicate artists")
    print(f"\nNext step: Run export and deploy to update static JSON files")
    print(f"  ./deploy.sh")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: execute_merge_plan.py <plan_file.json>")
        sys.exit(1)

    plan_file = sys.argv[1]
    db = init_firebase()

    print("\n⚠️  WARNING: This will modify your Firestore database!")
    print(f"   Plan file: {plan_file}")
    confirm = input("\nProceed with merges? (yes/no): ").strip().lower()

    if confirm == 'yes':
        execute_merge_plan(db, plan_file)
    else:
        print("Cancelled.")
