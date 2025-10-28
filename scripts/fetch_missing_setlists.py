#!/usr/bin/env python3
"""
Fetch missing setlists from setlist.fm for concerts with empty setlist documents.
This script will attempt to find and import setlists for the 379 concerts marked as "Not found".
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys
from datetime import datetime
from setlistfm_client import SetlistFMClient

# Setlist.fm API key
SETLISTFM_API_KEY = "DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE"

def init_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'earplugs-and-memories'),
            })
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            sys.exit(1)
    return firestore.client()

def fetch_missing_setlists(limit=None):
    """
    Fetch setlists for concerts with empty setlist documents

    Args:
        limit: Optional limit on number of concerts to process (for testing)
    """
    print("\n" + "=" * 80)
    print("FETCHING MISSING SETLISTS FROM SETLIST.FM")
    print("=" * 80)

    db = init_firebase()
    client = SetlistFMClient(SETLISTFM_API_KEY)

    # Get all empty setlist documents
    print("\n📊 Finding concerts with empty setlists...")
    empty_setlists = list(db.collection('setlists').where('song_count', '==', 0).stream())

    total = len(empty_setlists)
    if limit:
        empty_setlists = empty_setlists[:limit]

    print(f"   Found {total} concerts with empty setlists")
    if limit:
        print(f"   Processing first {limit} concerts (test mode)")

    # Statistics
    found = 0
    still_not_found = 0
    errors = 0
    updated = 0

    print(f"\n🔍 Starting setlist fetch...")
    print(f"   Rate limit: ~1.67 requests/second")
    print(f"   Estimated time: {len(empty_setlists) * 0.6 / 60:.1f} minutes\n")

    for i, setlist_doc in enumerate(empty_setlists, 1):
        setlist_data = setlist_doc.to_dict()
        concert_id = setlist_data.get('concert_id')

        # Get concert details
        concert_ref = db.collection('concerts').document(concert_id)
        concert = concert_ref.get()

        if not concert.exists:
            print(f"❌ [{i}/{len(empty_setlists)}] Concert {concert_id}: Not found in database")
            errors += 1
            continue

        concert_data = concert.to_dict()

        # Extract concert info
        artists = concert_data.get('artists', [])
        if not artists:
            print(f"⏭️  [{i}/{len(empty_setlists)}] Concert {concert_id}: No artists listed")
            errors += 1
            continue

        artist_name = artists[0].get('artist_name', '')
        venue_name = concert_data.get('venue_name', '')
        city = concert_data.get('city', '')
        state = concert_data.get('state', '')
        date_str = concert_data.get('date', '')

        if not date_str:
            print(f"⏭️  [{i}/{len(empty_setlists)}] Concert {concert_id}: No date")
            errors += 1
            continue

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            print(f"⏭️  [{i}/{len(empty_setlists)}] Concert {concert_id}: Invalid date format")
            errors += 1
            continue

        # Show progress every 10 concerts
        if i % 10 == 0:
            print(f"\n📈 Progress: {i}/{len(empty_setlists)} ({i*100//len(empty_setlists)}%)")
            print(f"   Found: {found} | Not found: {still_not_found} | Errors: {errors}")

        # Search for setlist
        try:
            setlist_result = client.find_setlist_for_concert(
                artist_name=artist_name,
                date=date,
                venue_name=venue_name,
                city=city,
                state=state
            )

            if setlist_result:
                # Extract songs
                songs = client.extract_songs_from_setlist(setlist_result)

                if songs:
                    # Update setlist document
                    has_encore = any(s['encore'] > 0 for s in songs)

                    # Format songs for Firestore
                    formatted_songs = []
                    for song in songs:
                        formatted_songs.append({
                            'position': song['position'],
                            'name': song['name'],
                            'set_name': song['set_name'],
                            'encore': song['encore'],
                            'is_cover': song['cover'] is not None,
                            'cover_artist': song['cover'],
                            'is_tape': song['tape'],
                            'info': song['info']
                        })

                    # Update setlist
                    setlist_doc.reference.update({
                        'songs': formatted_songs,
                        'song_count': len(songs),
                        'has_encore': has_encore,
                        'setlistfm_id': setlist_result.get('id'),
                        'setlistfm_url': setlist_result.get('url'),
                        'notes': 'Imported from setlist.fm',
                        'fetched_at': firestore.SERVER_TIMESTAMP
                    })

                    # Update concert has_setlist flag
                    concert_ref.update({
                        'has_setlist': True,
                        'updated_at': firestore.SERVER_TIMESTAMP
                    })

                    print(f"✅ [{i}/{len(empty_setlists)}] Concert {concert_id}: {artist_name} - {len(songs)} songs imported")
                    found += 1
                    updated += 1
                else:
                    print(f"⚠️  [{i}/{len(empty_setlists)}] Concert {concert_id}: {artist_name} - Found but no songs")
                    still_not_found += 1
            else:
                print(f"❌ [{i}/{len(empty_setlists)}] Concert {concert_id}: {artist_name} - Not found on setlist.fm")
                still_not_found += 1

        except Exception as e:
            print(f"❌ [{i}/{len(empty_setlists)}] Concert {concert_id}: Error - {str(e)}")
            errors += 1

    # Final summary
    print("\n" + "=" * 80)
    print("✅ FETCH COMPLETE")
    print("=" * 80)
    print(f"\nProcessed: {len(empty_setlists)} concerts")
    print(f"  ✅ Successfully imported: {found}")
    print(f"  ❌ Not found on setlist.fm: {still_not_found}")
    print(f"  ⚠️  Errors: {errors}")
    print(f"  📊 Updated {updated} setlists in Firestore")

    if found > 0:
        print(f"\n🎉 Imported {found} new setlists!")
        print("\nNext steps:")
        print("  1. Run: python3 scripts/export_to_web.py")
        print("  2. Deploy: firebase deploy --only hosting")
    else:
        print("\n😕 No new setlists found. All 379 concerts appear to be unavailable on setlist.fm.")

    return found, still_not_found, errors

if __name__ == '__main__':
    # Check if test mode (limit to 10 concerts)
    test_mode = '--test' in sys.argv
    limit = 10 if test_mode else None

    if test_mode:
        print("\n⚠️  TEST MODE: Processing only 10 concerts")
        print("   Remove --test flag to process all concerts\n")

    fetch_missing_setlists(limit=limit)
