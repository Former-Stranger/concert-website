#!/usr/bin/env python3
"""
Fetch missing setlists from setlist.fm with automatic API key rotation.

This script will:
1. Find concerts without setlists (has_setlist=false)
2. Attempt to fetch setlists using setlist.fm API
3. Automatically rotate between 3 API keys when rate limits are hit
4. Stop when all 3 keys are exhausted (15 consecutive failures per key)
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys
from datetime import datetime
from setlistfm_client import SetlistFMClient

# Three setlist.fm API keys
API_KEYS = [
    "DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE",  # Key 1
    "Uo48MPdBZN5ujA_PJKkyeKYyiMzOaf-kd4gi",  # Key 2
    "_Q380wqoYXFLsXALU_vlNSUTjwy7j7KQ6Bx9",  # Key 3
]

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

def is_rate_limit_error(error_msg):
    """Check if an error is a rate limit error"""
    if error_msg is None:
        return False
    error_str = str(error_msg).lower()
    return '429' in error_str or 'rate limit' in error_str or 'too many requests' in error_str

def fetch_missing_setlists(limit=None):
    """
    Fetch setlists for concerts without them, with automatic API key rotation

    Args:
        limit: Optional limit on number of concerts to process (for testing)
    """
    print("\n" + "=" * 80)
    print("FETCHING MISSING SETLISTS FROM SETLIST.FM")
    print("With Automatic API Key Rotation")
    print("=" * 80)

    db = init_firebase()

    # Track API key usage
    current_key_index = 0
    consecutive_rate_limits = [0, 0, 0]  # Track consecutive failures for each key
    total_requests_per_key = [0, 0, 0]
    successful_fetches_per_key = [0, 0, 0]

    client = SetlistFMClient(API_KEYS[current_key_index])

    print(f"\n🔑 Starting with API Key #{current_key_index + 1}")

    # Get all concerts without setlists
    print("\n📊 Finding concerts without setlists...")
    concerts_without_setlists = list(
        db.collection('concerts')
        .where('has_setlist', '==', False)
        .stream()
    )

    total = len(concerts_without_setlists)
    if limit:
        concerts_without_setlists = concerts_without_setlists[:limit]

    print(f"   Found {total} concerts without setlists")
    if limit:
        print(f"   Processing first {limit} concerts (test mode)")

    # Statistics
    found = 0
    not_found = 0
    errors = 0
    updated = 0
    skipped = 0

    print(f"\n🔍 Starting setlist fetch...")
    print(f"   Rate limit: 4 seconds between requests")
    print(f"   Will rotate keys after 15 consecutive rate limit errors")
    print(f"   Estimated time: {len(concerts_without_setlists) * 4 / 60:.1f} minutes per key\n")

    for i, concert_doc in enumerate(concerts_without_setlists, 1):
        concert_data = concert_doc.to_dict()
        concert_id = concert_doc.id

        # Extract concert info
        artists = concert_data.get('artists', [])
        if not artists:
            print(f"⏭️  [{i}/{len(concerts_without_setlists)}] Concert {concert_id}: No artists listed")
            skipped += 1
            continue

        # Get the headliner (or first artist if no headliner)
        headliner = None
        for artist in artists:
            if artist.get('role') == 'headliner':
                headliner = artist
                break

        if not headliner and artists:
            headliner = artists[0]  # Fallback to first artist

        artist_name = headliner.get('artist_name', '') if headliner else ''
        venue_name = concert_data.get('venue_name', '')
        city = concert_data.get('city', '')
        state = concert_data.get('state', '')
        date_str = concert_data.get('date', '')

        if not date_str:
            print(f"⏭️  [{i}/{len(concerts_without_setlists)}] Concert {concert_id}: No date")
            skipped += 1
            continue

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            print(f"⏭️  [{i}/{len(concerts_without_setlists)}] Concert {concert_id}: Invalid date format")
            skipped += 1
            continue

        # Show progress every 10 concerts
        if i % 10 == 0:
            print(f"\n📈 Progress: {i}/{len(concerts_without_setlists)} ({i*100//len(concerts_without_setlists)}%)")
            print(f"   Current Key: #{current_key_index + 1}")
            print(f"   Found: {found} | Not found: {not_found} | Errors: {errors} | Skipped: {skipped}")
            print(f"   Key Stats: {successful_fetches_per_key[current_key_index]} successful / {total_requests_per_key[current_key_index]} total")

        # Search for setlist
        total_requests_per_key[current_key_index] += 1
        error_msg = None

        try:
            setlist_result = client.find_setlist_for_concert(
                artist_name=artist_name,
                date=date,
                venue_name=venue_name,
                city=city,
                state=state
            )

            # Success - reset rate limit counter for this key
            consecutive_rate_limits[current_key_index] = 0

            if setlist_result:
                # Extract songs
                songs = client.extract_songs_from_setlist(setlist_result)

                if songs:
                    # Create or get setlist document
                    setlist_ref = db.collection('setlists').document(concert_id)

                    # Format songs for Firestore
                    formatted_songs = []
                    has_encore = False

                    for song in songs:
                        formatted_songs.append({
                            'position': song['position'],
                            'name': song['name'],
                            'set_name': song['set_name'],
                            'encore': song['encore'],
                            'is_cover': song['cover'] is not None,
                            'cover_artist': song['cover'],
                            'is_tape': song.get('tape', False),
                            'info': song.get('info')
                        })
                        if song['encore'] > 0:
                            has_encore = True

                    # Create/update setlist document
                    setlist_ref.set({
                        'concert_id': concert_id,
                        'songs': formatted_songs,
                        'song_count': len(songs),
                        'has_encore': has_encore,
                        'setlistfm_id': setlist_result.get('id'),
                        'setlistfm_url': setlist_result.get('url'),
                        'notes': 'Imported from setlist.fm',
                        'fetched_at': firestore.SERVER_TIMESTAMP,
                        'created_at': firestore.SERVER_TIMESTAMP
                    })

                    # Update concert has_setlist flag
                    concert_doc.reference.update({
                        'has_setlist': True,
                        'updated_at': firestore.SERVER_TIMESTAMP
                    })

                    print(f"✅ [{i}/{len(concerts_without_setlists)}] Concert {concert_id}: {artist_name} - {len(songs)} songs imported (Key #{current_key_index + 1})")
                    found += 1
                    updated += 1
                    successful_fetches_per_key[current_key_index] += 1
                else:
                    print(f"⚠️  [{i}/{len(concerts_without_setlists)}] Concert {concert_id}: {artist_name} - Found but no songs")
                    not_found += 1
            else:
                # Not found is not an error - just log it
                # print(f"❌ [{i}/{len(concerts_without_setlists)}] Concert {concert_id}: {artist_name} - Not found on setlist.fm")
                not_found += 1

        except Exception as e:
            error_msg = str(e)

            # Check if this is a rate limit error
            if is_rate_limit_error(error_msg):
                consecutive_rate_limits[current_key_index] += 1

                print(f"⚠️  [{i}/{len(concerts_without_setlists)}] Concert {concert_id}: Rate limit hit (Key #{current_key_index + 1}, {consecutive_rate_limits[current_key_index]}/15)")

                # Check if we need to rotate keys
                if consecutive_rate_limits[current_key_index] >= 15:
                    print(f"\n🔄 Key #{current_key_index + 1} exhausted after {consecutive_rate_limits[current_key_index]} consecutive rate limits")
                    print(f"   Total requests on this key: {total_requests_per_key[current_key_index]}")
                    print(f"   Successful fetches: {successful_fetches_per_key[current_key_index]}")

                    # Try to find another key that's not exhausted
                    next_key_index = None
                    for j in range(len(API_KEYS)):
                        test_index = (current_key_index + j + 1) % len(API_KEYS)
                        if consecutive_rate_limits[test_index] < 15:
                            next_key_index = test_index
                            break

                    if next_key_index is not None:
                        current_key_index = next_key_index
                        client = SetlistFMClient(API_KEYS[current_key_index])
                        print(f"   Switching to Key #{current_key_index + 1}\n")
                    else:
                        print("\n❌ ALL API KEYS EXHAUSTED!")
                        print("   All 3 keys have hit rate limits (15 consecutive failures each)")
                        print("   Stopping fetch process.\n")
                        break

                errors += 1
            else:
                # Other error
                print(f"❌ [{i}/{len(concerts_without_setlists)}] Concert {concert_id}: Error - {error_msg}")
                errors += 1

    # Final summary
    print("\n" + "=" * 80)
    print("✅ FETCH COMPLETE")
    print("=" * 80)
    print(f"\nProcessed: {i} concerts")
    print(f"  ✅ Successfully imported: {found}")
    print(f"  ❌ Not found on setlist.fm: {not_found}")
    print(f"  ⚠️  Errors: {errors}")
    print(f"  ⏭️  Skipped: {skipped}")
    print(f"  📊 Updated {updated} setlists in Firestore")

    print(f"\n🔑 API Key Usage:")
    for idx, key in enumerate(API_KEYS):
        status = "EXHAUSTED" if consecutive_rate_limits[idx] >= 15 else "OK"
        print(f"   Key #{idx + 1}: {total_requests_per_key[idx]} requests, {successful_fetches_per_key[idx]} successful ({status})")

    if found > 0:
        print(f"\n🎉 Imported {found} new setlists!")
        print("\nNext steps:")
        print("  1. Run: python3 scripts/export_to_web.py")
        print("  2. Deploy: firebase deploy --only hosting")
    else:
        print("\n😕 No new setlists found.")

    return found, not_found, errors

if __name__ == '__main__':
    # Check if test mode (limit to 10 concerts)
    test_mode = '--test' in sys.argv
    limit = 10 if test_mode else None

    if test_mode:
        print("\n⚠️  TEST MODE: Processing only 10 concerts")
        print("   Remove --test flag to process all concerts\n")

    fetch_missing_setlists(limit=limit)
