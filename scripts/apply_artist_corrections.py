#!/usr/bin/env python3
"""
Apply artist name corrections from the review CSV back to Firestore and re-export.

Usage: python3 scripts/apply_artist_corrections.py website/data/headliners_to_review.csv
"""

import firebase_admin
from firebase_admin import credentials, firestore
import csv
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
            print("\nTo fix this, run:")
            print("  gcloud auth application-default login")
            sys.exit(1)

def apply_corrections(csv_file):
    """Apply artist name corrections from CSV to Firestore"""

    if not os.path.exists(csv_file):
        print(f"Error: File not found: {csv_file}")
        sys.exit(1)

    print("\n" + "="*80)
    print("APPLYING ARTIST NAME CORRECTIONS")
    print("="*80)

    # Read corrections from CSV
    corrections = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only process rows where user filled in a correction
            corrected_name = row.get('artist_name_corrected', '').strip()
            if corrected_name and corrected_name != row['artist_name']:
                corrections.append({
                    'concert_id': row['concert_id'],
                    'artist_id': row['artist_id'],
                    'old_name': row['artist_name'],
                    'new_name': corrected_name,
                    'artist_position': row.get('artist_position', '1'),
                    'notes': row.get('notes', '')
                })

    if not corrections:
        print("\n⚠ No corrections found in CSV!")
        print("   Make sure to fill in the 'artist_name_corrected' column")
        print("   for the artists you want to update.")
        return

    print(f"\nFound {len(corrections)} corrections to apply:\n")
    for i, corr in enumerate(corrections[:10], 1):
        print(f"{i}. Concert {corr['concert_id']}")
        print(f"   Old: {corr['old_name']}")
        print(f"   New: {corr['new_name']}")
        if corr['notes']:
            print(f"   Note: {corr['notes']}")
        print()

    if len(corrections) > 10:
        print(f"   ... and {len(corrections) - 10} more corrections")

    response = input("\nApply these corrections to Firestore? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return

    # Initialize Firestore
    init_firebase()
    db = firestore.client()

    # Apply corrections
    print("\nApplying corrections...")
    updated_count = 0
    errors = []

    for corr in corrections:
        try:
            concert_ref = db.collection('concerts').document(corr['concert_id'])
            concert_doc = concert_ref.get()

            if not concert_doc.exists:
                errors.append(f"Concert {corr['concert_id']} not found")
                continue

            concert_data = concert_doc.to_dict()
            artists = concert_data.get('artists', [])

            # Find and update the specific artist
            updated = False
            for artist in artists:
                # Match by artist_id if available, otherwise by name
                if (corr['artist_id'] and artist.get('artist_id') == corr['artist_id']) or \
                   (artist.get('artist_name') == corr['old_name']):
                    artist['artist_name'] = corr['new_name']
                    updated = True
                    break

            if updated:
                # Update the concert document
                concert_ref.update({'artists': artists})
                updated_count += 1
                print(f"  ✓ Updated concert {corr['concert_id']}: {corr['old_name']} → {corr['new_name']}")
            else:
                errors.append(f"Concert {corr['concert_id']}: Artist '{corr['old_name']}' not found")

        except Exception as e:
            errors.append(f"Concert {corr['concert_id']}: {str(e)}")

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✓ Successfully updated: {updated_count} artists")

    if errors:
        print(f"\n⚠ Errors ({len(errors)}):")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")

    if updated_count > 0:
        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)
        print("Run the following to update the website:")
        print("  1. python3 scripts/export_to_web.py")
        print("  2. firebase deploy --only hosting")
        print("     OR: ./deploy.sh")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/apply_artist_corrections.py <csv_file>")
        print("Example: python3 scripts/apply_artist_corrections.py website/data/headliners_to_review.csv")
        sys.exit(1)

    csv_file = sys.argv[1]
    apply_corrections(csv_file)
