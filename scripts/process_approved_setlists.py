#!/usr/bin/env python3
"""
Manually process approved setlist submissions that haven't been processed yet.
This is useful for submissions that were approved before the Cloud Function was deployed.
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
            print("\nOr download a service account key and set GOOGLE_APPLICATION_CREDENTIALS:")
            print("  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json")
            sys.exit(1)
    return firestore.client()


def process_setlist_data(setlist_data):
    """Parse setlist.fm data and format for Firestore"""
    songs = []
    position = 1
    has_encore = False

    if setlist_data and 'sets' in setlist_data and 'set' in setlist_data['sets']:
        for set_item in setlist_data['sets']['set']:
            set_name = set_item.get('name') or 'Main Set'
            encore = set_item.get('encore', 0)

            if encore > 0:
                has_encore = True

            if 'song' in set_item:
                for song in set_item['song']:
                    songs.append({
                        'position': position,
                        'name': song['name'],
                        'set_name': set_name,
                        'encore': encore,
                        'is_cover': 'cover' in song and song['cover'] is not None,
                        'cover_artist': song['cover']['name'] if 'cover' in song and song['cover'] else None,
                        'is_tape': 'tape' in song and song['tape'] is not None,
                        'info': song.get('info')
                    })
                    position += 1

    return songs, len(songs), has_encore


def process_approved_setlists():
    """Find and process all approved submissions that haven't been processed"""
    db = init_firebase()

    print("Searching for approved submissions that need processing...")
    print("=" * 80)

    # Query for approved submissions that haven't been processed
    submissions_ref = db.collection('pending_setlist_submissions')
    query = submissions_ref.where('status', '==', 'approved')

    approved_submissions = query.stream()

    processed_count = 0
    skipped_count = 0
    error_count = 0

    for submission_doc in approved_submissions:
        submission_id = submission_doc.id
        submission_data = submission_doc.to_dict()

        # Skip if already processed
        if submission_data.get('processed'):
            print(f"\n✓ Skipping {submission_id} - already processed")
            skipped_count += 1
            continue

        concert_id = str(submission_data.get('concertId'))  # Ensure it's a string
        setlist_data = submission_data.get('setlistData')

        print(f"\n📝 Processing submission {submission_id} for concert {concert_id}")

        try:
            # Parse setlist data
            songs, song_count, has_encore = process_setlist_data(setlist_data)

            if song_count == 0:
                print(f"   ⚠️  No songs found in setlist data")
                error_count += 1
                continue

            # Check if setlist already exists for this concert
            existing_setlists_query = db.collection('setlists').where('concert_id', '==', concert_id).limit(1).stream()
            existing_setlists = list(existing_setlists_query)

            if existing_setlists:
                # Update existing setlist
                setlist_ref = existing_setlists[0].reference
                print(f"   📝 Updating existing setlist")
            else:
                # Create new setlist
                setlist_ref = db.collection('setlists').document()
                print(f"   ✨ Creating new setlist")

            # Write setlist data
            setlist_ref.set({
                'concert_id': concert_id,
                'setlistfm_id': submission_data.get('setlistfmId'),
                'setlistfm_url': submission_data.get('setlistfmUrl'),
                'song_count': song_count,
                'has_encore': has_encore,
                'songs': songs,
                'created_at': firestore.SERVER_TIMESTAMP,
                'fetched_at': firestore.SERVER_TIMESTAMP
            })

            # Update concert to mark that it has a setlist
            concert_ref = db.collection('concerts').document(concert_id)
            concert_ref.update({
                'has_setlist': True,
                'updated_at': firestore.SERVER_TIMESTAMP
            })

            # Mark submission as processed
            submission_doc.reference.update({
                'processed': True,
                'processed_at': firestore.SERVER_TIMESTAMP
            })

            print(f"   ✅ Successfully imported setlist ({song_count} songs)")
            processed_count += 1

        except Exception as e:
            print(f"   ❌ Error processing submission: {e}")

            # Mark submission with error
            submission_doc.reference.update({
                'import_error': str(e),
                'import_error_at': firestore.SERVER_TIMESTAMP
            })

            error_count += 1

    print("\n" + "=" * 80)
    print(f"✅ Processed: {processed_count}")
    print(f"⏭️  Skipped (already processed): {skipped_count}")
    print(f"❌ Errors: {error_count}")
    print("=" * 80)

    if processed_count > 0:
        print("\nNext steps:")
        print("1. Run the export script to update JSON files:")
        print("   python3 scripts/export_to_web.py")
        print("2. Deploy the updated website:")
        print("   firebase deploy --only hosting")


if __name__ == "__main__":
    process_approved_setlists()
