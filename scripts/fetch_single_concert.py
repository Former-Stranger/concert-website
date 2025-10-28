#!/usr/bin/env python3
"""
Fetch setlist for a single concert by ID
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys
import os
from fetch_setlists_enhanced import (
    init_firebase,
    fetch_setlists_for_concert,
    SetlistFMClient,
    SETLISTFM_API_KEY
)


def fetch_single_concert_setlist(concert_id):
    """Fetch setlist for a single concert"""

    print("="*80)
    print(f"FETCHING SETLIST FOR CONCERT {concert_id}")
    print("="*80)

    db = init_firebase()
    client = SetlistFMClient(SETLISTFM_API_KEY)

    # Get concert data
    concert_doc = db.collection('concerts').document(concert_id).get()

    if not concert_doc.exists:
        print(f"\n❌ Concert {concert_id} not found in database")
        return

    concert_data = concert_doc.to_dict()

    # Display concert info
    headliners = [a for a in concert_data.get('artists', []) if a.get('role') == 'headliner']
    headliner_names = ', '.join([a.get('artist_name', '') for a in headliners])

    print(f"\n📅 Concert: {headliner_names}")
    print(f"   Date: {concert_data.get('date')}")
    print(f"   Venue: {concert_data.get('venue_name')}")
    print(f"   Location: {concert_data.get('city')}, {concert_data.get('state')}")
    print(f"   Headliners: {len(headliners)}")

    # Fetch setlist(s)
    print(f"\n🔍 Searching setlist.fm...")
    result = fetch_setlists_for_concert(concert_id, concert_data, client, db, dry_run=False)

    # Display result
    print("\n" + "="*80)
    if result['status'] == 'success':
        print(f"✅ SUCCESS!")
        print(f"   {result['message']}")
        print(f"   Created {result['setlists_created']} setlist document(s)")

        # Update concert's has_setlist flag
        print(f"\n📝 Updating concert {concert_id} has_setlist flag...")
        db.collection('concerts').document(concert_id).update({'has_setlist': True})
        print("   ✅ Updated")

    elif result['status'] == 'not_found':
        print(f"❌ NOT FOUND")
        print(f"   {result['message']}")
    else:
        print(f"⚠️  ERROR")
        print(f"   {result['message']}")

    print("="*80)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 fetch_single_concert.py <concert_id>")
        print("Example: python3 fetch_single_concert.py 847")
        sys.exit(1)

    concert_id = sys.argv[1]
    fetch_single_concert_setlist(concert_id)
