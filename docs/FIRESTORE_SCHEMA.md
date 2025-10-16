# Firestore Schema

## Collections

### `artists`
```
{
  id: auto-generated
  canonical_name: string
  aliases: array of strings (optional)
  created_at: timestamp
}
```

### `venues`
```
{
  id: auto-generated
  canonical_name: string
  short_name: string (optional)
  city: string
  state: string
  venue_type: string (optional)
  created_at: timestamp
}
```

### `concerts`
```
{
  id: auto-generated (or imported from SQLite ID)
  show_number: number (optional)
  date: string (YYYY-MM-DD format)
  date_unknown: boolean
  venue_id: string (reference to venues collection)
  venue_name: string (denormalized for easy display)
  city: string (denormalized)
  state: string (denormalized)
  festival_name: string (optional)
  artists: array of {
    artist_id: string
    artist_name: string (denormalized)
    role: string (headliner, opener, festival_performer)
    position: number
  }
  opening_song: string (optional)
  closing_song: string (optional)
  notes: string (optional)
  attended: boolean
  has_setlist: boolean (computed field)
  created_at: timestamp
  updated_at: timestamp
}
```

### `setlists`
```
{
  id: auto-generated
  concert_id: string (reference to concerts)
  setlistfm_id: string (optional)
  setlistfm_url: string (optional)
  song_count: number
  has_encore: boolean
  notes: string (optional)
  songs: array of {
    position: number
    name: string
    set_name: string (e.g., "Set 1", "Encore")
    encore: number (0 = not encore, 1 = first encore, etc.)
    is_cover: boolean
    cover_artist: string (optional)
    is_tape: boolean
    info: string (optional, e.g., ">", "->")
  }
  fetched_at: timestamp
  created_at: timestamp
}
```

### `concert_notes` (existing - for personal notes)
```
{
  id: concert_id
  notes: string
  created_at: timestamp
  updated_at: timestamp
}
```

### `concert_comments` (existing)
```
{
  id: auto-generated
  concert_id: string
  user_id: string
  user_name: string
  user_photo: string
  comment: string
  created_at: timestamp
}
```

### `pending_setlist_submissions` (existing)
```
{
  id: auto-generated
  concert_id: number
  setlistfm_url: string
  setlistfm_id: string
  submitted_by_email: string
  submitted_by_name: string
  submitted_at: timestamp
  status: string (pending, approved, rejected)
  reviewed_by_email: string (optional)
  reviewed_at: timestamp (optional)
  rejection_reason: string (optional)
  setlist_data: object (raw data from setlist.fm)
}
```

### `concert_photos` (new)
```
{
  id: auto-generated
  concert_id: string (reference to concerts)
  user_id: string (Firebase Auth UID of uploader)
  user_name: string (display name of uploader)
  user_photo: string (profile photo URL, optional)
  storage_path: string (path in Firebase Storage)
  download_url: string (public download URL)
  uploaded_at: timestamp
  file_size: number (bytes)
  file_type: string (MIME type: image/jpeg, image/png, etc.)
  caption: string (optional user caption)
}
```

## Denormalization Strategy

To optimize read performance and reduce queries, we denormalize some data:

- **concerts** includes venue name, city, state (instead of just venue_id)
- **concerts** includes artist names in the artists array
- **setlists** stores all songs inline (no separate songs collection)

This means:
- ✅ Fast reads (single query gets all concert data)
- ✅ No complex joins needed
- ⚠️ Larger documents
- ⚠️ Updates require updating multiple places (rare in this use case)

## Indexes

Firestore will auto-create single-field indexes. We'll need composite indexes for:

- `concerts`: `date` (desc)
- `concerts`: `has_setlist` + `date` (desc)
- `concerts`: `artists.artist_id` + `date` (desc)
- `concert_photos`: `concert_id` + `uploaded_at` (desc)

These will be created automatically when we run queries that need them.

## Firebase Storage Structure

Photos are stored in Firebase Storage:

```
/concert_photos/
  ├── {concert_id}/
  │   ├── {photo_id_1}.jpg
  │   ├── {photo_id_2}.png
  │   └── {photo_id_3}.jpg
  └── {another_concert_id}/
      └── {photo_id_4}.jpg
```

Each photo file is referenced in the `concert_photos` Firestore collection via `storage_path` and `download_url` fields.
