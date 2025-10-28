# Co-Headliner Setlist Proposal

## Problem Statement

Concert 847 (Rod Stewart / Cyndi Lauper) has **two separate setlists** on setlist.fm:
- https://www.setlist.fm/setlist/rod-stewart/2018/madison-square-garden-new-york-ny-63eb562f.html
- https://www.setlist.fm/setlist/cyndi-lauper/2018/madison-square-garden-new-york-ny-6beb562e.html

**Requirements:**
1. ✅ Concert count = 1 (one show attended)
2. ✅ Each artist's page shows only their own setlist
3. ✅ Concert page shows both setlists
4. ✅ Stats count this as 1 concert, not 2

## Recommended Solution: Multiple Setlists per Concert

### Data Structure

**Concert Document (Already Fixed):**
```json
{
  "id": "847",
  "date": "2018-08-07",
  "venue_name": "Madison Square Garden",
  "artists": [
    {
      "artist_id": "481",
      "artist_name": "Rod Stewart",
      "role": "headliner",
      "position": 1
    },
    {
      "artist_id": "Ts7IBnCtQNORftKRdruR",
      "artist_name": "Cyndi Lauper",
      "role": "headliner",
      "position": 2
    }
  ]
}
```

**Setlist Documents (New Structure):**
```json
// Document ID: "847-rod-stewart" or "847-1"
{
  "concert_id": "847",
  "artist_id": "481",  // NEW FIELD
  "artist_name": "Rod Stewart",  // NEW FIELD for easier querying
  "setlistfm_id": "63eb562f",
  "setlistfm_url": "https://www.setlist.fm/setlist/rod-stewart/...",
  "song_count": 18,
  "has_encore": true,
  "songs": [
    { "position": 1, "name": "Infatuation", ... },
    // ... Rod's songs
  ]
}

// Document ID: "847-cyndi-lauper" or "847-2"
{
  "concert_id": "847",
  "artist_id": "Ts7IBnCtQNORftKRdruR",  // NEW FIELD
  "artist_name": "Cyndi Lauper",  // NEW FIELD
  "setlistfm_id": "6beb562e",
  "setlistfm_url": "https://www.setlist.fm/setlist/cyndi-lauper/...",
  "song_count": 16,
  "has_encore": true,
  "songs": [
    { "position": 1, "name": "She Bop", ... },
    // ... Cyndi's songs
  ]
}
```

### Schema Changes Required

**Add to `setlists` collection:**
- `artist_id`: string (optional - only set for co-headliner setlists)
- `artist_name`: string (optional - denormalized for easier display)

**Backward Compatible:**
- Existing setlists without `artist_id` still work (single-headliner shows)
- Only co-headliner concerts use multiple setlist documents

### Document ID Strategy

**Option A: Descriptive (Recommended)**
- `847-rod-stewart`
- `847-cyndi-lauper`
- Easy to debug, human-readable

**Option B: Position-based**
- `847-1` (first headliner)
- `847-2` (second headliner)
- Simpler naming, relies on artist position in concert doc

### Code Changes Required

#### 1. Export Script (`export_to_web.py`)

**Current:**
```python
setlist_doc = db.collection('setlists').document(concert_id).get()
```

**New:**
```python
# Query all setlists for this concert
setlists_query = db.collection('setlists').where('concert_id', '==', concert_id).stream()
setlists = list(setlists_query)

if len(setlists) == 0:
    # No setlist
    continue
elif len(setlists) == 1:
    # Single setlist (normal case)
    export_single_setlist(setlists[0])
else:
    # Multiple setlists (co-headliners)
    export_multiple_setlists(concert, setlists)
```

