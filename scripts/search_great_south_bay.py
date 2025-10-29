#!/usr/bin/env python3
"""
Search for Great South Bay Music Festival 2008 setlists
"""

import json
from datetime import datetime
from setlistfm_client import SetlistFMClient

SETLISTFM_API_KEY = "DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE"


def search_festival():
    """Search for Great South Bay Music Festival April 6, 2008 in Oakdale, NY"""

    client = SetlistFMClient(SETLISTFM_API_KEY)

    print("=" * 100)
    print("SEARCHING FOR GREAT SOUTH BAY MUSIC FESTIVAL - APRIL 6, 2008")
    print("=" * 100)

    # Try different search approaches
    searches = [
        # Search by city and date
        {
            "city_name": "Oakdale",
            "state": "NY",
            "date": "06-04-2008"  # dd-MM-yyyy format
        },
        # Search by city and year
        {
            "city_name": "Oakdale",
            "state": "NY",
            "year": 2008
        },
        # Try venue name variations
        {
            "venue_name": "Great South Bay",
            "year": 2008
        },
        {
            "venue_name": "South Shore Music Theatre",
            "year": 2008
        },
    ]

    all_setlists = []

    for i, search_params in enumerate(searches, 1):
        print(f"\n{'#' * 100}")
        print(f"# SEARCH ATTEMPT {i}: {search_params}")
        print(f"{'#' * 100}\n")

        result = client.search_setlists(**search_params)

        if result and 'setlist' in result:
            setlists = result['setlist']
            print(f"✓ FOUND {len(setlists)} SETLISTS")

            # Filter to April 6, 2008
            for setlist in setlists:
                event_date = setlist.get('eventDate', '')
                if event_date == '06-04-2008':
                    all_setlists.append(setlist)
                    print(f"  - {setlist.get('artist', {}).get('name')} on {event_date}")
        else:
            print("✗ No results")

    if not all_setlists:
        print("\n" + "=" * 100)
        print("NO SETLISTS FOUND FOR APRIL 6, 2008")
        print("=" * 100)
        return

    print("\n" + "=" * 100)
    print(f"FOUND {len(all_setlists)} SETLISTS FOR APRIL 6, 2008 IN OAKDALE, NY")
    print("=" * 100)

    # Display each setlist
    for idx, setlist in enumerate(all_setlists, 1):
        print(f"\n\n{'#' * 100}")
        print(f"# SETLIST {idx}/{len(all_setlists)}: {setlist.get('artist', {}).get('name')}")
        print(f"{'#' * 100}\n")

        print("=" * 100)
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
            print(f"  - {key}")

        print("\n" + "=" * 100)
        print("CHECKING FOR FESTIVAL/EVENT FIELDS:")
        print("=" * 100)

        festival_keywords = [
            'festival', 'eventName', 'event', 'festivalName',
            'isFestival', 'festivalId', 'festivalUrl', 'eventType'
        ]

        found_festival = False
        for keyword in festival_keywords:
            if keyword in setlist:
                print(f"✓ FOUND '{keyword}': {json.dumps(setlist[keyword], indent=2)}")
                found_festival = True

        if not found_festival:
            print("✗ No explicit festival fields found")

        print("\n" + "=" * 100)
        print("TOUR FIELD:")
        print("=" * 100)
        if 'tour' in setlist and setlist['tour']:
            print(json.dumps(setlist['tour'], indent=2))
        else:
            print("No tour field")

        print("\n" + "=" * 100)
        print("INFO FIELD:")
        print("=" * 100)
        if 'info' in setlist and setlist['info']:
            print(setlist['info'])
        else:
            print("No info field")

        print("\n" + "=" * 100)
        print("VENUE DETAILS:")
        print("=" * 100)
        print(json.dumps(setlist.get('venue', {}), indent=2))

        print("\n" + "=" * 100)
        print("ARTIST DETAILS:")
        print("=" * 100)
        print(json.dumps(setlist.get('artist', {}), indent=2))

        # Show song count
        song_count = 0
        if 'sets' in setlist and 'set' in setlist['sets']:
            for set_data in setlist['sets']['set']:
                song_count += len(set_data.get('song', []))
        print("\n" + "=" * 100)
        print(f"SONGS: {song_count} total")
        print("=" * 100)

        print("\n" + "=" * 100)
        print("COMPLETE RAW JSON:")
        print("=" * 100)
        print(json.dumps(setlist, indent=2))

    print("\n\n" + "=" * 100)
    print("END OF DATA")
    print("=" * 100)


if __name__ == '__main__':
    search_festival()
