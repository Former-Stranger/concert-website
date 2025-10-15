#!/usr/bin/env python3
"""
Quick script to check Firestore for pending submissions
"""

import firebase_admin
from firebase_admin import credentials, firestore

def check_firestore():
    # Initialize Firebase
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    # Get all pending submissions
    submissions_ref = db.collection('pending_setlist_submissions')
    all_submissions = submissions_ref.get()

    print(f"\nTotal submissions in Firestore: {len(all_submissions)}")
    print("="*80)

    for doc in all_submissions:
        data = doc.to_dict()
        print(f"\nSubmission ID: {doc.id}")
        print(f"  Concert ID: {data.get('concertId')}")
        print(f"  Status: {data.get('status')}")
        print(f"  URL: {data.get('setlistfmUrl')}")
        print(f"  Submitted by: {data.get('submittedByName')} ({data.get('submittedByEmail')})")
        print(f"  Submitted at: {data.get('submittedAt')}")
        print(f"  Has setlist data: {'Yes' if data.get('setlistData') else 'No'}")

if __name__ == "__main__":
    check_firestore()
