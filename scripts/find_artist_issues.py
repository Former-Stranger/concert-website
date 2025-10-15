#!/usr/bin/env python3
"""Find artist name issues in concerts collection"""

import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from collections import defaultdict

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'earplugs-and-memories'
    })

db = firestore.client()

def find_similar_artists():
    """Find artist names that might be duplicates"""
    print("Analyzing artist names in concerts...")

    concerts_ref = db.collection('concerts')
    all_concerts = concerts_ref.stream()

    # Collect all artist names as they appear in concerts
    artist_name_variants = defaultdict(set)  # normalized -> original names

    for doc in all_concerts:
        concert = doc.to_dict()
        for artist in concert.get('artists', []):
            name = artist.get('artist_name', '')
            if name:
                # Normalize by lowercasing and removing "the"
                normalized = name.lower().replace('the ', '').strip()
                artist_name_variants[normalized].add(name)

    # Find potential duplicates
    print("\nPotential duplicate artists:\n")

    found_issues = False
    for normalized, variants in sorted(artist_name_variants.items()):
        if len(variants) > 1:
            found_issues = True
            print(f"  Normalized: '{normalized}'")
            for v in sorted(variants):
                print(f"    - '{v}'")
            print()

    if not found_issues:
        print("  No obvious duplicates found!")

    # Also search for specific ones mentioned by user
    print("\n" + "=" * 60)
    print("Searching for specific artists mentioned:\n")

    for search_term in ["wallflower", "mumford"]:
        print(f"  Artist names containing '{search_term}':")
        found = False
        for normalized, variants in artist_name_variants.items():
            if search_term in normalized:
                found = True
                for v in sorted(variants):
                    print(f"    - '{v}'")
        if not found:
            print(f"    (none found)")
        print()

if __name__ == '__main__':
    find_similar_artists()
