#!/usr/bin/env python3
"""Force reprocessing by toggling status"""

import sys
import time
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'earplugs-and-memories'
    })

db = firestore.client()

submission_id = 'YU7XDtlluHY0OFtKugyq'

doc_ref = db.collection('pending_setlist_submissions').document(submission_id)

print(f"Forcing reprocessing of submission {submission_id}...")

# First, set status to 'pending'
print("Step 1: Setting status to 'pending'")
doc_ref.update({
    'status': 'pending'
})

# Wait a moment
time.sleep(2)

# Then set it back to 'approved' to trigger the function
print("Step 2: Setting status back to 'approved'")
doc_ref.update({
    'status': 'approved',
    'reviewedAt': firestore.SERVER_TIMESTAMP,
    'reviewedBy': 'system-reprocess'
})

print("\n✓ Status toggled to trigger processApprovedSetlist function")
print("Wait a few seconds, then check:")
print("  python3 scripts/check_submission.py")
