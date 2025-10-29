#!/usr/bin/env python3
"""
Fetch Jackson Browne at Great South Bay Music Festival - April 6, 2008
"""

import json
from datetime import datetime
from setlistfm_client import SetlistFMClient

SETLISTFM_API_KEY = "DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE"


def fetch_jackson_browne_festival():
    """Fetch Jackson Browne setlist from Great South Bay Festival"""

    client = SetlistFMClient(SETLISTFM_API_KEY)

    print("=" * 100)
    print("FETCHING: Jackson Browne - Great South Bay Music Festival")
    print("Date: April 6, 2008")
    print("Location: Oakdale, NY")
    print("=" * 100)

    # Try to find the setlist
    setlist = client.find_setlist_for_concert(
        artist_name="Jackson Browne",
        date=datetime(2008, 4, 6),
        venue_name="Great South Bay Music Festival",
        city="Oakdale",
        state="NY"
    )

    if not setlist:
        # Try alternate venue names
        print("\nFirst search failed, trying alternate venue names...\n")

        venues_to_try = [
            "South Shore Music Theatre",
            "Great South Bay",
            "Oakdale Theatre",
        ]

        for venue in venues_to_try:
            print(f"Trying venue: {venue}")
            setlist = client.find_setlist_for_concert(
                artist_name="Jackson Browne",
                date=datetime(2008, 4, 6),
                venue_name=venue,
                city="Oakdale",
                state="NY"
            )
            if setlist:
                break

    if not setlist:
        print("\n" + "=" * 100)
        print("NO SETLIST FOUND")
        print("=" * 100)
        return

    print("\n" + "=" * 100)
    print("✓ SETLIST FOUND!")
    print("=" * 100)

    print("\n" + "=" * 100)
    print("BASIC INFO:")
    print("=" * 100)
    print(f"Artist: {setlist.get('artist', {}).get('name')}")
    print(f"Date: {setlist.get('eventDate')}")
    print(f"Venue: {setlist.get('venue', {}).get('name')}")
    print(f"City: {setlist.get('venue', {}).get('city', {}).get('name')}, {setlist.get('venue', {}).get('city', {}).get('stateCode')}")
    print(f"URL: {setlist.get('url')}")

    print("\n" + "=" * 100)
    print("ALL TOP-LEVEL FIELDS:")
    print("=" * 100)
    for key in sorted(setlist.keys()):
        value_preview = str(setlist[key])[:50] if not isinstance(setlist[key], (dict, list)) else type(setlist[key]).__name__
        print(f"  - {key}: {value_preview}")

    print("\n" + "=" * 100)
    print("CHECKING FOR FESTIVAL/EVENT FIELDS:")
    print("=" * 100)

    festival_keywords = [
        'festival', 'eventName', 'event', 'festivalName',
        'isFestival', 'festivalId', 'festivalUrl', 'eventType',
        'festivalEdition', 'eventInfo'
    ]

    found_festival = False
    for keyword in festival_keywords:
        if keyword in setlist:
            print(f"\n✓ FOUND '{keyword}':")
            print(json.dumps(setlist[keyword], indent=2))
            found_festival = True

    if not found_festival:
        print("✗ No explicit festival fields in top level")

    print("\n" + "=" * 100)
    print("TOUR FIELD:")
    print("=" * 100)
    if 'tour' in setlist and setlist['tour']:
        print(json.dumps(setlist['tour'], indent=2))
    else:
        print("No tour field or empty")

    print("\n" + "=" * 100)
    print("INFO FIELD:")
    print("=" * 100)
    if 'info' in setlist and setlist['info']:
        print(setlist['info'])
    else:
        print("No info field or empty")

    print("\n" + "=" * 100)
    print("VENUE DETAILS (checking for festival info):")
    print("=" * 100)
    venue = setlist.get('venue', {})
    print(json.dumps(venue, indent=2))

    # Check if venue has festival-related fields
    venue_festival_fields = ['festival', 'festivalId', 'isFestival', 'type']
    venue_has_festival = False
    for field in venue_festival_fields:
        if field in venue:
            print(f"\n✓ Venue has '{field}': {venue[field]}")
            venue_has_festival = True

    if not venue_has_festival:
        print("\n✗ No festival fields in venue object")

    print("\n" + "=" * 100)
    print("ARTIST DETAILS:")
    print("=" * 100)
    print(json.dumps(setlist.get('artist', {}), indent=2))

    # Show songs
    print("\n" + "=" * 100)
    print("SETLIST:")
    print("=" * 100)
    if 'sets' in setlist and 'set' in setlist['sets']:
        for set_idx, set_data in enumerate(setlist['sets']['set'], 1):
            encore = set_data.get('encore', 0)
            if encore:
                print(f"\nENCORE {encore}:")
            else:
                print(f"\nSET {set_idx}:")

            for song_idx, song in enumerate(set_data.get('song', []), 1):
                print(f"  {song_idx}. {song.get('name')}")

    print("\n" + "=" * 100)
    print("COMPLETE RAW JSON (ALL FIELDS):")
    print("=" * 100)
    print(json.dumps(setlist, indent=2))


if __name__ == '__main__':
    fetch_jackson_browne_festival()
