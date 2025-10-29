#!/usr/bin/env python3
"""
Inspect raw setlist.fm API response for a specific concert
"""

import json
from datetime import datetime
from setlistfm_client import SetlistFMClient

SETLISTFM_API_KEY = "DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE"

def inspect_concert_847():
    """Fetch and display raw API response for concert 847"""

    client = SetlistFMClient(SETLISTFM_API_KEY)

    # Concert 847 details
    artist_names = ["Rod Stewart", "Cyndi Lauper"]
    date = datetime(2018, 8, 7)
    venue = "Madison Square Garden"
    city = "New York"
    state = "NY"

    print("="*80)
    print("SETLIST.FM API RAW RESPONSE INSPECTION")
    print("="*80)
    print(f"\nConcert: Rod Stewart & Cyndi Lauper")
    print(f"Date: {date.strftime('%Y-%m-%d')}")
    print(f"Venue: {venue}, {city}, {state}")
    print("\n" + "="*80 + "\n")

    for artist_name in artist_names:
        print(f"\n{'='*80}")
        print(f"ARTIST: {artist_name}")
        print(f"{'='*80}\n")

        setlist = client.find_setlist_for_concert(
            artist_name=artist_name,
            date=date,
            venue_name=venue,
            city=city,
            state=state
        )

        if setlist:
            print(json.dumps(setlist, indent=2))
            print("\n" + "="*80)
            print("KEY FIELDS:")
            print("="*80)
            print(f"ID: {setlist.get('id')}")
            print(f"Version ID: {setlist.get('versionId')}")
            print(f"Event Date: {setlist.get('eventDate')}")
            print(f"Last Updated: {setlist.get('lastUpdated')}")
            print(f"Artist: {setlist.get('artist', {}).get('name')}")
            print(f"Venue: {setlist.get('venue', {}).get('name')}")
            print(f"Tour: {setlist.get('tour', {}).get('name') if setlist.get('tour') else 'None'}")
            print(f"Info: {setlist.get('info') if setlist.get('info') else 'None'}")
            print(f"URL: {setlist.get('url')}")

            # Check for event type or show type fields
            print("\n" + "="*80)
            print("CHECKING FOR EVENT/SHOW TYPE FIELDS:")
            print("="*80)

            # Common fields that might indicate type
            possible_type_fields = [
                'eventType', 'type', 'showType', 'concertType',
                'category', 'eventCategory', 'kind', 'format'
            ]

            found_type_field = False
            for field in possible_type_fields:
                if field in setlist:
                    print(f"✓ Found: {field} = {setlist[field]}")
                    found_type_field = True

            if not found_type_field:
                print("✗ No explicit event type field found")
                print("\nAll top-level fields in response:")
                for key in setlist.keys():
                    print(f"  - {key}")

            # Check venue object for type info
            venue_obj = setlist.get('venue', {})
            if venue_obj:
                print("\nVenue object fields:")
                for key in venue_obj.keys():
                    print(f"  - {key}: {venue_obj[key]}")

        else:
            print(f"No setlist found for {artist_name}")

        print("\n")

if __name__ == '__main__':
    inspect_concert_847()
