#!/usr/bin/env python3
"""
Setlist.fm API Client
API Documentation: https://api.setlist.fm/docs/1.0/index.html

Rate Limits:
- 2 requests per second (standard API key)
- 1440 calls per day (may vary by API key type)
"""

import requests
import time
from typing import Optional, Dict, List
from datetime import datetime
import json

class SetlistFMClient:
    """Client for interacting with the setlist.fm API"""

    BASE_URL = "https://api.setlist.fm/rest/1.0"

    def __init__(self, api_key: str):
        """
        Initialize the client with an API key

        Args:
            api_key: Your setlist.fm API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': api_key,
            'Accept': 'application/json',
            'User-Agent': 'ConcertDatabase/1.0'
        })

        # Rate limiting: 4 seconds between requests (very conservative to avoid cumulative limits)
        self.min_request_interval = 4.0  # 4 seconds = 0.25 req/sec (well under 2/sec limit)
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Make a request to the API with rate limiting

        Args:
            endpoint: API endpoint (e.g., '/search/setlists')
            params: Query parameters

        Returns:
            JSON response or None if error
        """
        self._rate_limit()

        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                return None  # Not found
            elif response.status_code == 429:
                # Check for Retry-After header
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    wait_time = int(retry_after)
                else:
                    # Default to 1 second (rate limit is per second, so window resets quickly)
                    wait_time = 1

                print(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return self._make_request(endpoint, params)  # Retry
            else:
                print(f"HTTP Error: {e}")
                return None
        except Exception as e:
            print(f"Error making request: {e}")
            return None

    def search_setlists(self,
                       artist_name: Optional[str] = None,
                       venue_name: Optional[str] = None,
                       city_name: Optional[str] = None,
                       state: Optional[str] = None,
                       date: Optional[str] = None,
                       year: Optional[int] = None,
                       page: int = 1) -> Optional[Dict]:
        """
        Search for setlists

        Args:
            artist_name: Name of the artist
            venue_name: Name of the venue
            city_name: Name of the city
            state: State code (e.g., 'NY')
            date: Date in format 'dd-MM-yyyy' (e.g., '09-05-2019')
            year: Year (e.g., 2019)
            page: Page number (default 1)

        Returns:
            Search results or None
        """
        params = {'p': page}

        if artist_name:
            params['artistName'] = artist_name
        if venue_name:
            params['venueName'] = venue_name
        if city_name:
            params['cityName'] = city_name
        if state:
            params['state'] = state
        if date:
            params['date'] = date
        if year:
            params['year'] = year

        return self._make_request('/search/setlists', params)

    def get_setlist(self, setlist_id: str) -> Optional[Dict]:
        """
        Get a specific setlist by ID

        Args:
            setlist_id: The setlist ID

        Returns:
            Setlist data or None
        """
        return self._make_request(f'/setlist/{setlist_id}')

    def search_artist(self, artist_name: str, page: int = 1) -> Optional[Dict]:
        """
        Search for an artist

        Args:
            artist_name: Name of the artist
            page: Page number

        Returns:
            Artist search results or None
        """
        params = {
            'artistName': artist_name,
            'p': page
        }
        return self._make_request('/search/artists', params)

    def find_setlist_for_concert(self,
                                 artist_name: str,
                                 date: datetime,
                                 venue_name: Optional[str] = None,
                                 city: Optional[str] = None,
                                 state: Optional[str] = None) -> Optional[Dict]:
        """
        Find a setlist for a specific concert

        Tries progressively broader searches to find a match:
        1. Artist + date + venue + city + state
        2. Artist + date + city + state (no venue)
        3. Artist + date only (most lenient)

        Args:
            artist_name: Name of the artist
            date: Concert date
            venue_name: Venue name (optional but helps matching)
            city: City name (optional)
            state: State code (optional)

        Returns:
            Best matching setlist or None
        """
        # Clean artist name - remove parenthetical notes like "(Final Franchise)" or "(75th Birthday)"
        # Also remove opener notation like "w/" or "w."
        # Also remove common band suffixes for search
        clean_artist = artist_name.split('(')[0].strip()
        clean_artist = clean_artist.split(' w/')[0].strip()
        clean_artist = clean_artist.split(' w.')[0].strip()

        # Remove band suffixes for cleaner search
        band_suffixes = [
            ' & the E Street Band',
            ' & The E Street Band',
            ' & the Silver Bullet Band',
            ' & the 400 Unit',
            ' and the E Street Band',
            ' + the E Street Band',
            ' + Joe Sumner',  # Handle "+ featured artist" patterns
        ]

        search_artist = clean_artist
        for suffix in band_suffixes:
            if suffix in search_artist:
                search_artist = search_artist.replace(suffix, '').strip()
                break

        # Format date as dd-MM-yyyy for API
        date_str = date.strftime('%d-%m-%Y')

        # Search with just artist and date (most reliable approach)
        # Venue names change frequently due to sponsorships/rebranding
        results = self.search_setlists(
            artist_name=search_artist,
            date=date_str
        )

        if results and 'setlist' in results and len(results['setlist']) > 0:
            return results['setlist'][0]

        return None

    def extract_songs_from_setlist(self, setlist_data: Dict) -> List[Dict]:
        """
        Extract song information from setlist data

        Args:
            setlist_data: Setlist JSON from API

        Returns:
            List of songs with position, name, and info
        """
        songs = []
        position = 1

        if 'sets' not in setlist_data or 'set' not in setlist_data['sets']:
            return songs

        for set_data in setlist_data['sets']['set']:
            set_name = set_data.get('name', 'Main Set')
            encore = set_data.get('encore', 0)

            if 'song' not in set_data:
                continue

            for song in set_data['song']:
                song_info = {
                    'position': position,
                    'name': song.get('name', 'Unknown'),
                    'set_name': set_name,
                    'encore': encore,
                    'cover': song.get('cover', {}).get('name') if 'cover' in song else None,
                    'tape': song.get('tape', False),  # Song played from tape/recording
                    'info': song.get('info', None)  # Additional info
                }
                songs.append(song_info)
                position += 1

        return songs


def test_client():
    """Test the client with a sample query"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 setlistfm_client.py YOUR_API_KEY")
        print("\nExample test:")
        print("  python3 setlistfm_client.py your-key-here")
        return

    api_key = sys.argv[1]
    client = SetlistFMClient(api_key)

    print("Testing setlist.fm API client...")
    print("=" * 80)

    # Test: Search for Kip Moore at Ridgefield Playhouse on May 9, 2019
    print("\nTest: Kip Moore at Ridgefield Playhouse on May 9, 2019")
    date = datetime(2019, 5, 9)

    setlist = client.find_setlist_for_concert(
        artist_name="Kip Moore",
        date=date,
        venue_name="Ridgefield Playhouse",
        city="Ridgefield",
        state="CT"
    )

    if setlist:
        print(f"✓ Found setlist!")
        print(f"  Event: {setlist.get('eventDate')}")
        print(f"  Venue: {setlist.get('venue', {}).get('name')}")

        songs = client.extract_songs_from_setlist(setlist)
        print(f"  Songs: {len(songs)}")

        if songs:
            print(f"\n  First song: {songs[0]['name']}")
            print(f"  Last song: {songs[-1]['name']}")

            # Show encore songs
            encore_songs = [s for s in songs if s['encore'] > 0]
            if encore_songs:
                print(f"\n  Encore ({len(encore_songs)} songs):")
                for song in encore_songs:
                    print(f"    - {song['name']}")
    else:
        print("✗ No setlist found")

    print("\n" + "=" * 80)
    print("Test complete!")


if __name__ == "__main__":
    test_client()
