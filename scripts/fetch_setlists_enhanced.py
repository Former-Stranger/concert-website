#!/usr/bin/env python3
"""
Enhanced setlist fetcher that handles co-headliners automatically

For concerts with multiple headliners, this script:
1. Identifies all artists with role='headliner'
2. Fetches a separate setlist for each headliner
3. Creates individual setlist documents (e.g., "847-rod-stewart", "847-cyndi-lauper")

For regular concerts (single headliner):
1. Fetches the setlist
2. Creates a single setlist document using concert_id as document ID
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys
import os
from datetime import datetime
import time
from setlistfm_client import SetlistFMClient

# Setlist.fm API key
SETLISTFM_API_KEY = "DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE"

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
    return text.lower().replace(' ', '-').replace('&', 'and')

def parse_setlist_data(setlist_json, concert_id, artist_id, artist_name):
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
                    song_entry['guest_artist'] = str(with_artist)

            # Add tape indicator if present
            tape = song.get('tape')
            if tape:
                song_entry['is_tape'] = True

            # Add notes if present
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
        'concert_id': concert_id,
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

def detect_missing_openers(concert_id, concert_data, client):
    """
    Detect potential missing openers for a concert using setlist.fm API

    Args:
        concert_id: Concert ID
        concert_data: Concert document data
        client: SetlistFMClient instance

    Returns:
        List of detected openers with confidence scores, or empty list
    """
    artists = concert_data.get('artists', [])

    # Only check if concert has exactly 1 headliner
    headliners = [a for a in artists if a.get('role') == 'headliner']
    if len(headliners) != 1:
        return []

    headliner = headliners[0]
    headliner_name = headliner.get('artist_name', '')
    date_str = concert_data.get('date', '')

    if not headliner_name or not date_str:
        return []

    try:
        # Convert date format
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        api_date_str = date_obj.strftime('%d-%m-%Y')

        # STEP 1: Find headliner's setlist to get exact venue
        result = client.search_setlists(
            artist_name=headliner_name,
            date=api_date_str
        )

        if not result or not result.get('setlist'):
            return []

        headliner_setlist = result['setlist'][0]
        venue = headliner_setlist.get('venue', {})
        exact_venue_name = venue.get('name', '')

        if not exact_venue_name:
            return []

        # Count headliner songs
        headliner_songs = sum(
            len(s.get('song', []))
            for s in headliner_setlist.get('sets', {}).get('set', [])
        )

        # STEP 2: Search for all performers at venue + date
        result2 = client.search_setlists(
            venue_name=exact_venue_name,
            date=api_date_str
        )

        if not result2 or not result2.get('setlist'):
            return []

        all_setlists = result2['setlist']

        # Need at least 2 setlists (headliner + opener)
        if len(all_setlists) <= 1:
            return []

        # STEP 3: Identify potential openers
        performers = []
        for setlist in all_setlists:
            artist = setlist.get('artist', {})
            artist_name = artist.get('name', '')
            artist_mbid = artist.get('mbid', '')

            song_count = sum(
                len(s.get('song', []))
                for s in setlist.get('sets', {}).get('set', [])
            )

            tour = setlist.get('tour', {})
            tour_name = tour.get('name') if tour else None

            performers.append({
                'artist_name': artist_name,
                'artist_mbid': artist_mbid,
                'song_count': song_count,
                'tour_name': tour_name,
                'setlistfm_id': setlist.get('id'),
                'setlistfm_url': setlist.get('url')
            })

        # Sort by song count (descending)
        performers.sort(key=lambda x: x['song_count'], reverse=True)

        likely_headliner = performers[0]
        potential_openers = performers[1:]

        # STEP 4: Get guest artists from headliner's setlist
        guest_artists = set()
        headliner_sets = headliner_setlist.get('sets', {}).get('set', [])

        for set_data in headliner_sets:
            for song in set_data.get('song', []):
                guest = song.get('with', {})
                if guest and isinstance(guest, dict):
                    guest_name = guest.get('name')
                    if guest_name:
                        guest_artists.add(guest_name.lower())

        # Calculate confidence for each opener
        detected_openers = []
        for opener in potential_openers:
            # Must have fewer songs than headliner
            if opener['song_count'] >= likely_headliner['song_count']:
                continue

            confidence = 30  # Base: has fewer songs

            # High confidence: appears as guest
            opener_name_lower = opener['artist_name'].lower()
            for guest in guest_artists:
                if opener_name_lower in guest or guest in opener_name_lower:
                    confidence += 50
                    break

            # Medium confidence: significantly fewer songs
            song_ratio = opener['song_count'] / likely_headliner['song_count']
            if song_ratio < 0.5:
                confidence += 15

            # Low confidence: no tour name
            if not opener['tour_name']:
                confidence += 5

            if confidence >= 50:  # Only return medium/high confidence
                opener['confidence'] = min(confidence, 100)
                detected_openers.append(opener)

        return detected_openers

    except Exception as e:
        # Silently fail - this is an optional enhancement
        return []


def fetch_setlists_for_concert(concert_id, concert_data, client, db, dry_run=False, detect_openers=False):
    """
    Fetch setlists for a concert (handles both single and co-headliners)

    Args:
        concert_id: Concert ID
        concert_data: Concert document data
        client: SetlistFMClient instance
        db: Firestore database reference
        dry_run: If True, don't write to Firestore
        detect_openers: If True, check for missing openers

    Returns:
        dict with keys:
            'status': 'success', 'not_found', 'error'
            'setlists_created': number of setlists created
            'message': description
            'detected_openers': list of detected openers (if detect_openers=True)
    """

    # Get all performing artists (headliners and openers)
    artists = concert_data.get('artists', [])
    performing_artists = [a for a in artists if a.get('role') in ['headliner', 'opener', 'festival_performer']]

    if not performing_artists:
        return {
            'status': 'error',
            'setlists_created': 0,
            'message': 'No performing artists found'
        }

    # Get concert details
    venue_name = concert_data.get('venue_name', '')
    city = concert_data.get('city', '')
    state = concert_data.get('state', '')
    date_str = concert_data.get('date', '')

    if not date_str:
        return {
            'status': 'error',
            'setlists_created': 0,
            'message': 'No date'
        }

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return {
            'status': 'error',
            'setlists_created': 0,
            'message': 'Invalid date format'
        }

    # Fetch setlist for each performing artist
    setlists_found = []

    for performer in performing_artists:
        artist_name = performer.get('artist_name', '')
        artist_id = performer.get('artist_id', '')

        if not artist_name:
            continue

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
                # Parse the setlist
                setlist_data = parse_setlist_data(
                    setlist_result,
                    concert_id,
                    artist_id,
                    artist_name
                )

                if setlist_data and setlist_data.get('song_count', 0) > 0:
                    setlists_found.append({
                        'artist_name': artist_name,
                        'artist_id': artist_id,
                        'data': setlist_data
                    })

        except Exception as e:
            print(f"      Error searching for {artist_name}: {e}")

    # If no setlists found
    if not setlists_found:
        return {
            'status': 'not_found',
            'setlists_created': 0,
            'message': f'No setlists found for {len(performing_artists)} artist(s)'
        }

    # Create setlist documents
    if not dry_run:
        if len(setlists_found) == 1:
            # Single headliner - use concert_id as document ID
            doc_id = concert_id
            setlist_data = setlists_found[0]['data']

            db.collection('setlists').document(doc_id).set(setlist_data)
        else:
            # Multiple headliners - use concert_id-artist_slug format
            for setlist_info in setlists_found:
                artist_slug = slugify(setlist_info['artist_name'])
                doc_id = f"{concert_id}-{artist_slug}"
                setlist_data = setlist_info['data']

                db.collection('setlists').document(doc_id).set(setlist_data)

    # Build result message
    if len(setlists_found) == 1:
        message = f"Found: {setlists_found[0]['artist_name']} ({setlists_found[0]['data']['song_count']} songs)"
    else:
        song_counts = [f"{s['artist_name']} ({s['data']['song_count']})" for s in setlists_found]
        message = f"Found {len(setlists_found)} setlists: {', '.join(song_counts)}"

    result = {
        'status': 'success',
        'setlists_created': len(setlists_found),
        'message': message
    }

    # Check for missing openers if requested
    if detect_openers and len(performing_artists) == 1:
        detected = detect_missing_openers(concert_id, concert_data, client)
        if detected:
            result['detected_openers'] = detected

    return result

def fetch_all_setlists(limit=None, dry_run=False, skip_existing=True, detect_openers=False):
    """
    Fetch setlists for all concerts

    Args:
        limit: Max number of concerts to process (for testing)
        dry_run: If True, don't write to Firestore
        skip_existing: If True, skip concerts that already have setlists
        detect_openers: If True, automatically detect and report missing openers
    """

    print("="*80)
    print("ENHANCED SETLIST FETCHER - WITH CO-HEADLINER SUPPORT")
    print("="*80)

    if dry_run:
        print("⚠️  DRY RUN MODE - No changes will be written to Firestore")

    db = init_firebase()
    client = SetlistFMClient(SETLISTFM_API_KEY)

    # Get all concerts
    print("\n📊 Loading concerts...")
    concerts_ref = db.collection('concerts').order_by('date', direction=firestore.Query.DESCENDING)

    if limit:
        concerts_docs = list(concerts_ref.limit(limit).stream())
    else:
        concerts_docs = list(concerts_ref.stream())

    print(f"   Found {len(concerts_docs)} concerts")

    # Filter to concerts that need setlists
    concerts_to_process = []

    for concert_doc in concerts_docs:
        concert_id = concert_doc.id
        concert_data = concert_doc.to_dict()

        # Skip if no date
        if not concert_data.get('date'):
            continue

        # Skip future concerts
        try:
            date = datetime.strptime(concert_data.get('date'), '%Y-%m-%d')
            if date > datetime.now():
                continue
        except ValueError:
            continue

        # Check if setlist already exists
        if skip_existing:
            # Check for both single and multi-format
            single_exists = db.collection('setlists').document(concert_id).get().exists

            # Check for multi-format (any documents with concert_id field matching)
            multi_exists = len(list(db.collection('setlists').where('concert_id', '==', concert_id).limit(1).stream())) > 0

            if single_exists or multi_exists:
                continue

        concerts_to_process.append((concert_id, concert_data))

    print(f"   {len(concerts_to_process)} concerts need setlists")

    if not concerts_to_process:
        print("\n✅ All concerts already have setlists!")
        return

    # Estimate time
    estimated_minutes = len(concerts_to_process) * 0.6 / 60
    print(f"   Estimated time: {estimated_minutes:.1f} minutes")

    # Ask for confirmation if processing many concerts (skip if using --limit)
    if not dry_run and len(concerts_to_process) > 10 and not limit:
        response = input(f"\n⚠️  About to fetch {len(concerts_to_process)} setlists. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return

    # Statistics
    stats = {
        'success': 0,
        'not_found': 0,
        'errors': 0,
        'co_headliners': 0,
        'total_setlists': 0
    }

    print(f"\n🔍 Starting setlist fetch...\n")

    for i, (concert_id, concert_data) in enumerate(concerts_to_process, 1):
        # Get headliners
        headliners = [a for a in concert_data.get('artists', []) if a.get('role') == 'headliner']
        headliner_names = ', '.join([a.get('artist_name', '') for a in headliners])

        is_co_headliner = len(headliners) > 1
        prefix = "🎭" if is_co_headliner else "🎤"

        print(f"{prefix} [{i}/{len(concerts_to_process)}] Concert {concert_id}: {headliner_names}")
        print(f"      {concert_data.get('date')} at {concert_data.get('venue_name', 'Unknown')}")

        # Fetch setlists
        result = fetch_setlists_for_concert(concert_id, concert_data, client, db, dry_run, detect_openers)

        # Update stats
        if result['status'] == 'success':
            stats['success'] += 1
            stats['total_setlists'] += result['setlists_created']
            if is_co_headliner:
                stats['co_headliners'] += 1
            print(f"      ✅ {result['message']}")

            # Report detected openers
            if 'detected_openers' in result:
                for opener in result['detected_openers']:
                    conf = opener['confidence']
                    print(f"      🔍 Detected opener: {opener['artist_name']} ({conf}% confidence, {opener['song_count']} songs)")
        elif result['status'] == 'not_found':
            stats['not_found'] += 1
            print(f"      ❌ {result['message']}")
        else:
            stats['errors'] += 1
            print(f"      ⚠️  {result['message']}")

        # Progress update every 10 concerts
        if i % 10 == 0:
            print(f"\n📈 Progress: {i}/{len(concerts_to_process)} ({i*100//len(concerts_to_process)}%)")
            print(f"   Success: {stats['success']} | Not found: {stats['not_found']} | Errors: {stats['errors']}")
            print(f"   Co-headliners: {stats['co_headliners']} | Total setlists created: {stats['total_setlists']}\n")

    # Final summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total concerts processed: {len(concerts_to_process)}")
    print(f"✅ Success: {stats['success']}")
    print(f"❌ Not found: {stats['not_found']}")
    print(f"⚠️  Errors: {stats['errors']}")
    print(f"🎭 Co-headliner shows: {stats['co_headliners']}")
    print(f"📝 Total setlists created: {stats['total_setlists']}")

    if dry_run:
        print("\n⚠️  This was a DRY RUN - no changes were made to Firestore")
        print("   Run without --dry-run to actually create the setlists")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Fetch setlists from setlist.fm (with co-headliner support)')
    parser.add_argument('--limit', type=int, help='Limit number of concerts to process (for testing)')
    parser.add_argument('--dry-run', action='store_true', help='Test mode - don\'t write to Firestore')
    parser.add_argument('--all', action='store_true', help='Process all concerts, including those with existing setlists')
    parser.add_argument('--detect-openers', action='store_true', help='Automatically detect and report missing openers')

    args = parser.parse_args()

    fetch_all_setlists(
        limit=args.limit,
        dry_run=args.dry_run,
        skip_existing=not args.all,
        detect_openers=args.detect_openers
    )
