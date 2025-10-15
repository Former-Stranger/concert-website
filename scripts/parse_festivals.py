#!/usr/bin/env python3
"""
Parse festival and multi-artist entries into individual searchable artists
"""

import re
from typing import List, Tuple, Optional

class FestivalParser:
    """Parse complex artist strings into individual artists"""

    # Band names that contain & or 'and' but are single entities
    PROTECTED_BANDS = [
        'Bruce Springsteen & the E Street Band',
        'Bruce Springsteen & E Street Band',
        'Tom Petty & the Heartbreakers',
        'Tom Petty & The Heartbreakers',
        'Hootie & the Blowfish',
        'Crosby, Stills and Nash',
        'Crosby Stills and Nash',
        'Emerson, Lake and Palmer',
        'Earth, Wind and Fire',
        'Blood, Sweat and Tears',
        'Peter, Paul and Mary',
        'Crosby and Nash',
        'Simon and Garfunkel',
        'Hall and Oates',
        'Hall & Oates',
        'Ringo Starr & His All-Starr Band',
        'Ringo Starr & His All Sarr Band',
        'Bob Seger & Silver Bullet Band',
        'Bob Seger & the Silver Bullet Band',
        'Bob Weir & Ratdog',
    ]

    def __init__(self):
        # Create patterns for protected bands
        self.protected_patterns = [
            re.escape(band.lower()) for band in self.PROTECTED_BANDS
        ]

    def is_protected_band(self, text: str) -> bool:
        """Check if text is a protected band name"""
        text_lower = text.lower().strip()
        # Clean up multiple spaces
        text_lower = ' '.join(text_lower.split())

        # Check exact matches and partial matches
        for band in self.PROTECTED_BANDS:
            band_lower = band.lower()
            # Exact match
            if text_lower == band_lower:
                return True
            # Check if the text starts with this band name
            if text_lower.startswith(band_lower + ' '):
                return True
            if text_lower.startswith(band_lower + ' ('):
                return True
        return False

    def parse_artist_entry(self, artist_string: str) -> Tuple[Optional[str], List[str]]:
        """
        Parse an artist entry into festival name and individual artists

        Returns:
            (festival_name, [list of artists])
            If not a festival, festival_name will be None
        """
        if not artist_string or artist_string == 'nan':
            return None, []

        artist_string = artist_string.strip()

        # Pattern 1: Festival with colon (e.g., "Outlaw Festival: Dylan, Nelson")
        if ':' in artist_string:
            if any(keyword in artist_string for keyword in ['Festival', 'Concert', 'Benefit', 'Relief', 'Upfront', 'Earth']):
                parts = artist_string.split(':', 1)
                festival_name = parts[0].strip()
                artists_part = parts[1].strip() if len(parts) > 1 else ''

                # Parse the artists part
                artists = self._parse_artist_list(artists_part)
                return festival_name, artists

        # Pattern 2: Multiple artists with commas (3+ names)
        # But NOT if it's a protected band name
        if artist_string.count(',') >= 2:
            # Check if whole thing is protected
            if self.is_protected_band(artist_string):
                return None, [artist_string]

            # Check for parenthetical list format
            if '(' in artist_string and ')' in artist_string:
                # Extract the parenthetical part
                match = re.match(r'^([^(]+)\s*\((.+)\)$', artist_string)
                if match:
                    main_part = match.group(1).strip()
                    paren_part = match.group(2).strip()

                    # Check if main part looks like a festival/event name
                    if any(keyword in main_part for keyword in ['Concert', 'Benefit', 'Light of Day']):
                        artists = self._parse_artist_list(paren_part)
                        return main_part, artists

            # Otherwise, parse as list of artists
            artists = self._parse_artist_list(artist_string)
            if len(artists) >= 3:
                return 'Multi-Artist Show', artists

        # Pattern 3: Artist & Artist (but not protected band names)
        if ' & ' in artist_string:
            # Check if whole string is a protected band
            if self.is_protected_band(artist_string):
                return None, [artist_string]

            # Split and check each part
            parts = artist_string.split(' & ')
            valid_artists = []
            current_protected = None

            for i, part in enumerate(parts):
                part = part.strip()

                # Check if this part combines with previous to form protected band
                if current_protected:
                    combined = f"{current_protected} & {part}"
                    if self.is_protected_band(combined):
                        valid_artists[-1] = combined
                        current_protected = combined
                        continue
                    else:
                        current_protected = None

                # Check if this part starts a protected band
                if self.is_protected_band(part):
                    current_protected = part
                    valid_artists.append(part)
                else:
                    valid_artists.append(part)

            if len(valid_artists) > 1:
                return 'Multi-Artist Show', valid_artists

        # Pattern 4: Artist and Artist (but not protected band names)
        if ' and ' in artist_string.lower():
            if self.is_protected_band(artist_string):
                return None, [artist_string]

            # Check for pattern like "A and B with C"
            if ' with ' in artist_string.lower():
                # This is likely already handled by opener logic
                return None, [artist_string]

            # Split by ' and ' case-insensitively
            parts = re.split(r'\s+and\s+', artist_string, flags=re.IGNORECASE)
            if len(parts) > 1 and not self.is_protected_band(artist_string):
                # Check each part
                valid_artists = [p.strip() for p in parts if p.strip()]
                if len(valid_artists) > 1:
                    return 'Multi-Artist Show', valid_artists

        # Not a multi-artist entry
        return None, [artist_string]

    def _parse_artist_list(self, artists_string: str) -> List[str]:
        """Parse a string containing multiple artist names"""
        if not artists_string:
            return []

        # Remove common prefixes
        artists_string = re.sub(r'^with\s+', '', artists_string, flags=re.IGNORECASE)

        # First, try to split by commas and 'and'
        # Replace ' and ' with ','
        artists_string = re.sub(r'\s+and\s+', ',', artists_string, flags=re.IGNORECASE)

        # Split by commas
        parts = [p.strip() for p in artists_string.split(',')]

        # Clean up each artist name
        artists = []
        for part in parts:
            if not part:
                continue

            # Remove extra whitespace
            part = ' '.join(part.split())

            # Skip empty or very short names
            if len(part) < 2:
                continue

            artists.append(part)

        return artists

def test_parser():
    """Test the parser with various examples"""
    parser = FestivalParser()

    test_cases = [
        "Outlaw Festival: Bob Dylan and Willie Nelson",
        "Bruce Springsteen & the E Street Band",
        "Tom Petty & the Heartbreakers",
        "Elton John & Billy Joel",
        "Newport Folk Festival: Sheryl Crow, Phil Lesh",
        "12-12-12 Concert For Sandy Relief: Bruce Springsteen, Paul McCartney, Rolling Stones",
        "Crosby, Stills and Nash",
        "Crosby and Nash",
        "Hall & Oates",
        "Billy Joel",
        "Ringo Starr & His All-Starr Band (Kirke, Jack Bruce, Gary Brooker, Frampton)",
    ]

    print("=" * 80)
    print("FESTIVAL PARSER TEST")
    print("=" * 80)

    for test in test_cases:
        festival, artists = parser.parse_artist_entry(test)
        print(f"\nInput: {test}")
        if festival:
            print(f"  Festival: {festival}")
            print(f"  Artists: {', '.join(artists)}")
        else:
            print(f"  Single artist: {artists[0] if artists else 'None'}")

if __name__ == "__main__":
    test_parser()
