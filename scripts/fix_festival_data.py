#!/usr/bin/env python3
"""
Fix festival data structure issues.

This script identifies and fixes:
1. Festival names embedded in artist names (e.g., "Sea Hear Now (Stevie Nicks)")
2. Missing festival_name field when it should be set
3. Incorrect artist roles for festival performers
"""

import firebase_admin
from firebase_admin import credentials, firestore
import re
import sys
import os

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'earplugs-and-memories'),
            })
        except Exception as e:
            print(f"Could not use application default credentials: {e}")
            sys.exit(1)

def find_festival_issues():
    """Find concerts with festival naming issues"""

    db = firestore.client()
    concerts = list(db.collection('concerts').stream())

    issues = []

    for concert_doc in concerts:
        concert_id = concert_doc.id
        data = concert_doc.to_dict()

        for artist in data.get('artists', []):
            artist_name = artist.get('artist_name', '')

            # Pattern: "Festival/Event Name (Actual Artist)"
            match = re.match(r'^([^(]+)\s*\(([^)]+)\)$', artist_name)
            if match:
                possible_festival = match.group(1).strip()
                possible_artist = match.group(2).strip()

                # Skip if it's clearly not a festival (e.g., "Billy Joel (100th)")
                # These are notes, not festivals
                if re.search(r'\d+(st|nd|rd|th)', possible_artist):
                    continue
                if possible_artist.lower() in ['acoustic', 'band', 'with', 'w.']:
                    continue

                issues.append({
                    'concert_id': concert_id,
                    'date': data.get('date'),
                    'venue': data.get('venue_name'),
                    'current_artist_name': artist_name,
                    'current_festival_name': data.get('festival_name'),
                    'suggested_festival': possible_festival,
                    'suggested_artist': possible_artist,
                    'artist_id': artist.get('artist_id'),
                    'artist_role': artist.get('role'),
                    'artist_position': artist.get('position')
                })

    return issues

def main():
    """Main function"""

    print("\n" + "="*80)
    print("FESTIVAL DATA STRUCTURE ANALYSIS")
    print("="*80)

    init_firebase()
    issues = find_festival_issues()

    if not issues:
        print("\n✓ No festival naming issues found!")
        return

    print(f"\nFound {len(issues)} potential festival naming issues:\n")

    # Group by suggested festival
    from collections import defaultdict
    by_festival = defaultdict(list)
    for issue in issues:
        by_festival[issue['suggested_festival']].append(issue)

    print("Grouped by festival:\n")
    for festival, items in sorted(by_festival.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n  {festival}: {len(items)} concert(s)")
        for item in items:
            print(f"    Concert {item['concert_id']} ({item['date']})")
            print(f"      Current: {item['current_artist_name']}")
            print(f"      Suggested: festival_name='{item['suggested_festival']}', artist='{item['suggested_artist']}'")

    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    print("\nFor true festivals (like Sea Hear Now):")
    print("  - Set festival_name field")
    print("  - Extract actual artist name from parentheses")
    print("  - Change role to 'festival_performer'")
    print("\nFor special events/notes (like 'Billy Joel (100th)'):")
    print("  - Keep artist as 'Billy Joel'")
    print("  - Remove the note from artist_name")
    print("  - Optionally add to a notes field")

    print("\n" + "="*80)
    print("SPECIFIC CASES")
    print("="*80)

    print("\nSea Hear Now Festival:")
    sea_hear = [i for i in issues if 'Sea Hear Now' in i['suggested_festival']]
    if sea_hear:
        print(f"  Found {len(sea_hear)} concerts")
        print("  These should be:")
        for item in sea_hear:
            print(f"    Concert {item['concert_id']}: festival_name='Sea Hear Now', artist='{item['suggested_artist']}'")

    print("\nBilly Joel special shows:")
    billy = [i for i in issues if 'Billy Joel' in i['suggested_festival']]
    if billy:
        print(f"  Found {len(billy)} concerts")
        print("  These are NOT festivals - they're milestone shows")
        print("  Recommend: Keep artist='Billy Joel', add note about milestone")

    print("\n" + "="*80)
    print("\nTo fix these issues, you can:")
    print("1. Review the 'headliners_to_review.csv' file")
    print("2. For festivals, fill in artist_name_corrected with just the artist name")
    print("3. Add a note indicating it's a festival")
    print("4. I can then apply those corrections AND set the festival_name field")

if __name__ == '__main__':
    main()
