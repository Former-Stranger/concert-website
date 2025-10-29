#!/usr/bin/env python3
"""
Inspect setlist.fm API response for a festival performance to identify festival fields
"""

import json
from datetime import datetime
from setlistfm_client import SetlistFMClient

SETLISTFM_API_KEY = "DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE"


def inspect_festival_show():
    """
    Fetch a setlist from Bonnaroo 2025 to see festival-specific fields
    We'll search for performances at Bonnaroo
    """

    client = SetlistFMClient(SETLISTFM_API_KEY)

    print("=" * 100)
    print("FESTIVAL SETLIST INSPECTION - BONNAROO")
    print("=" * 100)

    # Try to search for Bonnaroo setlists
    # Let's try searching by venue name "Bonnaroo" or city "Manchester, TN"

    # First, let's search for any Bonnaroo setlists from recent years
    test_cases = [
        {
            "artist": "Foo Fighters",
            "date": datetime(2022, 6, 19),  # Bonnaroo 2022
            "venue": "Great Stage Park",
            "city": "Manchester",
            "state": "TN"
        },
        {
            "artist": "Tyler, the Creator",
            "date": datetime(2024, 6, 16),  # Bonnaroo 2024
            "venue": "Great Stage Park",
            "city": "Manchester",
            "state": "TN"
        },
        {
            "artist": "Red Hot Chili Peppers",
            "date": datetime(2017, 6, 11),  # Bonnaroo 2017
            "venue": "Great Stage Park",
            "city": "Manchester",
            "state": "TN"
        }
    ]

    for test in test_cases:
        print(f"\n{'#' * 100}")
        print(f"# TESTING: {test['artist']} at Bonnaroo {test['date'].year}")
        print(f"{'#' * 100}\n")

        setlist = client.find_setlist_for_concert(
            artist_name=test['artist'],
            date=test['date'],
            venue_name=test['venue'],
            city=test['city'],
            state=test['state']
        )

        if setlist:
            print("\n" + "=" * 100)
            print("✓ SETLIST FOUND!")
            print("=" * 100)

            # Display all top-level fields
            print("\nALL TOP-LEVEL FIELDS:")
            print("-" * 100)
            for key in setlist.keys():
                print(f"  - {key}")

            # Check for festival-specific fields
            print("\n" + "=" * 100)
            print("CHECKING FOR FESTIVAL-SPECIFIC FIELDS:")
            print("=" * 100)

            festival_fields = [
                'festival', 'eventName', 'event', 'festivalName',
                'isFestival', 'festivalId', 'festivalUrl'
            ]

            found = False
            for field in festival_fields:
                if field in setlist:
                    print(f"\n✓ FOUND: '{field}'")
                    print(f"  Value: {json.dumps(setlist[field], indent=2)}")
                    found = True

            if not found:
                print("\n✗ No explicit festival fields found")

            # Show tour field (might contain festival info)
            print("\n" + "=" * 100)
            print("TOUR FIELD (might contain festival name):")
            print("=" * 100)
            if 'tour' in setlist:
                print(json.dumps(setlist['tour'], indent=2))
            else:
                print("No tour field")

            # Show venue field
            print("\n" + "=" * 100)
            print("VENUE FIELD:")
            print("=" * 100)
            if 'venue' in setlist:
                print(json.dumps(setlist['venue'], indent=2))

            # Show info field
            print("\n" + "=" * 100)
            print("INFO FIELD (might contain festival notes):")
            print("=" * 100)
            if 'info' in setlist and setlist['info']:
                print(setlist['info'])
            else:
                print("No info field")

            # Show full JSON
            print("\n" + "=" * 100)
            print("COMPLETE RAW JSON:")
            print("=" * 100)
            print(json.dumps(setlist, indent=2))

            # Found one, stop searching
            break
        else:
            print(f"✗ No setlist found for {test['artist']} on {test['date'].strftime('%Y-%m-%d')}")

    print("\n" + "=" * 100)
    print("END OF INSPECTION")
    print("=" * 100)


if __name__ == '__main__':
    inspect_festival_show()
