#!/usr/bin/env python3
"""
Display all available setlist.fm data for concert 847 in a readable format
"""

import json
from datetime import datetime
from setlistfm_client import SetlistFMClient

SETLISTFM_API_KEY = "DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE"


def display_field(label, value, indent=0):
    """Display a field with proper formatting"""
    prefix = "  " * indent
    if value is None:
        print(f"{prefix}{label}: None")
    elif isinstance(value, bool):
        print(f"{prefix}{label}: {value}")
    elif isinstance(value, (int, float)):
        print(f"{prefix}{label}: {value}")
    elif isinstance(value, str):
        if len(value) > 100:
            print(f"{prefix}{label}: {value[:100]}...")
        else:
            print(f"{prefix}{label}: {value}")
    elif isinstance(value, dict):
        print(f"{prefix}{label}:")
        for k, v in value.items():
            display_field(k, v, indent + 1)
    elif isinstance(value, list):
        print(f"{prefix}{label}: [{len(value)} items]")
        for i, item in enumerate(value):
            if isinstance(item, dict):
                print(f"{prefix}  [{i}]:")
                for k, v in item.items():
                    display_field(k, v, indent + 2)
            else:
                print(f"{prefix}  [{i}]: {item}")
    else:
        print(f"{prefix}{label}: {value}")


def show_full_data():
    """Fetch and display all available data for concert 847"""

    client = SetlistFMClient(SETLISTFM_API_KEY)

    artists = [
        {"name": "Rod Stewart", "date": datetime(2018, 8, 7)},
        {"name": "Cyndi Lauper", "date": datetime(2018, 8, 7)}
    ]

    venue = "Madison Square Garden"
    city = "New York"
    state = "NY"

    print("=" * 100)
    print("COMPLETE SETLIST.FM DATA FOR CONCERT 847")
    print("=" * 100)
    print(f"\nConcert: Rod Stewart & Cyndi Lauper")
    print(f"Date: August 7, 2018")
    print(f"Venue: {venue}, {city}, {state}")
    print("\n" + "=" * 100)

    for artist_info in artists:
        artist_name = artist_info["name"]
        date = artist_info["date"]

        print(f"\n\n{'#' * 100}")
        print(f"# ARTIST: {artist_name}")
        print(f"{'#' * 100}\n")

        setlist = client.find_setlist_for_concert(
            artist_name=artist_name,
            date=date,
            venue_name=venue,
            city=city,
            state=state
        )

        if setlist:
            # Display all fields in order
            print("\n" + "=" * 100)
            print("TOP-LEVEL FIELDS")
            print("=" * 100)

            for key in ['id', 'versionId', 'eventDate', 'lastUpdated', 'info']:
                if key in setlist:
                    display_field(key, setlist[key])

            print("\n" + "=" * 100)
            print("ARTIST INFORMATION")
            print("=" * 100)
            if 'artist' in setlist:
                display_field('artist', setlist['artist'])

            print("\n" + "=" * 100)
            print("VENUE INFORMATION")
            print("=" * 100)
            if 'venue' in setlist:
                display_field('venue', setlist['venue'])

            print("\n" + "=" * 100)
            print("TOUR INFORMATION")
            print("=" * 100)
            if 'tour' in setlist:
                display_field('tour', setlist['tour'])
            else:
                print("  No tour information")

            print("\n" + "=" * 100)
            print("SETLIST (SONGS)")
            print("=" * 100)
            if 'sets' in setlist:
                sets = setlist['sets']
                if 'set' in sets:
                    for set_idx, set_data in enumerate(sets['set']):
                        encore = set_data.get('encore', 0)
                        if encore:
                            print(f"\n  ENCORE {encore}:")
                        else:
                            print(f"\n  SET {set_idx + 1}:")

                        if 'name' in set_data and set_data['name']:
                            print(f"    Name: {set_data['name']}")

                        if 'song' in set_data:
                            for song_idx, song in enumerate(set_data['song'], 1):
                                print(f"\n    {song_idx}. {song.get('name', 'Unknown')}")

                                # Cover info
                                if 'cover' in song:
                                    cover = song['cover']
                                    print(f"       Cover of: {cover.get('name', 'Unknown')}")
                                    if 'disambiguation' in cover and cover['disambiguation']:
                                        print(f"       ({cover['disambiguation']})")

                                # Guest artist
                                if 'with' in song:
                                    guest = song['with']
                                    if isinstance(guest, dict):
                                        print(f"       With: {guest.get('name', 'Unknown')}")
                                    else:
                                        print(f"       With: {guest}")

                                # Tape indicator
                                if song.get('tape'):
                                    print(f"       [TAPE]")

                                # Additional info
                                if 'info' in song and song['info']:
                                    print(f"       Note: {song['info']}")

            print("\n" + "=" * 100)
            print("URL")
            print("=" * 100)
            print(f"  {setlist.get('url', 'N/A')}")

            print("\n" + "=" * 100)
            print("RAW JSON (for debugging)")
            print("=" * 100)
            print(json.dumps(setlist, indent=2))

        else:
            print(f"✗ No setlist found for {artist_name}")

    print("\n\n" + "=" * 100)
    print("END OF DATA")
    print("=" * 100)


if __name__ == '__main__':
    show_full_data()
