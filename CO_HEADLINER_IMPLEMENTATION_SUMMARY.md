# Co-Headliner Setlist Implementation Summary

## Status: Code Complete - Ready for Testing

All code changes have been implemented to support multiple setlists per concert for co-headliner shows. The implementation is **backward compatible** with existing single-setlist concerts.

---

## What Was Implemented

### 1. Concert Data Fixed (Already Done)
Concert 847 (Rod Stewart / Cyndi Lauper) now has two separate artist records:
- Rod Stewart (artist_id: 481, role: headliner, position: 1)
- Cyndi Lauper (artist_id: Ts7IBnCtQNORftKRdruR, role: headliner, position: 2)

### 2. Setlist Creation Script
**File:** `scripts/create_coheadliner_setlists_847.py`

Creates two setlist documents for Concert 847:
- Document ID: `847-rod-stewart` (Rod Stewart's setlist)
- Document ID: `847-cyndi-lauper` (Cyndi Lauper's setlist)

Each setlist includes:
- `concert_id`: "847"
- `artist_id`: Artist's ID from concerts collection
- `artist_name`: Artist name for display
- `setlistfm_id`: ID from setlist.fm
- `setlistfm_url`: Full URL to setlist.fm page
- `songs`: Array of song objects
- `song_count`: Number of songs
- `has_encore`: Boolean

**Usage:**
```bash
python3 scripts/create_coheadliner_setlists_847.py YOUR_SETLISTFM_API_KEY
```

### 3. Export Script Updated
**File:** `scripts/export_to_web.py`

**Changes:**
- Groups setlists by `concert_id` instead of iterating individually
- Detects when a concert has multiple setlists
- Exports different formats based on count:

**Single Setlist (Backward Compatible):**
```json
{
  "id": "123",
  "date": "2023-01-01",
  "artists": [...],
  "setlistfm_url": "...",
  "song_count": 20,
  "has_encore": true,
  "songs": [...]
}
```

**Multiple Setlists (Co-Headliners):**
```json
{
  "id": "847",
  "date": "2018-08-07",
  "artists": [...],
  "setlists": [
    {
      "artist_id": "481",
      "artist_name": "Rod Stewart",
      "setlistfm_url": "...",
      "song_count": 18,
      "has_encore": true,
      "songs": [...]
    },
    {
      "artist_id": "Ts7IBnCtQNORftKRdruR",
      "artist_name": "Cyndi Lauper",
      "setlistfm_url": "...",
      "song_count": 16,
      "has_encore": true,
      "songs": [...]
    }
  ],
  "total_song_count": 34,
  "has_encore": true
}
```

### 4. Concert Display Page Updated
**File:** `website/js/concert.js`

**Changes:**
- Detects `concert.setlists` array vs `concert.songs` array
- Automatically renders appropriate format
- For multiple setlists:
  - Shows "Setlists" (plural) header
  - Displays each artist's name and song count
  - Shows separate setlist.fm link for each artist
  - Adds visual separator (horizontal rule) between setlists
- For single setlist:
  - Uses original rendering (backward compatible)

**Display Format:**
```
Rod Stewart (18 songs)                    [View on Setlist.fm]
  Set 1:
    1. Infatuation
    2. Some Guys Have All the Luck
    ...
  Encore:
    18. Sailing

─────────────────────────────────────────────────────────────

Cyndi Lauper (16 songs)                   [View on Setlist.fm]
  Set 1:
    1. She Bop
    2. Girls Just Want to Have Fun
    ...
  Encore:
    16. Time After Time
```

---

## Key Design Decisions

### 1. Document ID Strategy
Using descriptive IDs: `{concert_id}-{artist_slug}`
- Example: `847-rod-stewart`, `847-cyndi-lauper`
- Human-readable and easy to debug
- Clear relationship to concert and artist

### 2. Schema Changes
Added to `setlists` collection:
- `artist_id` (string, optional): Links to artist in concerts collection
- `artist_name` (string, optional): Denormalized for display

**Backward Compatible:**
- Existing setlists without these fields still work
- Only co-headliner concerts use multiple documents

### 3. Concert Count Preservation
**Critical Requirement:** Concert 847 = 1 concert (not 2)

**How it's preserved:**
- Concerts collection has ONE document (id: 847)
- Setlists collection has TWO documents (847-rod-stewart, 847-cyndi-lauper)
- Both link to the same concert via `concert_id: "847"`
- Concert statistics count unique `concert_id` values
- Artist pages filter by `artist_id` in setlists

---

## Next Steps (User Action Required)

### Step 1: Fetch Setlists from Setlist.fm
You need your setlist.fm API key to run this step.

```bash
# Run the script with your API key
python3 scripts/create_coheadliner_setlists_847.py YOUR_API_KEY
```

This will:
1. Fetch Rod Stewart's setlist (ID: 63eb562f)
2. Fetch Cyndi Lauper's setlist (ID: 6beb562e)
3. Create two setlist documents in Firestore
4. Delete old setlist document (if exists)

### Step 2: Export Updated Data
```bash
python3 scripts/export_to_web.py
```

This will:
- Export all concerts with new multi-setlist support
- Create `website/data/concert_details/847.json` with both setlists
- Update all other concert detail files
- Update artist and venue details

### Step 3: Test Locally
Open `website/concert.html?id=847` in a browser to verify:
- Both artist names show in header: "Rod Stewart, Cyndi Lauper"
- Stats show combined totals (34 songs)
- Two separate setlists display
- Each setlist has its own setlist.fm link

### Step 4: Deploy
```bash
firebase deploy --only hosting
```

### Step 5: Verify Live
Visit: https://earplugsandmemories.com/concert.html?id=847

Check:
- ✅ Concert displays both artists
- ✅ Two separate setlists visible
- ✅ Concert count on homepage is correct (doesn't increase)
- ✅ Artist pages show individual setlists:
  - Rod Stewart's page: Only his songs from concert 847
  - Cyndi Lauper's page: Only her songs from concert 847

---

## Future Co-Headliner Shows

To add more co-headliner shows, follow this pattern:

### Concert Data
1. Split artist name in concerts collection
2. Create separate artist records with `role: 'headliner'`

### Setlist Data
1. Fetch each artist's setlist from setlist.fm
2. Create setlist document: `{concert_id}-{artist_slug}`
3. Include `artist_id` and `artist_name` fields

### Example: Concert 487 (Kenny Chesney / Zac Brown Band)
```bash
# 1. Fix concert data (similar to fix_co_headliners.py)
python3 scripts/fix_concert_487.py

# 2. Create setlists
python3 scripts/create_coheadliner_setlists_487.py YOUR_API_KEY

# 3. Export and deploy
python3 scripts/export_to_web.py
firebase deploy --only hosting
```

---

## Other Co-Headliner Concerts to Fix

From `headliners_to_review.csv`:

1. **Concert 487**: Kenny Chesney/Zac Brown Band
2. **Concert 489**: Lynyrd Skynyrd/Doobie Brothers
3. **Concert 775**: Buckingham/McVie (verify - might be band name)
4. **Concert 837**: Steve Miller Band/Peter Frampton
5. **Concert 1056**: Bruce Springsteen / Jann Wenner
6. **Concert 1069**: Last Waltz with Warren Haynes + Jamey Johnson
7. **Concert 1106**: Joe Bonamassa + Styx + Don Felder
8. **Concert 1111**: The Eagles + Steely Dan
9. **Concert 1112**: Sting + Joe Sumner

---

## Technical Notes

### Querying Multiple Setlists
```javascript
// In export_to_web.py
setlists_by_concert = defaultdict(list)
for setlist_doc in setlists_docs:
    concert_id = setlist_doc.get('concert_id')
    setlists_by_concert[concert_id].append(setlist_doc)

# Process each concert
for concert_id, setlist_list in setlists_by_concert.items():
    if len(setlist_list) == 1:
        # Single setlist
    else:
        # Multiple setlists
```

### Artist Page Filtering
When exporting artist pages, filter setlists by `artist_id`:
```python
# Get setlists for this specific artist
artist_setlists = db.collection('setlists').where('artist_id', '==', artist_id).stream()
```

This ensures:
- Rod Stewart's page shows only his songs from concert 847
- Cyndi Lauper's page shows only her songs from concert 847
- Concert 847 appears on both artist pages
- But each artist page shows different setlists

---

## Benefits of This Approach

1. **Accurate Data**: Matches setlist.fm structure
2. **Proper Artist Pages**: Each artist shows only their songs
3. **Concert Count Preserved**: 847 = 1 concert, not 2
4. **Scalable**: Works for any number of co-headliners
5. **Backward Compatible**: Existing single setlists unchanged
6. **Clean Separation**: Each artist's setlist is independent
7. **Multiple Links**: Each setlist links to its setlist.fm page

---

## Questions or Issues?

If you encounter any issues:
1. Check Firestore for setlist documents (847-rod-stewart, 847-cyndi-lauper)
2. Check exported JSON: `website/data/concert_details/847.json`
3. Check browser console for JavaScript errors
4. Verify concert count didn't increase on homepage

## Files Modified

- ✅ `scripts/create_coheadliner_setlists_847.py` (created)
- ✅ `scripts/export_to_web.py` (updated)
- ✅ `website/js/concert.js` (updated)
- ✅ `CO_HEADLINER_SETLIST_PROPOSAL.md` (created)
- ✅ `CO_HEADLINER_IMPLEMENTATION_SUMMARY.md` (this file)
