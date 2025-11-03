#!/usr/bin/env python3
"""
Interactive Firestore query tool
Browse and edit Firestore data from the command line
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json
import sys
from datetime import datetime

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Could not use application default credentials: {e}")
            print("\nTo fix this, run:")
            print("  gcloud auth application-default login")
            sys.exit(1)
    return firestore.client()


def list_collections(db):
    """List all top-level collections"""
    print("\n=== Firestore Collections ===")
    collections = list(db.collections())
    for collection in collections:
        # Get actual document count (no limit)
        count = len(list(collection.stream()))
        print(f"  • {collection.id} ({count} documents)")
    print("\nUse commands 2-6 to query specific collections.")


def query_concerts(db, search_term=None):
    """Query concerts with optional search"""
    concerts_ref = db.collection('concerts')

    if search_term:
        # Search by artist name (case-insensitive substring match)
        concerts = concerts_ref.stream()
        results = []
        search_lower = search_term.lower()

        for doc in concerts:
            data = doc.to_dict()
            artists = data.get('artists', [])
            artist_names = [a.get('artist_name', '').lower() for a in artists]

            if any(search_lower in name for name in artist_names):
                results.append({
                    'id': doc.id,
                    'show_number': data.get('show_number'),
                    'date': data.get('date'),
                    'artists': ', '.join([a.get('artist_name') for a in artists]),
                    'venue': data.get('venue_name')
                })

        print(f"\n=== Found {len(results)} concerts matching '{search_term}' ===")
        for concert in sorted(results, key=lambda x: x['date'], reverse=True)[:20]:
            #print(f"Concert {concert['id']} (#{concert['show_number']}): {concert['artists']} @ {concert['venue']} - {concert['date']}")
            print(f"Concert {concert['id']} {concert['artists']} @ {concert['venue']} - {concert['date']}")
    else:
        # Just show recent concerts
        concerts = concerts_ref.order_by('date', direction=firestore.Query.DESCENDING).limit(20).stream()
        print("\n=== Recent Concerts (Last 20) ===")
        for doc in concerts:
            data = doc.to_dict()
            artists = ', '.join([a.get('artist_name') for a in data.get('artists', [])])
            print(f"Concert {doc.id} (#{data.get('show_number')}): {artists} @ {data.get('venue_name')} - {data.get('date')}")


def query_artists(db, search_term=None):
    """Query artists with optional search"""
    artists_ref = db.collection('artists')

    if search_term:
        artists = artists_ref.stream()
        results = []
        search_lower = search_term.lower()

        for doc in artists:
            data = doc.to_dict()
            name = data.get('canonical_name', '')
            if search_lower in name.lower():
                results.append({
                    'id': doc.id,
                    'name': name,
                    'aliases': data.get('aliases', [])
                })

        print(f"\n=== Found {len(results)} artists matching '{search_term}' ===")
        for artist in sorted(results, key=lambda x: x['name']):
            aliases = f" (aliases: {', '.join(artist['aliases'])})" if artist['aliases'] else ""
            print(f"{artist['id']}: {artist['name']}{aliases}")
    else:
        artists = artists_ref.order_by('canonical_name').limit(50).stream()
        print("\n=== Artists (First 50, alphabetical) ===")
        for doc in artists:
            data = doc.to_dict()
            print(f"{doc.id}: {data.get('canonical_name')}")


def get_concert(db, concert_id):
    """Get detailed concert info"""
    doc = db.collection('concerts').document(concert_id).get()

    if not doc.exists:
        print(f"Concert {concert_id} not found!")
        return

    data = doc.to_dict()
    print(f"\n=== Concert {concert_id} (#{data.get('show_number')}) ===")
    print(f"Date: {data.get('date')}")
    print(f"Venue: {data.get('venue_name')} ({data.get('city')}, {data.get('state')})")
    print(f"Artists:")
    for artist in data.get('artists', []):
        print(f"  - {artist.get('artist_name')} ({artist.get('role')}, position {artist.get('position')})")
    print(f"Has Setlist: {data.get('has_setlist', False)}")
    print(f"Setlist Status: {data.get('setlist_status', 'not_researched')}")

    if data.get('festival_name'):
        print(f"Festival: {data.get('festival_name')}")
    if data.get('tour_name'):
        print(f"Tour: {data.get('tour_name')}")

    # Get setlists
    setlists = db.collection('setlists').where('concert_id', '==', concert_id).stream()
    setlist_list = list(setlists)

    if setlist_list:
        print(f"\nSetlists ({len(setlist_list)}):")
        for setlist_doc in setlist_list:
            setlist_data = setlist_doc.to_dict()
            print(f"  - {setlist_data.get('artist_name')}: {setlist_data.get('song_count', 0)} songs")


def get_artist(db, artist_id):
    """Get detailed artist info"""
    doc = db.collection('artists').document(artist_id).get()

    if not doc.exists:
        print(f"Artist {artist_id} not found!")
        return

    data = doc.to_dict()
    print(f"\n=== Artist {artist_id} ===")
    print(f"Name: {data.get('canonical_name')}")
    if data.get('aliases'):
        print(f"Aliases: {', '.join(data.get('aliases'))}")
    print(f"Created: {data.get('created_at')}")

    # Count concerts
    concerts = db.collection('concerts').stream()
    concert_count = 0
    concert_list = []

    for concert_doc in concerts:
        concert_data = concert_doc.to_dict()
        for artist in concert_data.get('artists', []):
            if artist.get('artist_id') == artist_id:
                concert_count += 1
                concert_list.append({
                    'id': concert_doc.id,
                    'date': concert_data.get('date'),
                    'venue': concert_data.get('venue_name'),
                    'role': artist.get('role')
                })
                break

    print(f"\nConcerts: {concert_count}")
    if concert_list:
        print("\nRecent appearances:")
        for concert in sorted(concert_list, key=lambda x: x['date'], reverse=True)[:10]:
            print(f"  {concert['date']}: {concert['venue']} ({concert['role']})")


def update_artist_name(db, artist_id, new_name):
    """Update artist canonical name"""
    doc_ref = db.collection('artists').document(artist_id)
    doc = doc_ref.get()

    if not doc.exists:
        print(f"Artist {artist_id} not found!")
        return

    old_name = doc.to_dict().get('canonical_name')

    print(f"\n⚠️  About to update artist name:")
    print(f"   ID: {artist_id}")
    print(f"   Old: {old_name}")
    print(f"   New: {new_name}")

    confirm = input("\nAre you sure? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return

    doc_ref.update({
        'canonical_name': new_name
    })

    print(f"\n✅ Updated artist {artist_id}")
    print(f"\n⚠️  Note: This does NOT update concerts automatically!")
    print("   Concerts will still show the old artist name until:")
    print("   1. A Cloud Function cascade is implemented, OR")
    print("   2. Setlists are re-imported for affected concerts")


def interactive_mode(db):
    """Interactive query interface"""
    print("\n" + "="*60)
    print("   FIRESTORE INTERACTIVE QUERY TOOL")
    print("="*60)

    while True:
        print("\nCommands:")
        print("  1. List collections")
        print("  2. Search concerts")
        print("  3. Search artists")
        print("  4. Get concert by ID")
        print("  5. Get artist by ID")
        print("  6. Update artist name")
        print("  q. Quit")

        choice = input("\nEnter command: ").strip()

        if choice == 'q':
            break
        elif choice == '1':
            list_collections(db)
        elif choice == '2':
            search = input("Search artist name (or press Enter for recent): ").strip()
            query_concerts(db, search if search else None)
        elif choice == '3':
            search = input("Search artist name (or press Enter for first 50): ").strip()
            query_artists(db, search if search else None)
        elif choice == '4':
            concert_id = input("Enter concert ID: ").strip()
            get_concert(db, concert_id)
        elif choice == '5':
            artist_id = input("Enter artist ID: ").strip()
            get_artist(db, artist_id)
        elif choice == '6':
            artist_id = input("Enter artist ID: ").strip()
            new_name = input("Enter new name: ").strip()
            update_artist_name(db, artist_id, new_name)
        else:
            print("Invalid command!")


if __name__ == '__main__':
    db = init_firebase()

    if len(sys.argv) > 1:
        # Command line mode
        command = sys.argv[1]

        if command == 'concerts':
            search = sys.argv[2] if len(sys.argv) > 2 else None
            query_concerts(db, search)
        elif command == 'artists':
            search = sys.argv[2] if len(sys.argv) > 2 else None
            query_artists(db, search)
        elif command == 'concert':
            if len(sys.argv) < 3:
                print("Usage: query_firestore.py concert <id>")
            else:
                get_concert(db, sys.argv[2])
        elif command == 'artist':
            if len(sys.argv) < 3:
                print("Usage: query_firestore.py artist <id>")
            else:
                get_artist(db, sys.argv[2])
        else:
            print(f"Unknown command: {command}")
            print("Usage: query_firestore.py [concerts|artists|concert|artist] [args]")
    else:
        # Interactive mode
        interactive_mode(db)
