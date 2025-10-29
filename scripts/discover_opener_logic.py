#!/usr/bin/env python3
"""
Test script to discover opener detection logic using setlist.fm API

Goal: Find if we can detect Lucius as opener for Mumford & Sons on Aug 9, 2025

SMART STRATEGY (venue names change, dates don't):
1. Search by ARTIST + DATE to find headliner's setlist
2. Extract EXACT venue name from that result
3. Search by EXACT VENUE + DATE to find all performers that day
4. Identify opener vs headliner using heuristics
"""

import requests
import json
from datetime import datetime
import time

# Use a fresh API key if the others are rate limited
# You can generate a new one at: https://www.setlist.fm/settings/api
SETLISTFM_API_KEY = "_Q380wqoYXFLsXALU_vlNSUTjwy7j7KQ6Bx9"

def search_by_venue_and_date(venue_name, city_name, date_str):
    """
    Search for ALL setlists at a venue on a specific date

    Args:
        venue_name: e.g., "Forest Hills Stadium"
        city_name: e.g., "Queens" or "New York"
        date_str: Format "dd-MM-yyyy" e.g., "09-08-2025"
    """

    url = 'https://api.setlist.fm/rest/1.0/search/setlists'

    headers = {
        'x-api-key': SETLISTFM_API_KEY,
        'Accept': 'application/json'
    }

    # Try multiple search strategies
    search_strategies = [
        # Strategy 1: Venue name + date
        {
            'venueName': venue_name,
            'date': date_str
        },
        # Strategy 2: City + date
        {
            'cityName': city_name,
            'date': date_str
        },
        # Strategy 3: Venue + city + date
        {
            'venueName': venue_name,
            'cityName': city_name,
            'date': date_str
        },
    ]

    print("="*80)
    print("SEARCHING FOR ALL SETLISTS AT FOREST HILLS STADIUM - AUGUST 9, 2025")
    print("="*80)

    for i, params in enumerate(search_strategies, 1):
        print(f"\n{'='*80}")
        print(f"STRATEGY {i}: {params}")
        print(f"{'='*80}")

        try:
            time.sleep(1)  # Rate limiting
            response = requests.get(url, params=params, headers=headers)

            if response.status_code == 429:
                print("⚠️  Rate limited. Wait a moment and try with a fresh API key.")
                retry_after = response.headers.get('Retry-After', '60')
                print(f"   Retry after: {retry_after} seconds")
                return None

            if not response.ok:
                print(f"❌ Error: {response.status_code}")
                continue

            data = response.json()
            setlists = data.get('setlist', [])

            print(f"✓ Found {len(setlists)} setlist(s)")

            if not setlists:
                continue

            # Display results
            for j, setlist in enumerate(setlists, 1):
                print(f"\n{'─'*80}")
                print(f"SETLIST {j}:")
                print(f"{'─'*80}")

                artist = setlist.get('artist', {})
                venue = setlist.get('venue', {})
                tour = setlist.get('tour', {})

                print(f"Artist: {artist.get('name', 'Unknown')}")
                print(f"Date: {setlist.get('eventDate', 'Unknown')}")
                print(f"Venue: {venue.get('name', 'Unknown')}")
                print(f"City: {venue.get('city', {}).get('name', 'Unknown')}")
                print(f"Tour: {tour.get('name', 'None') if tour else 'None'}")
                print(f"URL: {setlist.get('url', 'N/A')}")

                # Check for time information
                print(f"\nLOOKING FOR TIME/ORDER INFORMATION:")

                # Check all possible fields
                time_fields = [
                    'startTime', 'time', 'eventTime', 'performanceTime',
                    'doorTime', 'showTime', 'order', 'position', 'sequence'
                ]

                found_time_info = False
                for field in time_fields:
                    if field in setlist:
                        print(f"  ✓ {field}: {setlist[field]}")
                        found_time_info = True

                if not found_time_info:
                    print("  ✗ No time/order fields found")

                # Check info field (might contain notes about opener)
                info = setlist.get('info')
                if info:
                    print(f"\nInfo/Notes: {info}")

                # Check for any other interesting fields
                print(f"\nAll top-level fields:")
                for key in sorted(setlist.keys()):
                    if key not in ['artist', 'venue', 'sets', 'url', 'tour']:
                        value = setlist[key]
                        if isinstance(value, (str, int, float, bool)):
                            print(f"  - {key}: {value}")

                # Check venue object for additional info
                print(f"\nVenue object fields:")
                for key in sorted(venue.keys()):
                    print(f"  - {key}: {venue[key]}")

                # Show first few songs to see structure
                sets = setlist.get('sets', {}).get('set', [])
                if sets and sets[0].get('song'):
                    songs = sets[0].get('song', [])
                    print(f"\nFirst 3 songs:")
                    for song in songs[:3]:
                        song_name = song.get('name', 'Unknown')
                        guest = song.get('with', {}).get('name') if song.get('with') else None
                        if guest:
                            print(f"  - {song_name} (with {guest})")
                        else:
                            print(f"  - {song_name}")

                # Print full JSON for first result (for deep inspection)
                if j == 1:
                    print(f"\n{'='*80}")
                    print("FULL JSON (First Result):")
                    print(f"{'='*80}")
                    print(json.dumps(setlist, indent=2))

            # If we found results, we're done
            if setlists:
                print(f"\n{'='*80}")
                print("ANALYSIS:")
                print(f"{'='*80}")

                if len(setlists) == 1:
                    print("❌ Only found 1 setlist (the headliner)")
                    print("   The opener's setlist may not be on setlist.fm")
                    print("   OR the search didn't return both")
                else:
                    print(f"✓ Found {len(setlists)} setlists at same venue/date!")
                    print("  This means we CAN detect multiple artists")

                    artists_found = [s.get('artist', {}).get('name') for s in setlists]
                    print(f"\n  Artists: {', '.join(artists_found)}")

                    print("\n  CHALLENGE: Determining who is opener vs headliner")
                    print("  - No explicit 'isOpener' or 'role' field in API")
                    print("  - No time information found")
                    print("  - May need to use heuristics:")
                    print("    1. Artist with shorter setlist = likely opener")
                    print("    2. Artist with tour name = likely headliner")
                    print("    3. Artist order in search results (maybe)")

                return setlists

        except Exception as e:
            print(f"❌ Exception: {e}")
            continue

    print("\n❌ Could not find setlists with any search strategy")
    return None


