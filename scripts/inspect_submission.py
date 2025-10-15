#!/usr/bin/env python3
"""Inspect a submission in detail"""

import sys
import firebase_admin
from firebase_admin import credentials, firestore
import json

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'earplugs-and-memories'
    })

db = firestore.client()

submission_id = 'YU7XDtlluHY0OFtKugyq'

doc = db.collection('pending_setlist_submissions').document(submission_id).get()
if doc.exists:
    data = doc.to_dict()
    print(json.dumps(data, indent=2, default=str))
else:
    print("Submission not found")
