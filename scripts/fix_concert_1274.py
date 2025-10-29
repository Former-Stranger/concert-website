#!/usr/bin/env python3
"""
Fix concert 1274 (Mumford & Sons with Lucius)

ISSUE:
- Concert incorrectly labeled as "Multi-Artist Show"
- Artist role set to "festival_performer" instead of "headliner"
- Lucius (opening act) missing from artists array
- Lucius setlist not fetched because artist wasn't in database

ROOT CAUSE:
The parse_festivals.py script has logic that detects " & " in artist names and
assumes it's a multi-artist show if not a protected band. "Mumford & Sons" is NOT
in the protected bands list, so it was parsed as multi-artist.

FIX:
1. Change artist role from "festival_performer" to "headliner"
2. Remove festival_name (set to None)
3. Add Lucius as an opener to the artists array
4. Fetch Lucius setlist from setlist.fm
5. Re-export data and deploy

Lucius setlist URL: https://www.setlist.fm/setlist/lucius/2025/forest-hills-stadium-queens-ny-3b423814.html
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys
import os
from datetime import datetime
from setlistfm_client import SetlistFMClient

# Setlist.fm API key
SETLISTFM_API_KEY = "Uo48MPdBZN5ujA_PJKkyeKYyiMzOaf-kd4gi"

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

def slugify(text):
    """Convert text to URL-friendly slug"""
    return text.lower().replace(' ', '-').replace('&', 'and').replace("'", '')

def main():
    print("=" * 80)
    print("FIX CONCERT 1274 - MUMFORD & SONS WITH LUCIUS")
    print("=" * 80)

    db = init_firebase()
    concert_ref = db.collection('concerts').document('1274')
    concert = concert_ref.get()

    if not concert.exists:
        print("❌ Concert 1274 not found!")
        return

    concert_data = concert.to_dict()

    print("\n📋 CURRENT STATE:")
    print(f"  Festival Name: {concert_data.get('festival_name')}")
    print(f"  Artists:")
    for artist in concert_data.get('artists', []):
        print(f"    - {artist.get('artist_name')} (role: {artist.get('role')})")

    # Step 1: Check if Lucius artist exists
    print("\n🔍 Looking for Lucius in artists collection...")
    artists_ref = db.collection('artists')
    lucius_query = artists_ref.where('canonical_name', '==', 'Lucius').limit(1).get()

    if lucius_query:
        lucius_doc = lucius_query[0]
        lucius_id = lucius_doc.id
        print(f"  ✓ Found Lucius (ID: {lucius_id})")
    else:
        print("  ✗ Lucius not found, creating new artist...")
        lucius_ref = artists_ref.document()
        lucius_ref.set({
            'canonical_name': 'Lucius',
            'created_at': firestore.SERVER_TIMESTAMP
        })
        lucius_id = lucius_ref.id
        print(f"  ✓ Created Lucius (ID: {lucius_id})")

    # Step 2: Update concert document
    print("\n🔧 UPDATING CONCERT 1274:")

    # Update artists array
    updated_artists = [
        {
            'artist_id': concert_data['artists'][0]['artist_id'],
            'artist_name': 'Mumford & Sons',
            'role': 'headliner',  # Change from festival_performer
            'position': 1
        },
        {
            'artist_id': lucius_id,
            'artist_name': 'Lucius',
            'role': 'opener',
            'position': 2
        }
    ]

    concert_ref.update({
        'festival_name': None,  # Remove "Multi-Artist Show"
        'artists': updated_artists,
        'updated_at': firestore.SERVER_TIMESTAMP
    })

    print("  ✓ Changed Mumford & Sons role: festival_performer → headliner")
    print("  ✓ Removed festival_name: 'Multi-Artist Show' → None")
    print("  ✓ Added Lucius as opener")

    # Step 3: Fetch Lucius setlist
    print("\n🎵 FETCHING LUCIUS SETLIST:")

    client = SetlistFMClient(SETLISTFM_API_KEY)
    concert_date = datetime.strptime(concert_data['date'], '%Y-%m-%d')

    print(f"  Searching for: Lucius on {concert_date.strftime('%B %d, %Y')}")
    print(f"  Venue: {concert_data.get('venue_name')}")

    setlist_json = client.find_setlist_for_concert(
        artist_name='Lucius',
        date=concert_date,
        venue_name=concert_data.get('venue_name'),
        city=concert_data.get('city'),
        state=concert_data.get('state')
    )

    if not setlist_json:
        print("  ❌ Setlist not found on setlist.fm")
        print("\n⚠️  You may need to manually fetch the setlist")
        print("     URL: https://www.setlist.fm/setlist/lucius/2025/forest-hills-stadium-queens-ny-3b423814.html")
        return

    print(f"  ✓ Found setlist!")
    print(f"    URL: {setlist_json.get('url', 'N/A')}")

    # Parse setlist
    songs = []
    position = 1
    has_encore = False

    sets = setlist_json.get('sets', {}).get('set', [])
    for set_idx, set_data in enumerate(sets):
        set_name = set_data.get('name', '')
        if 'encore' in set_name.lower():
            has_encore = True
            set_display_name = f"Encore {set_name.replace('Encore', '').strip()}" if set_name.replace('Encore', '').strip() else "Encore"
        else:
            set_display_name = f"Set {set_idx + 1}" if not set_name else set_name

        song_list = set_data.get('song', [])
        for song in song_list:
            song_name = song.get('name', '')
            if not song_name:
                continue

            song_entry = {
                'position': position,
                'name': song_name,
                'set_name': set_display_name,
                'is_cover': 'cover' in song,
                'cover_artist': song.get('cover', {}).get('name') if 'cover' in song else None
            }

            songs.append(song_entry)
            position += 1

    print(f"    Songs: {len(songs)}")

    # Create setlist document
    setlist_doc_id = f"1274-{slugify('Lucius')}"
    setlist_ref = db.collection('setlists').document(setlist_doc_id)

    setlist_data = {
        'concert_id': '1274',
        'artist_id': lucius_id,
        'artist_name': 'Lucius',
        'setlistfm_id': setlist_json.get('id', ''),
        'setlistfm_url': setlist_json.get('url', ''),
        'song_count': len(songs),
        'has_encore': has_encore,
        'songs': songs,
        'created_at': firestore.SERVER_TIMESTAMP
    }

    # Add tour name if present
    tour = setlist_json.get('tour')
    if tour and isinstance(tour, dict):
        tour_name = tour.get('name')
        if tour_name:
            setlist_data['tour_name'] = tour_name

    setlist_ref.set(setlist_data)
    print(f"  ✓ Created setlist document: {setlist_doc_id}")

    # Summary
    print("\n" + "=" * 80)
    print("✅ SUCCESS!")
    print("=" * 80)
    print("\nCHANGES MADE:")
    print("  1. Mumford & Sons: festival_performer → headliner")
    print("  2. Festival name: 'Multi-Artist Show' → None")
    print("  3. Added Lucius as opener")
    print(f"  4. Created Lucius setlist ({len(songs)} songs)")
    print("\nNEXT STEPS:")
    print("  1. Run export script: python3 scripts/export_to_web.py")
    print("  2. Deploy to Firebase: firebase deploy --only hosting")
    print("  3. Verify at: https://earplugsandmemories.com/concert.html?id=1274")
    print("\nEXPECTED RESULT:")
    print("  - Page title: 'Mumford & Sons'")
    print("  - No 'Multi-Artist Show' label")
    print("  - Lucius setlist shown in 'Opening Act(s)' section")
    print("  - Mumford & Sons setlist shown as main headliner")
    print()

if __name__ == '__main__':
    main()