def test_specific_artist_searches():
    """
    Also try searching for each artist individually to see what we get
    """
    print("\n\n")
    print("="*80)
    print("TESTING INDIVIDUAL ARTIST SEARCHES")
    print("="*80)

    artists = ["Mumford & Sons", "Lucius"]
    date = "09-08-2025"  # August 9, 2025

    url = 'https://api.setlist.fm/rest/1.0/search/setlists'
    headers = {
        'x-api-key': SETLISTFM_API_KEY,
        'Accept': 'application/json'
    }

    for artist in artists:
        print(f"\n{'='*80}")
        print(f"SEARCHING: {artist} on {date}")
        print(f"{'='*80}")

        params = {
            'artistName': artist,
            'date': date
        }

        try:
            time.sleep(1)
            response = requests.get(url, params=params, headers=headers)

            if response.status_code == 429:
                print("⚠️  Rate limited")
                continue

            if not response.ok:
                print(f"❌ Error: {response.status_code}")
                continue

            data = response.json()
            setlists = data.get('setlist', [])

            if setlists:
                setlist = setlists[0]
                venue = setlist.get('venue', {})
                tour = setlist.get('tour', {})

                songs_count = sum(len(s.get('song', [])) for s in setlist.get('sets', {}).get('set', []))

                print(f"✓ Found setlist!")
                print(f"  Venue: {venue.get('name')}")
                print(f"  Tour: {tour.get('name') if tour else 'None'}")
                print(f"  Songs: {songs_count}")
                print(f"  URL: {setlist.get('url')}")
            else:
                print(f"❌ No setlist found for {artist}")

        except Exception as e:
            print(f"❌ Exception: {e}")


