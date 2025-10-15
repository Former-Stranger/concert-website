#!/usr/bin/env python3
"""Trigger processing of an approved but unprocessed submission"""

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

# Get the submission for concert 1275
submissions_ref = db.collection('pending_setlist_submissions')
query = submissions_ref.where('concertId', '==', 1275).where('status', '==', 'approved')

print(f"Looking for approved submission for concert 1275...\n")

submissions = list(query.stream())

if not submissions:
    print("No approved submissions found for concert 1275")
    sys.exit(1)

for doc in submissions:
    data = doc.to_dict()
    print(f"Found submission ID: {doc.id}")
    print(f"Status: {data.get('status')}")
    print(f"Processed: {data.get('processed', False)}")

    if data.get('processed'):
        print("Already processed, skipping")
        continue

    # Trigger reprocessing by updating a dummy field
    # This will cause the onWrite trigger to fire
    print(f"\nTriggering reprocessing...")
    doc.reference.update({
        'trigger_reprocess': firestore.SERVER_TIMESTAMP
    })
    print(f"✓ Updated submission to trigger processing")
    print(f"Check logs: firebase functions:log --project earplugs-and-memories")
