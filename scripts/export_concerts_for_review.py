#!/usr/bin/env python3
"""
Export all concerts to CSV for manual review and classification

Creates a CSV with:
- All current concert data
- Empty columns for updates/changes
- Suggested classifications based on current data
"""

import firebase_admin
from firebase_admin import credentials, firestore
import csv
import sys
from datetime import datetime


def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Could not use application default credentials: {e}")
            sys.exit(1)
    return firestore.client()


def suggest_event_type(concert_data):
    """
    Suggest event type based on current data

    Returns: (suggested_type, confidence, reason)
    """
    festival_name = concert_data.get('festival_name', '')
    venue_name = concert_data.get('venue_name', '')
    artists = concert_data.get('artists', [])
    headliner_count = len([a for a in artists if a.get('role') == 'headliner'])

    # Check for festival
    if 'festival' in venue_name.lower():
        return ('festival', 'high', f'Venue name contains "festival": {venue_name}')

    if festival_name and 'festival' in festival_name.lower():
        return ('festival', 'high', f'Festival name: {festival_name}')

    # Check for tour
    if festival_name and ('tour' in festival_name.lower() or 'outlaw' in festival_name.lower()):
        return ('tour', 'high', f'Tour name: {festival_name}')

    # Check for multi-artist show
    if festival_name == 'Multi-Artist Show':
        return ('multi_artist_show', 'medium', 'Currently labeled as Multi-Artist Show')

    if festival_name and any(word in festival_name.lower() for word in ['benefit', 'relief', 'tribute', 'concert for']):
        return ('multi_artist_show', 'high', f'Benefit/tribute event: {festival_name}')

    # Multiple headliners without tour/festival
    if headliner_count > 1 and not festival_name:
        return ('NEEDS_REVIEW', 'low', f'{headliner_count} headliners but no classification')

    # Single artist
    if headliner_count == 1 and not festival_name:
        return ('solo', 'high', 'Single headliner, no special event')

    # Default
    return ('NEEDS_REVIEW', 'low', 'Unable to classify automatically')


def export_concerts_csv():
    """Export all concerts to CSV for review"""

    print("=" * 80)
    print("EXPORTING CONCERTS FOR REVIEW")
    print("=" * 80)

    db = init_firebase()

    # Get all concerts
    print("\nFetching concerts from Firestore...")
    concerts_ref = db.collection('concerts').order_by('date', direction=firestore.Query.DESCENDING)
    concerts = list(concerts_ref.stream())

    print(f"Found {len(concerts)} concerts")

    # Prepare CSV data
    csv_file = 'concerts_for_review.csv'

    # Define columns
    columns = [
        # Identifiers
        'concert_id',
        'show_number',
        'date',

        # Current data
        'venue_name',
        'city',
        'state',
        'current_festival_name',
        'has_setlist',
        'attended',

        # Artist information
        'artist_count',
        'headliner_count',
        'artists_list',
        'artists_with_roles',

        # Classification suggestion
        'suggested_event_type',
        'suggestion_confidence',
        'suggestion_reason',

        # EDITABLE COLUMNS (for user input)
        'NEW_event_type',  # solo, tour, festival, multi_artist_show, other
        'NEW_event_name',  # Name of festival/benefit/special event
        'NEW_tour_name',   # Name of tour (if event_type=tour)
        'NEW_notes',       # Any notes about classification

        # Action column
        'ACTION',  # KEEP, UPDATE, DELETE, REVIEW
    ]

    print(f"\nGenerating CSV with {len(columns)} columns...")

    rows = []

    for concert_doc in concerts:
        concert_id = concert_doc.id
        data = concert_doc.to_dict()

        # Get artist information
        artists = data.get('artists', [])
        headliners = [a for a in artists if a.get('role') == 'headliner']

        # Format artist lists
        artists_list = ', '.join([a.get('artist_name', '') for a in artists])
        artists_with_roles = ' | '.join([
            f"{a.get('artist_name', '')} ({a.get('role', 'unknown')})"
            for a in artists
        ])

        # Get suggestion
        suggested_type, confidence, reason = suggest_event_type(data)

        # Create row
        row = {
            'concert_id': concert_id,
            'show_number': data.get('show_number', ''),
            'date': data.get('date', ''),
            'venue_name': data.get('venue_name', ''),
            'city': data.get('city', ''),
            'state': data.get('state', ''),
            'current_festival_name': data.get('festival_name', ''),
            'has_setlist': data.get('has_setlist', False),
            'attended': data.get('attended', True),
            'artist_count': len(artists),
            'headliner_count': len(headliners),
            'artists_list': artists_list,
            'artists_with_roles': artists_with_roles,
            'suggested_event_type': suggested_type,
            'suggestion_confidence': confidence,
            'suggestion_reason': reason,
            'NEW_event_type': '',  # Empty for user to fill
            'NEW_event_name': '',  # Empty for user to fill
            'NEW_tour_name': '',   # Empty for user to fill
            'NEW_notes': '',       # Empty for user to fill
            'ACTION': '',          # Empty for user to fill
        }

        rows.append(row)

    # Write CSV
    print(f"\nWriting to {csv_file}...")

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ CSV exported successfully!")
    print(f"  File: {csv_file}")
    print(f"  Rows: {len(rows)} concerts")
    print(f"  Columns: {len(columns)}")

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)

    suggestions = {}
    for row in rows:
        sug = row['suggested_event_type']
        suggestions[sug] = suggestions.get(sug, 0) + 1

    print("\nSuggested Classifications:")
    for event_type, count in sorted(suggestions.items(), key=lambda x: x[1], reverse=True):
        print(f"  {event_type:20} {count:4} concerts")

    needs_review = [row for row in rows if row['suggested_event_type'] == 'NEEDS_REVIEW']
    print(f"\n⚠️  {len(needs_review)} concerts need manual review")

    print("\n" + "=" * 80)
    print("INSTRUCTIONS FOR REVIEW")
    print("=" * 80)
    print("""
1. Open concerts_for_review.csv in Excel or Google Sheets
2. Review the suggested_event_type for each concert
3. Fill in the NEW_* columns with your desired values:
   - NEW_event_type: solo, tour, festival, multi_artist_show, or other
   - NEW_event_name: Name of festival/benefit/special event (if applicable)
   - NEW_tour_name: Name of tour (if event_type=tour)
   - NEW_notes: Any notes about the classification
4. Set ACTION column:
   - UPDATE: Apply the changes in NEW_* columns
   - KEEP: Keep current data as-is
   - REVIEW: Flag for further review
   - DELETE: Mark for deletion (rarely needed)
5. Save the CSV
6. Run: python3 scripts/process_concert_updates.py concerts_for_review.csv

NOTE: Leave NEW_* columns empty to keep current values.
      Only concerts with ACTION=UPDATE will be modified.
""")

    print("=" * 80)


if __name__ == '__main__':
    export_concerts_csv()