def smart_opener_detection(headliner_name, date_str):
    """
    SMART STRATEGY: Use headliner to get exact venue, then find all performers

    Args:
        headliner_name: e.g., "Mumford & Sons"
        date_str: Format "dd-MM-yyyy" e.g., "09-08-2025"
    """
    print("\n\n")
    print("="*80)
    print("SMART OPENER DETECTION STRATEGY")
    print("="*80)
    print(f"\nHeadliner: {headliner_name}")
    print(f"Date: {date_str}")
    print("\nWhy this works:")
    print("  ✓ Venue names change (sponsorships), dates don't")
    print("  ✓ Artist name + date = reliable search")
    print("  ✓ API gives us EXACT venue name")
    print("  ✓ Then search exact venue + date for all performers")

    url = 'https://api.setlist.fm/rest/1.0/search/setlists'
    headers = {
        'x-api-key': SETLISTFM_API_KEY,
        'Accept': 'application/json'
    }

    # STEP 1: Find headliner's setlist to get exact venue
    print(f"\n{'='*80}")
    print(f"STEP 1: Find {headliner_name}'s setlist")
    print(f"{'='*80}")

    params = {
        'artistName': headliner_name,
        'date': date_str
    }

    try:
        time.sleep(2)
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 429:
            print("⚠️  Rate limited. Need fresh API key.")
            return None

        if not response.ok:
            print(f"❌ Error: {response.status_code}")
            return None

        data = response.json()
        setlists = data.get('setlist', [])

        if not setlists:
            print(f"❌ No setlist found for {headliner_name} on {date_str}")
            return None

        headliner_setlist = setlists[0]
        venue = headliner_setlist.get('venue', {})
        exact_venue_name = venue.get('name', '')
        city_obj = venue.get('city', {})
        city_name = city_obj.get('name', '') if isinstance(city_obj, dict) else ''

        print(f"✓ Found headliner's setlist!")
        print(f"  Exact venue from API: '{exact_venue_name}'")
        print(f"  City: {city_name}")
        print(f"  URL: {headliner_setlist.get('url')}")

        # Count songs
        headliner_songs = sum(len(s.get('song', [])) for s in headliner_setlist.get('sets', {}).get('set', []))
        print(f"  Songs: {headliner_songs}")

        # STEP 2: Search for ALL setlists at exact venue + date
        print(f"\n{'='*80}")
        print(f"STEP 2: Search for ALL performers at this venue on this date")
        print(f"{'='*80}")
        print(f"Using EXACT venue name: '{exact_venue_name}'")

        params2 = {
            'venueName': exact_venue_name,
            'date': date_str
        }

        time.sleep(2)
        response2 = requests.get(url, params=params2, headers=headers)

        if response2.status_code == 429:
            print("⚠️  Rate limited")
            return None

        if not response2.ok:
            print(f"❌ Error: {response2.status_code}")
            return None

        data2 = response2.json()
        all_setlists = data2.get('setlist', [])

        print(f"\n✓ Found {len(all_setlists)} setlist(s) at this venue on this date:")

        performers = []
        for i, setlist in enumerate(all_setlists, 1):
            artist = setlist.get('artist', {})
            artist_name = artist.get('name', 'Unknown')
            tour = setlist.get('tour', {})
            tour_name = tour.get('name') if tour else None

            song_count = sum(len(s.get('song', [])) for s in setlist.get('sets', {}).get('set', []))

            performers.append({
                'artist': artist_name,
                'songs': song_count,
                'tour': tour_name,
                'url': setlist.get('url')
            })

            print(f"\n  {i}. {artist_name}")
            print(f"     Songs: {song_count}")
            print(f"     Tour: {tour_name or 'None'}")
            print(f"     URL: {setlist.get('url')}")

        # STEP 3: Identify opener vs headliner
        if len(performers) > 1:
            print(f"\n{'='*80}")
            print(f"STEP 3: Identify opener(s) vs headliner")
            print(f"{'='*80}")

            # Sort by song count (descending)
            performers_sorted = sorted(performers, key=lambda x: x['songs'], reverse=True)

            likely_headliner = performers_sorted[0]
            likely_openers = performers_sorted[1:]

            print(f"\nLikely HEADLINER: {likely_headliner['artist']}")
            print(f"  Reason: Most songs ({likely_headliner['songs']})")
            if likely_headliner['tour']:
                print(f"  + Has tour name: '{likely_headliner['tour']}'")

            print(f"\nLikely OPENER(S):")
            for opener in likely_openers:
                print(f"  - {opener['artist']}")
                print(f"    Songs: {opener['songs']} (fewer than headliner)")
                print(f"    Tour: {opener['tour'] or 'None'}")

            # Check if openers appear as guests in headliner's songs
            print(f"\n{'='*80}")
            print(f"STEP 4: Verify by checking guest appearances")
            print(f"{'='*80}")

            headliner_sets = headliner_setlist.get('sets', {}).get('set', [])
            guest_artists = set()

            for set_data in headliner_sets:
                for song in set_data.get('song', []):
                    guest = song.get('with', {})
                    if guest and isinstance(guest, dict):
                        guest_name = guest.get('name')
                        if guest_name:
                            guest_artists.add(guest_name)

            if guest_artists:
                print(f"\nGuest artists in {headliner_name}'s setlist:")
                for guest in guest_artists:
                    print(f"  - {guest}")

                    # Check if any opener matches guest
                    for opener in likely_openers:
                        if guest.lower() in opener['artist'].lower() or opener['artist'].lower() in guest.lower():
                            print(f"    ✓ MATCH! This confirms {opener['artist']} was the opener")
            else:
                print(f"\nNo guest artists found in headliner's setlist")

            return {
                'headliner': likely_headliner,
                'openers': likely_openers,
                'venue': exact_venue_name,
                'all_performers': performers
            }
        else:
            print(f"\n⚠️  Only found 1 setlist - no opener detected")
            print(f"   Either no opener, or opener's setlist not on setlist.fm")
            return None

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    print("\nTEST: Smart opener detection for Mumford & Sons concert")
    print("Date: August 9, 2025")

    result = smart_opener_detection(
        headliner_name="Mumford & Sons",
        date_str="09-08-2025"
    )

    if result:
        print("\n\n")
        print("="*80)
        print("✅ SUCCESS - OPENER DETECTION WORKED!")
        print("="*80)
        print(f"\nHeadliner: {result['headliner']['artist']}")
        print(f"Openers: {', '.join([o['artist'] for o in result['openers']])}")
        print(f"Venue: {result['venue']}")

        print("\n\nIMPLEMENTATION RECOMMENDATIONS:")
        print("="*80)
        print("""
This strategy works! Here's how to implement it:

1. In fetch_setlists_enhanced.py, add a new function:
   - detect_openers(artist_name, date)
   - Returns list of opener names and their setlist URLs

2. When processing a concert:
   a) If concert.artists only has 1 headliner
   b) Call detect_openers() to check for missing openers
   c) If found, prompt user or auto-add to database

3. Heuristics for identification:
   ✓ Opener has fewer songs than headliner
   ✓ Headliner usually has tour name
   ✓ Opener often appears as guest in headliner's songs

4. Confidence levels:
   - HIGH: Opener appears as guest + has fewer songs
   - MEDIUM: Has fewer songs + no tour name
   - LOW: Found via venue search but unclear relationship
        """)
    else:
        print("\n\n")
        print("="*80)
        print("RESULT")
        print("="*80)
        print("""
Could not test due to rate limiting.

Get a fresh API key from: https://www.setlist.fm/settings/api
Then update SETLISTFM_API_KEY in this script and run again.
        """)
