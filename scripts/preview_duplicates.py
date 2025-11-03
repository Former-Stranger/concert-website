#!/usr/bin/env python3
"""
Preview all duplicate artists with their concerts before merging
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys
from collections import defaultdict


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
            sys.exit(1)
    return firestore.client()


def normalize_artist_name(name):
    """Normalize artist name for comparison"""
    normalized = name.lower()
    normalized = ''.join(c if c.isalnum() or c.isspace() else '' for c in normalized)
    normalized = ' '.join(normalized.split())
    for article in ['the ', 'a ', 'an ']:
        if normalized.startswith(article):
            normalized = normalized[len(article):]
            break
    return normalized.strip()


def get_concerts_for_artist(db, artist_id, all_concerts):
    """Get all concerts for an artist"""
    concerts = []
    for concert_id, concert_data in all_concerts.items():
        for artist in concert_data.get('artists', []):
            if artist.get('artist_id') == artist_id:
                concerts.append({
                    'id': concert_id,
                    'show_number': concert_data.get('show_number'),
                    'date': concert_data.get('date', ''),
                    'venue': concert_data.get('venue_name', ''),
                    'role': artist.get('role', 'headliner')
                })
                break
    return sorted(concerts, key=lambda x: x['date'])


def find_duplicates_with_details(db):
    """Find duplicates and get all concert details"""
    print("Loading data...")

    # Load all artists
    artists_ref = db.collection('artists')
    artists_docs = list(artists_ref.stream())

    # Load all concerts
    concerts_ref = db.collection('concerts')
    all_concerts = {}
    for concert_doc in concerts_ref.stream():
        all_concerts[concert_doc.id] = concert_doc.to_dict()

    print(f"Loaded {len(artists_docs)} artists and {len(all_concerts)} concerts\n")

    # Group artists by normalized name
    normalized_groups = defaultdict(list)

    for doc in artists_docs:
        data = doc.to_dict()
        canonical_name = data.get('canonical_name', '')
        if canonical_name:
            normalized = normalize_artist_name(canonical_name)
            normalized_groups[normalized].append({
                'id': doc.id,
                'name': canonical_name,
                'created_at': data.get('created_at')
            })

    # Find duplicates and get their concerts
    duplicates = []
    for normalized, artists in normalized_groups.items():
        if len(artists) > 1:
            # Sort by creation date (oldest first)
            artists.sort(key=lambda x: x.get('created_at') or 0)

            # Get concerts for each artist
            for artist in artists:
                concerts = get_concerts_for_artist(db, artist['id'], all_concerts)
                artist['concerts'] = concerts
                artist['concert_count'] = len(concerts)

            duplicates.append({
                'normalized': normalized,
                'artists': artists,
                'total_concerts': sum(a['concert_count'] for a in artists)
            })

    # Sort by total concerts (most impactful first)
    duplicates.sort(key=lambda x: x['total_concerts'], reverse=True)

    return duplicates


def preview_all_duplicates(db):
    """Show detailed preview of all duplicates"""
    duplicates = find_duplicates_with_details(db)

    if not duplicates:
        print("✅ No duplicates found!")
        return []

    print(f"{'='*80}")
    print(f"DUPLICATE ARTISTS PREVIEW")
    print(f"Found {len(duplicates)} groups affecting {sum(d['total_concerts'] for d in duplicates)} total concerts")
    print(f"{'='*80}\n")

    merge_plan = []

    for i, dup in enumerate(duplicates, 1):
        normalized = dup['normalized']
        artists = dup['artists']
        total = dup['total_concerts']

        print(f"\n{'='*80}")
        print(f"GROUP {i}: '{normalized}' ({total} total concerts)")
        print(f"{'='*80}\n")

        # Recommend which to keep (most concerts, or oldest if tie)
        artists_sorted = sorted(artists, key=lambda x: (-x['concert_count'], x.get('created_at') or 0))
        keep_artist = artists_sorted[0]

        print(f"RECOMMENDATION: Keep '{keep_artist['name']}' (ID: {keep_artist['id'][:12]}...)")
        print(f"               Has {keep_artist['concert_count']} concerts, created first\n")

        for j, artist in enumerate(artists, 1):
            is_keep = artist['id'] == keep_artist['id']
            prefix = "✓ KEEP:  " if is_keep else "  MERGE: "

            print(f"{prefix}'{artist['name']}'")
            print(f"         ID: {artist['id']}")
            print(f"         Concerts: {artist['concert_count']}")

            if artist['concerts']:
                print(f"         Shows:")
                for concert in artist['concerts']:
                    role_str = f" ({concert['role']})" if concert['role'] != 'headliner' else ""
                    print(f"           - {concert['date']}: {concert['venue']}{role_str}")
            else:
                print(f"         Shows: (none - can be safely deleted)")

            print()

            if not is_keep:
                merge_plan.append({
                    'group': i,
                    'normalized': normalized,
                    'keep_id': keep_artist['id'],
                    'keep_name': keep_artist['name'],
                    'merge_id': artist['id'],
                    'merge_name': artist['name'],
                    'concert_count': artist['concert_count']
                })

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total duplicate groups: {len(duplicates)}")
    print(f"Total artists to merge: {len(merge_plan)}")
    print(f"Total concerts affected: {sum(m['concert_count'] for m in merge_plan)}")
    print(f"{'='*80}\n")

    return merge_plan


if __name__ == '__main__':
    db = init_firebase()
    merge_plan = preview_all_duplicates(db)

    if merge_plan:
        print("\nSave this merge plan? It will be used for automated merging.")
        print("The plan shows which artists to keep and which to merge.")
        print("\nTo execute the merges, run:")
        print("  python3 scripts/execute_merge_plan.py merge_plan.json")

        save = input("\nSave merge plan? (yes/no): ").strip().lower()
        if save == 'yes':
            import json
            with open('merge_plan.json', 'w') as f:
                json.dump(merge_plan, f, indent=2)
            print("\n✅ Merge plan saved to merge_plan.json")
