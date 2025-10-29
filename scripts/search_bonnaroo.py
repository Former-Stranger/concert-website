#!/usr/bin/env python3
"""
Search for Bonnaroo setlists and inspect the data structure
"""

import json
from setlistfm_client import SetlistFMClient

SETLISTFM_API_KEY = "DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE"


def search_bonnaroo():
    """Search for Bonnaroo setlists"""

    client = SetlistFMClient(SETLISTFM_API_KEY)

    print("=" * 100)
    print("SEARCHING FOR BONNAROO FESTIVAL SETLISTS")
    print("=" * 100)

    # Try different search approaches
    searches = [
        {"venue_name": "Great Stage Park", "city_name": "Manchester", "year": 2019},
        {"venue_name": "Great Stage Park", "city_name": "Manchester", "year": 2022},
        {"venue_name": "Bonnaroo", "year": 2019},
    ]

    for search_params in searches:
        print(f"\n{'#' * 100}")
        print(f"# SEARCH: {search_params}")
        print(f"{'#' * 100}\n")

        result = client.search_setlists(**search_params)

        if result and 'setlist' in result:
            setlists = result['setlist']
            print(f"\n✓ FOUND {len(setlists)} SETLISTS")

            if setlists:
                # Take the first one
                setlist = setlists[0]

                print("\n" + "=" * 100)
                print("FIRST SETLIST BASIC INFO:")
                print("=" * 100)
                print(f"Artist: {setlist.get('artist', {}).get('name')}")
                print(f"Date: {setlist.get('eventDate')}")
                print(f"Venue: {setlist.get('venue', {}).get('name')}")
                print(f"URL: {setlist.get('url')}")

                # Check all top-level fields
                print("\n" + "=" * 100)
                print("ALL TOP-LEVEL FIELDS:")
                print("=" * 100)
                for key in setlist.keys():
                    print(f"  - {key}")

                # Check for festival fields
                print("\n" + "=" * 100)
                print("FESTIVAL-SPECIFIC FIELDS:")
                print("=" * 100)

                festival_fields = ['festival', 'eventName', 'event', 'festivalName', 'isFestival']
                found_festival = False

                for field in festival_fields:
                    if field in setlist:
                        print(f"\n✓ '{field}': {json.dumps(setlist[field], indent=2)}")
                        found_festival = True

                if not found_festival:
                    print("✗ No explicit festival fields found")

                # Show tour field
                if 'tour' in setlist:
                    print("\n" + "=" * 100)
                    print("TOUR FIELD:")
                    print("=" * 100)
                    print(json.dumps(setlist['tour'], indent=2))

                # Show info field
                if 'info' in setlist and setlist['info']:
                    print("\n" + "=" * 100)
                    print("INFO FIELD:")
                    print("=" * 100)
                    print(setlist['info'])

                # Show venue details
                print("\n" + "=" * 100)
                print("VENUE DETAILS:")
                print("=" * 100)
                print(json.dumps(setlist.get('venue', {}), indent=2))

                # Full JSON
                print("\n" + "=" * 100)
                print("COMPLETE RAW JSON:")
                print("=" * 100)
                print(json.dumps(setlist, indent=2))

                # Success - stop searching
                return
        else:
            print("✗ No results")

    print("\n" + "=" * 100)
    print("Could not find any Bonnaroo setlists")
    print("=" * 100)


if __name__ == '__main__':
    search_bonnaroo()
