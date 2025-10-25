#!/usr/bin/env python3
"""
Remove duplicate "Friends" artists from Phil Lesh & Friends concerts.
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

def fix_phil_lesh_concerts():
    """Remove 'Friends' artists from Phil Lesh & Friends concerts."""
    
    print("\n🔧 Fixing Phil Lesh & Friends Concerts")
    print("=" * 60)
    
    concerts_ref = db.collection('concerts')
    updated_count = 0
    
    for doc in concerts_ref.stream():
        concert_data = doc.to_dict()
        artists = concert_data.get('artists', [])
        
        # Check if this concert has both "Phil Lesh & Friends" and "Friends"
        has_phil_lesh = any(a.get('artist_name') == 'Phil Lesh & Friends' for a in artists)
        has_friends = any('Friends' in a.get('artist_name', '') and a.get('artist_name') != 'Phil Lesh & Friends' for a in artists)
        
        if has_phil_lesh and has_friends:
            # Remove any artist that contains "Friends" but is not "Phil Lesh & Friends"
            new_artists = [
                a for a in artists 
                if a.get('artist_name') == 'Phil Lesh & Friends' or 'Friends' not in a.get('artist_name', '')
            ]
            
            if len(new_artists) != len(artists):
                removed = [a.get('artist_name') for a in artists if a not in new_artists]
                print(f"  Concert {doc.id} ({concert_data.get('date')})")
                print(f"    Removed: {', '.join(removed)}")
                print(f"    Kept: {', '.join([a.get('artist_name') for a in new_artists])}")
                
                doc.reference.update({'artists': new_artists})
                updated_count += 1
    
    print(f"\n✅ Updated {updated_count} concerts")
    print("=" * 60)
    
    return updated_count

if __name__ == '__main__':
    count = fix_phil_lesh_concerts()
    if count > 0:
        print("\nNext steps:")
        print("  1. Run: python3 scripts/export_to_web.py")
        print("  2. Deploy: firebase deploy --only hosting")
