#!/usr/bin/env python3
"""
Automated Opener Detection Script

This script scans concerts with single headliners and uses the setlist.fm API
to detect potentially missing opening acts.

Strategy:
1. Find concerts with only 1 artist (potential missing openers)
2. For each concert, search headliner + date on setlist.fm
3. Use exact venue name to search for all performers that day
4. Identify openers using heuristics:
   - Fewer songs than headliner
   - Appears as guest in headliner's setlist
   - No tour name or less prominent tour
5. Generate report with confidence levels for manual review

Usage:
    # Scan all concerts
    python3 detect_missing_openers.py

    # Scan specific concert
    python3 detect_missing_openers.py --concert-id 1274

    # Output to file
    python3 detect_missing_openers.py --output detected_openers.json

    # Limit number of concerts to check
    python3 detect_missing_openers.py --limit 50
"""

import sys
import os
import argparse
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time

# Add parent directory to path to import Firebase utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import firebase_admin
from firebase_admin import credentials, firestore
from setlistfm_client import SetlistFMClient


class OpenerDetector:
    """Detects missing opening acts using setlist.fm API"""

    def __init__(self, api_key: str, db):
        """
        Initialize detector

        Args:
            api_key: setlist.fm API key
            db: Firestore database reference
        """
        self.client = SetlistFMClient(api_key)
        self.db = db
        self.detected_openers = []

    def get_single_headliner_concerts(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get concerts that have only 1 artist (potential missing openers)

        Args:
            limit: Maximum number of concerts to check

        Returns:
            List of concert documents
        """
        concerts_ref = self.db.collection('concerts')
        query = concerts_ref.order_by('date', direction=firestore.Query.DESCENDING)

        if limit:
            query = query.limit(limit * 2)  # Get extra since we'll filter

        all_concerts = [doc.to_dict() for doc in query.stream()]

        # Filter to only concerts with 1 artist
        single_artist_concerts = []
        for concert in all_concerts:
            artists = concert.get('artists', [])
            if len(artists) == 1:
                single_artist_concerts.append(concert)

                if limit and len(single_artist_concerts) >= limit:
                    break

        return single_artist_concerts

    def detect_openers_for_concert(self, concert: Dict) -> Optional[Dict]:
        """
        Detect potential openers for a single concert

        Args:
            concert: Concert document from Firestore

        Returns:
            Detection result with openers and confidence, or None if no openers found
        """
        concert_id = concert.get('id')
        date_str = concert.get('date')  # YYYY-MM-DD
        artists = concert.get('artists', [])

        if not artists:
            return None

        headliner = artists[0]
        headliner_name = headliner.get('artist_name', '')

        if not headliner_name or not date_str:
            return None

        print(f"\n{'='*80}")
        print(f"Concert {concert_id}: {headliner_name}")
        print(f"Date: {date_str}")
        print(f"{'='*80}")

        try:
            # Convert date format
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            api_date_str = date_obj.strftime('%d-%m-%Y')

            # STEP 1: Find headliner's setlist
            print(f"Step 1: Searching for {headliner_name}'s setlist...")

            result = self.client.search_setlists(
                artist_name=headliner_name,
                date=api_date_str
            )

            if not result or not result.get('setlist'):
                print("  ✗ Headliner setlist not found")
                return None

            headliner_setlist = result['setlist'][0]
            venue = headliner_setlist.get('venue', {})
            exact_venue_name = venue.get('name', '')

            print(f"  ✓ Found at: {exact_venue_name}")

            # Count headliner songs
            headliner_songs = sum(
                len(s.get('song', []))
                for s in headliner_setlist.get('sets', {}).get('set', [])
            )
            print(f"  Songs: {headliner_songs}")

            # STEP 2: Search for all performers at venue + date
            print(f"\nStep 2: Searching for all performers at {exact_venue_name}...")

            result2 = self.client.search_setlists(
                venue_name=exact_venue_name,
                date=api_date_str
            )

            if not result2 or not result2.get('setlist'):
                print("  ✗ No results for venue search")
                return None

            all_setlists = result2['setlist']
            print(f"  ✓ Found {len(all_setlists)} setlist(s)")

            if len(all_setlists) <= 1:
                print("  ✗ Only 1 setlist found (no opener)")
                return None

            # STEP 3: Identify potential openers
            print(f"\nStep 3: Analyzing performers...")

            performers = []
            for setlist in all_setlists:
                artist = setlist.get('artist', {})
                artist_name = artist.get('name', '')
                artist_mbid = artist.get('mbid', '')  # MusicBrainz ID
                tour = setlist.get('tour', {})
                tour_name = tour.get('name') if tour else None

                song_count = sum(
                    len(s.get('song', []))
                    for s in setlist.get('sets', {}).get('set', [])
                )

                performers.append({
                    'artist_name': artist_name,
                    'artist_mbid': artist_mbid,
                    'song_count': song_count,
                    'tour_name': tour_name,
                    'setlistfm_id': setlist.get('id'),
                    'setlistfm_url': setlist.get('url'),
                    'setlist_data': setlist
                })

                print(f"  - {artist_name}: {song_count} songs")

            # Sort by song count (descending)
            performers.sort(key=lambda x: x['song_count'], reverse=True)

            likely_headliner = performers[0]
            potential_openers = performers[1:]

            # STEP 4: Check for guest appearances (high confidence signal)
            print(f"\nStep 4: Checking for guest appearances...")

            guest_artists = set()
            headliner_sets = headliner_setlist.get('sets', {}).get('set', [])

            for set_data in headliner_sets:
                for song in set_data.get('song', []):
                    guest = song.get('with', {})
                    if guest and isinstance(guest, dict):
                        guest_name = guest.get('name')
                        if guest_name:
                            guest_artists.add(guest_name.lower())

            # Assign confidence levels
            detected_openers = []
            for opener in potential_openers:
                confidence = self._calculate_confidence(
                    opener=opener,
                    headliner=likely_headliner,
                    guest_artists=guest_artists
                )

                if confidence > 0:
                    opener['confidence'] = confidence
                    opener['confidence_label'] = self._confidence_label(confidence)
                    detected_openers.append(opener)

                    print(f"  ✓ {opener['artist_name']}: {opener['confidence_label']} confidence")

            if not detected_openers:
                print("  ✗ No high-confidence openers detected")
                return None

            return {
                'concert_id': concert_id,
                'concert_date': date_str,
                'venue': exact_venue_name,
                'headliner': {
                    'name': likely_headliner['artist_name'],
                    'song_count': likely_headliner['song_count']
                },
                'detected_openers': detected_openers,
                'guest_artists': list(guest_artists)
            }

        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _calculate_confidence(self,
                             opener: Dict,
                             headliner: Dict,
                             guest_artists: set) -> float:
        """
        Calculate confidence score for detected opener

        Args:
            opener: Opener performer info
            headliner: Headliner performer info
            guest_artists: Set of guest artist names (lowercase)

        Returns:
            Confidence score (0-100)
        """
        confidence = 0

        # Base confidence: Has fewer songs than headliner
        if opener['song_count'] < headliner['song_count']:
            confidence += 30
        else:
            return 0  # Not an opener if equal/more songs

        # High confidence: Appears as guest in headliner's set
        opener_name_lower = opener['artist_name'].lower()
        for guest in guest_artists:
            if opener_name_lower in guest or guest in opener_name_lower:
                confidence += 50
                break

        # Medium confidence: Opener has significantly fewer songs
        song_ratio = opener['song_count'] / headliner['song_count']
        if song_ratio < 0.5:  # Less than 50% of headliner
            confidence += 15

        # Low confidence: Opener has no tour name (less established)
        if not opener['tour_name']:
            confidence += 5

        return min(confidence, 100)

    def _confidence_label(self, confidence: float) -> str:
        """Get confidence label"""
        if confidence >= 80:
            return "HIGH"
        elif confidence >= 50:
            return "MEDIUM"
        else:
            return "LOW"

    def scan_concerts(self,
                     concert_id: Optional[str] = None,
                     limit: Optional[int] = None) -> List[Dict]:
        """
        Scan concerts for missing openers

        Args:
            concert_id: Specific concert to check (optional)
            limit: Max concerts to scan (optional)

        Returns:
            List of detection results
        """
        if concert_id:
            # Check specific concert
            doc = self.db.collection('concerts').document(concert_id).get()
            if not doc.exists:
                print(f"Concert {concert_id} not found")
                return []

            concerts = [doc.to_dict()]
        else:
            # Get all single-headliner concerts
            print(f"Finding concerts with single headliners...")
            concerts = self.get_single_headliner_concerts(limit)
            print(f"Found {len(concerts)} concerts to check")

        results = []
        for i, concert in enumerate(concerts, 1):
            print(f"\n[{i}/{len(concerts)}]")

            result = self.detect_openers_for_concert(concert)
            if result:
                results.append(result)
                self.detected_openers.append(result)

        return results

    def generate_report(self, results: List[Dict]) -> str:
        """
        Generate human-readable report

        Args:
            results: Detection results

        Returns:
            Report string
        """
        report = []
        report.append("="*80)
        report.append("OPENER DETECTION REPORT")
        report.append("="*80)
        report.append(f"\nTotal concerts scanned: {len(results)}")
        report.append(f"Openers detected: {sum(len(r['detected_openers']) for r in results)}")

        # Group by confidence
        high_conf = []
        med_conf = []
        low_conf = []

        for result in results:
            for opener in result['detected_openers']:
                item = (result['concert_id'], result['concert_date'],
                       result['headliner']['name'], opener)

                if opener['confidence'] >= 80:
                    high_conf.append(item)
                elif opener['confidence'] >= 50:
                    med_conf.append(item)
                else:
                    low_conf.append(item)

        report.append(f"\nHIGH confidence: {len(high_conf)}")
        report.append(f"MEDIUM confidence: {len(med_conf)}")
        report.append(f"LOW confidence: {len(low_conf)}")

        # HIGH confidence openers
        if high_conf:
            report.append("\n" + "="*80)
            report.append("HIGH CONFIDENCE OPENERS (Recommended for auto-add)")
            report.append("="*80)

            for concert_id, date, headliner, opener in high_conf:
                report.append(f"\nConcert {concert_id} ({date})")
                report.append(f"  Headliner: {headliner}")
                report.append(f"  Opener: {opener['artist_name']} ({opener['song_count']} songs)")
                report.append(f"  Confidence: {opener['confidence']}%")
                report.append(f"  URL: {opener['setlistfm_url']}")

        # MEDIUM confidence openers
        if med_conf:
            report.append("\n" + "="*80)
            report.append("MEDIUM CONFIDENCE OPENERS (Review recommended)")
            report.append("="*80)

            for concert_id, date, headliner, opener in med_conf:
                report.append(f"\nConcert {concert_id} ({date})")
                report.append(f"  Headliner: {headliner}")
                report.append(f"  Opener: {opener['artist_name']} ({opener['song_count']} songs)")
                report.append(f"  Confidence: {opener['confidence']}%")
                report.append(f"  URL: {opener['setlistfm_url']}")

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Detect missing opening acts using setlist.fm API"
    )
    parser.add_argument(
        '--concert-id',
        help='Check specific concert ID'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of concerts to scan'
    )
    parser.add_argument(
        '--output',
        help='Output file for JSON results'
    )
    parser.add_argument(
        '--api-key',
        help='setlist.fm API key (or set SETLISTFM_API_KEY env var)'
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get('SETLISTFM_API_KEY')
    if not api_key:
        print("Error: API key required")
        print("Provide via --api-key or SETLISTFM_API_KEY environment variable")
        sys.exit(1)

    # Initialize Firebase
    if not firebase_admin._apps:
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'earplugs-and-memories'),
            })
        except Exception as e:
            print(f"Error: Could not initialize Firebase: {e}")
            print("Make sure you're authenticated with: gcloud auth application-default login")
            sys.exit(1)

    db = firestore.client()

    # Run detection
    print("Starting opener detection...")
    print(f"API Key: {api_key[:10]}...")

    detector = OpenerDetector(api_key, db)
    results = detector.scan_concerts(
        concert_id=args.concert_id,
        limit=args.limit
    )

    # Generate report
    print("\n\n")
    report = detector.generate_report(results)
    print(report)

    # Save to file if requested
    if args.output:
        output_data = {
            'scan_date': datetime.now().isoformat(),
            'total_concerts_scanned': len(results),
            'results': results
        }

        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\n\nResults saved to: {args.output}")

    print("\n\nNext steps:")
    print("1. Review the detected openers (especially HIGH confidence)")
    print("2. Use fix_concert_1274.py as template to add approved openers")
    print("3. Or modify this script to auto-add HIGH confidence openers")


if __name__ == '__main__':
    main()
