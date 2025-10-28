#!/usr/bin/env python3
"""
Create co-headliner setlists for Concert 847 (Rod Stewart / Cyndi Lauper)
Non-interactive version - automatically creates the setlists

This script:
1. Fetches both setlists from setlist.fm API
2. Creates two separate setlist documents with artist_id field
3. Uses document IDs: "847-rod-stewart" and "847-cyndi-lauper"
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys
import os
from setlistfm_client import SetlistFMClient

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

def parse_setlist_data(setlist_json, artist_id, artist_name):
    """Parse setlist.fm JSON into our format"""
    if not setlist_json:
        return None

    songs = []
    position = 1
    has_encore = False

    # Parse sets
    sets = setlist_json.get('sets', {}).get('set', [])
    for set_idx, set_data in enumerate(sets):
        set_name = set_data.get('name', '')
        if 'encore' in set_name.lower():
            has_encore = True
            set_display_name = f"Encore {set_name.replace('Encore', '').strip()}" if set_name.replace('Encore', '').strip() else "Encore"
        else:
            set_display_name = f"Set {set_idx + 1}" if not set_name else set_name

        # Parse songs in this set
        song_list = set_data.get('song', [])
        for song in song_list:
            song_name = song.get('name', '')
            if not song_name:
                continue

            song_entry = {
                'position': position,
                'name': song_name,
                'set_name': set_display_name
            }

            # Add cover info if present
            cover = song.get('cover')
            if cover:
                song_entry['is_cover'] = True
                song_entry['cover_artist'] = cover.get('name', '')
            else:
                song_entry['is_cover'] = False
                song_entry['cover_artist'] = None

            # Add guest artist if present
            with_artist = song.get('with')
            if with_artist:
                if isinstance(with_artist, dict):
                    song_entry['guest_artist'] = with_artist.get('name', '')
                else:
                    # Sometimes 'with' is just a string
                    song_entry['guest_artist'] = str(with_artist)

            # Add tape/info if present
            tape = song.get('tape')
            if tape:
                song_entry['is_tape'] = True

            info = song.get('info')
            if info:
                song_entry['notes'] = info

            songs.append(song_entry)
            position += 1

    # Get tour name if present
    tour_name = None
    tour = setlist_json.get('tour')
    if tour and isinstance(tour, dict):
        tour_name = tour.get('name')

    setlist_data = {
        'concert_id': '847',
        'artist_id': artist_id,
        'artist_name': artist_name,
        'setlistfm_id': setlist_json.get('id', ''),
        'setlistfm_url': setlist_json.get('url', ''),
        'song_count': len(songs),
        'has_encore': has_encore,
        'songs': songs
    }

    # Add tour name if present
    if tour_name:
        setlist_data['tour_name'] = tour_name

    return setlist_data

def create_coheadliner_setlists(api_key):
    """Create setlist documents for Concert 847 co-headliners"""

    print("\n" + "="*80)
    print("CREATING CO-HEADLINER SETLISTS FOR CONCERT 847")
    print("="*80)

    init_firebase()
    db = firestore.client()

    # Initialize setlist.fm client
    client = SetlistFMClient(api_key)

    # Define the two setlists
    setlists = [
        {
            'doc_id': '847-rod-stewart',
            'artist_id': '481',
            'artist_name': 'Rod Stewart',
            'setlistfm_id': '63eb562f'
        },
        {
            'doc_id': '847-cyndi-lauper',
            'artist_id': 'Ts7IBnCtQNORftKRdruR',
            'artist_name': 'Cyndi Lauper',
            'setlistfm_id': '6beb562e'
        }
    ]

    print("\nFetching setlists from setlist.fm API...")

    for setlist_info in setlists:
        print(f"\n{'-'*80}")
        print(f"Processing: {setlist_info['artist_name']}")
        print(f"  Setlist.fm ID: {setlist_info['setlistfm_id']}")
        print(f"  Document ID: {setlist_info['doc_id']}")

        # Fetch from API
        setlist_json = client.get_setlist(setlist_info['setlistfm_id'])
        if not setlist_json:
            print(f"  ❌ Failed to fetch setlist")
            continue

        # Parse into our format
        setlist_data = parse_setlist_data(
            setlist_json,
            setlist_info['artist_id'],
            setlist_info['artist_name']
        )

        if not setlist_data:
            print(f"  ❌ Failed to parse setlist")
            continue

        print(f"  ✓ Fetched {setlist_data['song_count']} songs")
        print(f"  ✓ Has encore: {setlist_data['has_encore']}")

        # Show first few songs
        print(f"\n  First 3 songs:")
        for song in setlist_data['songs'][:3]:
            print(f"    {song['position']}. {song['name']} ({song['set_name']})")

        # Create the document
        doc_ref = db.collection('setlists').document(setlist_info['doc_id'])
        doc_ref.set(setlist_data)
        print(f"\n  ✓ Created setlist document: {setlist_info['doc_id']}")

    # Check if old setlist document exists and should be deleted
    print(f"\n{'-'*80}")
    print("Checking for old setlist document...")
    old_doc = db.collection('setlists').document('847').get()
    if old_doc.exists:
        print("  Found old setlist document '847'")
        db.collection('setlists').document('847').delete()
        print("  ✓ Deleted old document")
    else:
        print("  No old document found")

    print("\n" + "="*80)
    print("SUCCESS!")
    print("="*80)
    print(f"Created 2 setlist documents for Concert 847")
    print(f"  - 847-rod-stewart")
    print(f"  - 847-cyndi-lauper")

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("1. Run: python3 scripts/export_to_web.py")
    print("2. Test locally: open website/concert.html?id=847")
    print("3. Deploy: firebase deploy --only hosting")
    print("4. Verify: https://earplugsandmemories.com/concert.html?id=847")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 create_coheadliner_setlists_847_auto.py YOUR_API_KEY")
        print("\nExample:")
        print("  python3 create_coheadliner_setlists_847_auto.py your-setlistfm-api-key")
        sys.exit(1)

    api_key = sys.argv[1]
    create_coheadliner_setlists(api_key)
