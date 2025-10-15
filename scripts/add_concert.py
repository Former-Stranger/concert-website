#!/usr/bin/env python3
"""
Add a new concert directly to Firestore

Usage:
  python3 scripts/add_concert.py

This will prompt you for concert details and add it to Firestore.
After adding, run ./deploy.sh to update the website.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys
from datetime import datetime

def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {'projectId': 'earplugs-and-memories'})
    return firestore.client()

def get_next_concert_id(db):
    """Get the next available concert ID"""
    # Query for the highest ID
    concerts = db.collection('concerts').order_by('concert_id', direction=firestore.Query.DESCENDING).limit(1).stream()

    for concert in concerts:
        return concert.to_dict().get('concert_id', 0) + 1

    return 1  # If no concerts exist

def add_concert():
    db = init_firebase()

    print("=" * 60)
    print("ADD NEW CONCERT TO FIRESTORE")
    print("=" * 60)
    print()

    # Get concert details
    date_str = input("Date (YYYY-MM-DD): ").strip()
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)

    artist_name = input("Artist name: ").strip()
    if not artist_name:
        print("Artist name is required")
        sys.exit(1)

    support_act = input("Support act (optional, press enter to skip): ").strip() or None
    festival_name = input("Festival name (optional, press enter to skip): ").strip() or None

    venue_name = input("Venue name: ").strip()
    if not venue_name:
        print("Venue name is required")
        sys.exit(1)

    city = input("City: ").strip()
    if not city:
        print("City is required")
        sys.exit(1)

    state = input("State/Province: ").strip()
    if not state:
        print("State is required")
        sys.exit(1)

    # Get next ID
    concert_id = get_next_concert_id(db)

    print()
    print("=" * 60)
    print("CONCERT SUMMARY")
    print("=" * 60)
    print(f"Concert ID: {concert_id}")
    print(f"Date: {date_str}")
    print(f"Artist: {artist_name}")
    if support_act:
        print(f"Support: {support_act}")
    if festival_name:
        print(f"Festival: {festival_name}")
    print(f"Venue: {venue_name}")
    print(f"Location: {city}, {state}")
    print("=" * 60)
    print()

    confirm = input("Add this concert? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("Cancelled.")
        sys.exit(0)

    # Create concert document
    concert_data = {
        'concert_id': concert_id,
        'date': date_str,
        'artist_name': artist_name,
        'support_act': support_act,
        'festival_name': festival_name,
        'venue_name': venue_name,
        'city': city,
        'state': state,
        'has_setlist': False,
        'created_at': firestore.SERVER_TIMESTAMP
    }

    # Add to Firestore using concert_id as document ID
    db.collection('concerts').document(str(concert_id)).set(concert_data)

    print()
    print(f"✓ Concert added successfully! Concert ID: {concert_id}")
    print()
    print("Next steps:")
    print(f"  1. To add a setlist, go to: https://earplugs-and-memories.web.app/concert.html?id={concert_id}")
    print(f"  2. Click 'Submit Setlist' and paste the setlist.fm URL")
    print(f"  3. The setlist will be automatically imported and deployed")
    print()
    print("OR run ./deploy.sh now to make the concert visible on the website")

if __name__ == '__main__':
    try:
        add_concert()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
