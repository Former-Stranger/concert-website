#!/usr/bin/env python3
"""
Setup admin users in Firestore.

This script creates an 'admins' collection and adds admin users.
Each admin document is keyed by their Firebase Auth email.
"""

import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth
import os

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    # Use Application Default Credentials from environment
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'earplugs-and-memories'),
    })

db = firestore.client()

def get_user_uid_by_email(email):
    """Get Firebase Auth UID for a user by email."""
    try:
        user = firebase_auth.get_user_by_email(email)
        return user.uid
    except firebase_auth.UserNotFoundError:
        return None
    except Exception as e:
        print(f"Error getting user for {email}: {e}")
        return None

def add_admin(email, role="owner", notes=""):
    """Add an admin user to the admins collection."""
    uid = get_user_uid_by_email(email)

    if not uid:
        print(f"⚠️  Warning: User {email} not found in Firebase Auth.")
        print(f"   They will be added to pending admins list.")
        print(f"   Run this script again after they sign up to activate their admin access.")
        print()

        # Store in pending_admins collection
        pending_data = {
            'email': email,
            'role': role,
            'notes': notes,
            'added_at': firestore.SERVER_TIMESTAMP,
            'status': 'pending_signup'
        }
        doc_id = email.replace('@', '_at_').replace('.', '_dot_')
        db.collection('pending_admins').document(doc_id).set(pending_data)
        print(f"✅ Added to pending admins: {email}")
        return None

    admin_data = {
        'email': email,
        'uid': uid,
        'role': role,
        'added_at': firestore.SERVER_TIMESTAMP,
        'notes': notes
    }

    # Store with UID as document ID (required for security rules)
    db.collection('admins').document(uid).set(admin_data)
    print(f"✅ Added admin: {email} (UID: {uid})")

    return uid

def list_admins():
    """List all current admins."""
    print("\n📋 Active Admins:")
    print("-" * 60)

    admins_ref = db.collection('admins')
    docs = admins_ref.stream()

    count = 0
    for doc in docs:
        data = doc.to_dict()
        count += 1
        print(f"{count}. {data.get('email')} - ✓ Active")
        print(f"   UID: {data.get('uid')}")
        if data.get('notes'):
            print(f"   Notes: {data.get('notes')}")

    if count == 0:
        print("No active admins found.")
    print("-" * 60)

    # List pending admins
    print("\n⏳ Pending Admins:")
    print("-" * 60)

    pending_ref = db.collection('pending_admins')
    pending_docs = pending_ref.stream()

    pending_count = 0
    for doc in pending_docs:
        data = doc.to_dict()
        pending_count += 1
        print(f"{pending_count}. {data.get('email')} - Waiting for signup")
        if data.get('notes'):
            print(f"   Notes: {data.get('notes')}")

    if pending_count == 0:
        print("No pending admins.")
    print("-" * 60)

def setup_initial_admins():
    """Set up the initial admin users."""
    print("\n🔧 Setting up admin users for Earplugs & Memories")
    print("=" * 60)

    # Add the primary owner
    add_admin(
        email='akalbfell@gmail.com',
        role='owner',
        notes='Primary owner - site creator'
    )

    # Add the second admin
    add_admin(
        email='jlbisogni@gmail.com',
        role='owner',
        notes='Co-admin - full access'
    )

    print("\n✨ Admin setup complete!")

    # List all admins
    list_admins()

if __name__ == '__main__':
    setup_initial_admins()
