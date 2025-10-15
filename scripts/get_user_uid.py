#!/usr/bin/env python3
"""Get the UID of a user by email"""

import sys
import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'earplugs-and-memories'
    })

# Get the owner's email
email = input("Enter the owner's email address: ")

try:
    user = auth.get_user_by_email(email)
    print(f"\nUser found!")
    print(f"Email: {user.email}")
    print(f"Display Name: {user.display_name}")
    print(f"UID: {user.uid}")
    print(f"\nCopy this UID and update OWNER_UID in website/js/auth.js")
except Exception as e:
    print(f"Error: {e}")
