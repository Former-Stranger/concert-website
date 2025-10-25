#!/usr/bin/env python3
"""
Clean up old admin documents (email-based IDs) from the previous setup.
Only keep UID-based admin documents.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'earplugs-and-memories'),
    })

db = firestore.client()

def cleanup_old_admins():
    """Remove old email-based admin documents."""
    print("🧹 Cleaning up old admin documents...")

    admins_ref = db.collection('admins')
    docs = admins_ref.stream()

    deleted_count = 0
    for doc in docs:
        doc_id = doc.id
        data = doc.to_dict()

        # Delete documents that have email-based IDs (contain '_at_' or '_dot_')
        # or have 'pending' as UID (from old setup)
        if '_at_' in doc_id or '_dot_' in doc_id or data.get('uid') == 'pending':
            print(f"  Deleting old document: {doc_id} ({data.get('email')})")
            doc.reference.delete()
            deleted_count += 1

    print(f"✅ Cleaned up {deleted_count} old document(s)")

    # Show remaining admins
    print("\n📋 Active Admins (after cleanup):")
    print("-" * 60)
    docs = admins_ref.stream()
    count = 0
    for doc in docs:
        data = doc.to_dict()
        count += 1
        print(f"{count}. {data.get('email')} - UID: {data.get('uid')}")

    print("-" * 60)

if __name__ == '__main__':
    cleanup_old_admins()
