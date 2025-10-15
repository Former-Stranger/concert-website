#!/usr/bin/env python3
"""Check status of a concert's setlist submission"""

import sys
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'earplugs-and-memories'
    })

db = firestore.client()

concert_id = '1275'

# Check for submissions
submissions_ref = db.collection('pending_setlist_submissions')
query = submissions_ref.where('concertId', '==', int(concert_id))

print(f"Checking submissions for concert {concert_id}...\n")

submissions = list(query.stream())

if not submissions:
    print(f"No submissions found for concert {concert_id}")
else:
    for doc in submissions:
        data = doc.to_dict()
        print(f"Submission ID: {doc.id}")
        print(f"Status: {data.get('status')}")
        print(f"Submitted by: {data.get('submittedByEmail')}")
        print(f"Submitted at: {data.get('submittedAt')}")
        print(f"Processed: {data.get('processed', False)}")
        print(f"Processed at: {data.get('processed_at', 'N/A')}")
        if data.get('import_error'):
            print(f"Import error: {data.get('import_error')}")
        print()

# Check if setlist exists
print(f"\nChecking if setlist exists for concert {concert_id}...")
setlists_ref = db.collection('setlists')
query = setlists_ref.where('concert_id', '==', concert_id)

setlists = list(query.stream())
if setlists:
    print(f"✓ Setlist exists! ({len(setlists[0].to_dict().get('songs', []))} songs)")
else:
    print(f"✗ No setlist found")
