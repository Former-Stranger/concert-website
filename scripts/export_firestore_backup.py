#!/usr/bin/env python3
"""
Export complete Firestore database to JSON files for backup
"""

import sys
import json
import os
from google.cloud import firestore

def export_collection(db, collection_name, output_dir):
    """Export a Firestore collection to JSON"""
    print(f"  Exporting {collection_name}...", end=" ", flush=True)

    collection_ref = db.collection(collection_name)
    docs = collection_ref.stream()

    docs_data = []
    count = 0
    for doc in docs:
        doc_dict = doc.to_dict()
        doc_dict['_id'] = doc.id  # Include document ID
        docs_data.append(doc_dict)
        count += 1

    output_file = os.path.join(output_dir, f"{collection_name}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(docs_data, f, indent=2, default=str)

    print(f"✓ ({count} documents)")
    return count

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 export_firestore_backup.py <output_directory>")
        sys.exit(1)

    output_dir = sys.argv[1]
    os.makedirs(output_dir, exist_ok=True)

    # Initialize Firestore
    db = firestore.Client()

    # Collections to backup
    collections = [
        'concerts',
        'artists',
        'venues',
        'songs',
        'setlists',
        'pending_setlist_submissions',
        'concert_photos',
        'users'
    ]

    total_docs = 0
    for collection in collections:
        try:
            count = export_collection(db, collection, output_dir)
            total_docs += count
        except Exception as e:
            print(f"✗ Error: {e}")

    print(f"\n  Total: {total_docs} documents exported to {output_dir}")

if __name__ == '__main__':
    main()
