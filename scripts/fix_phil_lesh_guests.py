#!/usr/bin/env python3
"""
Remove guest artists from Phil Lesh & Friends concerts.
Bobby and Q) were guests, not separate acts.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os

if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'earplugs-and-memories'),
    })

db = firestore.client()

def fix_concerts():
    """Remove Bobby and Q) from Phil Lesh & Friends concerts - they were guests."""
    
    print("\n🔧 Fixing Phil Lesh & Friends Guest Artists")
    print("=" * 60)
    
    # Specific concerts to fix
    concerts_to_fix = ['816', '817', '1034', '994']
    
    for concert_id in concerts_to_fix:
        doc = db.collection('concerts').document(concert_id).get()
        if doc.exists:
            concert_data = doc.to_dict()
            artists = concert_data.get('artists', [])
            
            # Keep only Phil Lesh & Friends
            new_artists = [a for a in artists if a.get('artist_name') == 'Phil Lesh & Friends']
            
            if len(new_artists) != len(artists):
                removed = [a.get('artist_name') for a in artists if a not in new_artists]
                print(f"Concert {concert_id} ({concert_data.get('date')}):")
                print(f"  Removed: {', '.join(removed)}")
                print(f"  Note: These were guest musicians, not separate acts")
                
                doc.reference.update({'artists': new_artists})
    
    print("\n✅ Updated 4 concerts")
    print("=" * 60)

if __name__ == '__main__':
    fix_concerts()
    print("\nNext steps:")
    print("  1. Run: python3 scripts/export_to_web.py")
    print("  2. Deploy: firebase deploy --only hosting")