**Export Format for Co-Headliners:**
```json
{
  "id": "847",
  "date": "2018-08-07",
  "venue": "Madison Square Garden",
  "artists": [...],
  "setlists": [  // NEW: array instead of single object
    {
      "artist_id": "481",
      "artist_name": "Rod Stewart",
      "song_count": 18,
      "songs": [...]
    },
    {
      "artist_id": "Ts7IBnCtQNORftKRdruR",
      "artist_name": "Cyndi Lauper",
      "song_count": 16,
      "songs": [...]
    }
  ],
  "total_song_count": 34,  // Sum of both
  "has_encore": true  // True if ANY setlist has encore
}
```

#### 2. Concert Display Page (`concert.js`)

**Current:**
```javascript
// Expects single songs array
const songs = concert.songs;
```

**New:**
```javascript
// Handle both single setlist and multiple setlists
if (concert.setlists) {
  // Co-headliner: multiple setlists
  renderMultipleSetlists(concert.setlists);
} else {
  // Single setlist (backward compatible)
  renderSingleSetlist(concert.songs);
}
```

**Display Format:**
```
Rod Stewart (18 songs)
Set 1:
  1. Infatuation
  2. Some Guys Have All the Luck
  ...

Cyndi Lauper (16 songs)
Set 1:
  1. She Bop
  2. Girls Just Want to Have Fun
  ...
```

#### 3. Artist Pages (`artist_details.json`)

**Current Query (implicit):**
- Artist pages currently only show concerts where artist is listed
- Songs are aggregated from setlists where concert has that artist

**New Query:**
```python
# Get setlists for this artist specifically
artist_setlists = db.collection('setlists').where('artist_id', '==', artist_id).stream()

# This automatically filters to only songs that artist performed
# Even in co-headliner shows
```

#### 4. Stats Calculation

**Important:** Concert count stays correct because:
- We count distinct `concert_id` values
- Concert 847 = 1 concert (even though it has 2 setlists)

```python
# This still returns 1 for concert 847
total_concerts = len(set(concert['concert_id'] for concert in concerts))
```

### Migration Strategy

**Phase 1: Schema Update**
1. ✅ Concert 847 already has 2 separate artist records (DONE)
2. Add `artist_id` and `artist_name` fields to setlists schema documentation
3. Update Firestore indexes if needed

**Phase 2: Create Multiple Setlists**
1. Fetch both setlists from setlist.fm:
   - Rod Stewart: `63eb562f`
   - Cyndi Lauper: `6beb562e`
2. Create two setlist documents:
   - `847-rod-stewart` with Rod's songs
   - `847-cyndi-lauper` with Cyndi's songs
3. Delete old single setlist if it exists

**Phase 3: Update Export/Display**
1. Update `export_to_web.py` to handle multiple setlists per concert
2. Update `concert.js` to display multiple setlists
3. Test with concert 847

**Phase 4: Handle Other Co-Headliners**
- Apply same pattern to other co-headliner shows:
  - Concert 487: Kenny Chesney/Zac Brown Band
  - Concert 489: Lynyrd Skynyrd/Doobie Brothers
  - Concert 775: Buckingham/McVie (but this might be band name)

### Alternative: Quick Fix (Option 2)

If you want a **simpler immediate solution**:

1. Keep **one** setlist document: `847`
2. Combine both setlists into one `songs` array
3. Use `set_name` to distinguish:
   - "Rod Stewart - Set 1"
   - "Rod Stewart - Encore"
   - "Cyndi Lauper - Set 1"
   - "Cyndi Lauper - Encore"

**Pros:**
- ✅ Works with existing code
- ✅ Quick to implement
- ✅ Concert count = 1

**Cons:**
- ❌ Artist pages show ALL songs (both artists)
- ❌ Can't easily filter songs by individual artist
- ❌ Doesn't match setlist.fm structure

## Recommendation

**Use Option 1 (Multiple Setlists)** because:
1. It's the most accurate representation
2. Artist pages will be correct
3. Scales to any number of co-headliners
4. Mirrors how setlist.fm structures the data
5. Concert count stays at 1 (most important requirement)

The code changes are manageable and make the system more flexible for future co-headliner shows.
