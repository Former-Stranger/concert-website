# Concert 1274 Analysis - Why it Was Labeled "Multi-Artist Show"

## The Problem

Concert 1274 (Mumford & Sons with Lucius opener) has two issues:

1. **Incorrectly labeled as "Multi-Artist Show"** instead of a regular headliner concert
2. **Missing Lucius setlist** - the opening act's setlist was never fetched

**Live URL:** https://earplugsandmemories.com/concert.html?id=1274

## Root Cause: The `parse_festivals.py` Logic

### How Concerts Were Initially Created

The project has a data import pipeline that processes concert data from CSV files. When processing artist names, the `parse_festivals.py` script tries to intelligently detect:

1. **Festivals** - Multi-day events with many performers
2. **Multi-Artist Shows** - Single concerts with multiple equal-billing artists
3. **Regular Concerts** - Single headliner with optional opener

### The Problematic Logic

**File:** `scripts/parse_festivals.py:110-142`

The script has this logic:

```python
# Pattern 3: Artist & Artist (but not protected band names)
if ' & ' in artist_string:
    # Check if whole string is a protected band
    if self.is_protected_band(artist_string):
        return None, [artist_string]

    # Split and check each part
    # ... logic to handle combinations ...

    if len(valid_artists) > 1:
        return 'Multi-Artist Show', valid_artists  # ← THIS HAPPENED
```

### The Protected Bands List

The script maintains a list of bands that contain `&` or `and` but should be treated as single entities:

```python
PROTECTED_BANDS = [
    'Bruce Springsteen & the E Street Band',
    'Tom Petty & the Heartbreakers',
    'Hootie & the Blowfish',
    'Hall & Oates',
    'Bob Seger & the Silver Bullet Band',
    # ... etc
]
```

**The Problem:** `Mumford & Sons` is **NOT** in this protected list!

### What Happened to Concert 1274

1. **Concert created:** October 15, 2025 at 00:05:50 UTC
2. **Artist name entered:** Likely "Mumford & Sons" (possibly with or without "with Lucius")
3. **parse_festivals.py logic:**
   - Detected `" & "` in "Mumford & Sons"
   - Checked if "Mumford & Sons" is in `PROTECTED_BANDS` → **NO**
   - Assumed it was two separate artists: "Mumford" and "Sons"
   - Returned: `('Multi-Artist Show', ['Mumford', 'Sons'])`
4. **Database record created:**
   - `festival_name: "Multi-Artist Show"`
   - `artists: [{"artist_name": "Mumford & Sons", "role": "festival_performer"}]`
   - Lucius was never added to the artists array

### Why Lucius Setlist Wasn't Fetched

**File:** `scripts/fetch_setlists_enhanced.py:142-143`

```python
performing_artists = [a for a in artists if a.get('role') in ['headliner', 'opener', 'festival_performer']]
```

The setlist fetcher only looks for artists **in the concert's artists array**. Since Lucius was never added to the database, the script never attempted to fetch their setlist.

---

## Comparison: Why Concert 1276 Worked Correctly

**Concert 1276:** Third Eye Blind with Dinosaur Jr.

This worked because:
- "Third Eye Blind" contains **no `&` or `and`**
- Was correctly identified as a regular concert
- Both artists were properly added:
  - Third Eye Blind: `role: "headliner"`
  - Dinosaur Jr.: `role: "opener"`
- Both setlists were fetched

---

## The Fix

### Script Created: `fix_concert_1274.py`

The script performs these steps:

1. **Update Mumford & Sons role:**
   - `festival_performer` → `headliner`

2. **Remove festival designation:**
   - `festival_name: "Multi-Artist Show"` → `null`

3. **Add Lucius as opener:**
   - Create Lucius artist if doesn't exist
   - Add to artists array with `role: "opener"`

4. **Fetch Lucius setlist:**
   - Use setlist.fm API to fetch setlist
   - Create setlist document: `1274-lucius`
   - Parse and store all songs

5. **Re-export and deploy:**
   - Run `export_to_web.py` to regenerate JSON
   - Deploy to Firebase Hosting

### Running the Fix

```bash
cd /Users/akalbfell/Documents/Jay/concert-website
python3 scripts/fix_concert_1274.py
python3 scripts/export_to_web.py
firebase deploy --only hosting
```

### Expected Result

After the fix, the concert page will show:

```
Mumford & Sons
Rushmere Tour
August 9, 2025
Forest Hills Stadium - Forest Hills, NY

Opening Act(s):
  Lucius - 10 songs
  [Lucius setlist displayed]

Mumford & Sons - 22 songs
  [Mumford & Sons setlist displayed]
```

---

## Future Prevention

### Option 1: Add Mumford & Sons to Protected Bands

Edit `scripts/parse_festivals.py`:

```python
PROTECTED_BANDS = [
    'Bruce Springsteen & the E Street Band',
    'Tom Petty & the Heartbreakers',
    'Hootie & the Blowfish',
    'Mumford & Sons',  # ← ADD THIS
    # ... etc
]
```

### Option 2: Improve Detection Logic

The parser could be enhanced to:
- Check if artist exists in database before splitting
- Use setlist.fm API to verify if it's a real band name
- Require manual confirmation for ambiguous cases

### Option 3: Manual Concert Entry

For future concerts, use the web form at `/add-concert.html` which allows explicit specification of:
- Headliner artist
- Opening act (optional)
- Festival name (optional)

This bypasses the automatic parsing logic entirely.

---

## Statistics

**Current State (Before Fix):**
- Concert 1274 setlist count: 1 (Mumford & Sons only)
- Total songs: 22
- Lucius: Not in artists array

**After Fix:**
- Concert 1274 setlist count: 2 (Mumford & Sons + Lucius)
- Total songs: 32 (22 + 10)
- Lucius: Added as opener

---

## Related Files

- **Parser Logic:** `scripts/parse_festivals.py` (lines 110-142)
- **Initial Import:** `scripts/2_normalize_artists.py` (uses FestivalParser)
- **Setlist Fetcher:** `scripts/fetch_setlists_enhanced.py` (lines 142-143)
- **Fix Script:** `scripts/fix_concert_1274.py` (this creates/updates data)
- **Export Script:** `scripts/export_to_web.py` (regenerates JSON files)

---

## Key Takeaway

**The "Multi-Artist Show" label was NOT from setlist.fm data.** It was generated by the project's own `parse_festivals.py` script during initial data import, based on pattern matching of the artist name "Mumford & Sons" which contains `&`.

The setlist.fm API doesn't provide festival/event classification in its responses (this was verified by inspecting API responses in other scripts). All festival detection is done client-side by the import scripts.
