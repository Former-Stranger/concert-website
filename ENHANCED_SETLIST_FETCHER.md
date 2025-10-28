# Enhanced Setlist Fetcher - Co-Headliner Support

## Overview

The enhanced setlist fetcher (`fetch_setlists_enhanced.py`) automatically handles:
- ✅ **Single headliner concerts** - Creates one setlist document
- ✅ **Co-headliner concerts** - Creates separate setlist documents for each headliner
- ✅ **Cover artist names** - Captures original artist for covers
- ✅ **Tour names** - Captures tour name from setlist.fm
- ✅ **Guest artists** - Captures guest performer information

## How It Works

### For Single Headliner Concerts
1. Finds the headliner artist
2. Searches setlist.fm (venue + city + state + date → city + state + date → date only)
3. Creates setlist document with ID = `concert_id`
   - Example: Document ID `847` for concert 847

### For Co-Headliner Concerts
1. Identifies **all artists with `role='headliner'`**
2. Searches setlist.fm for **each headliner separately**
3. Creates **separate setlist documents** for each:
   - Example: `847-rod-stewart` and `847-cyndi-lauper`

### Document ID Format

**Single headliner:**
```
{concert_id}
```

**Co-headliners:**
```
{concert_id}-{artist-slug}
```

Where `artist-slug` is the artist name converted to lowercase with spaces replaced by hyphens.

**Examples:**
- `847-rod-stewart`
- `847-cyndi-lauper`
- `489-lynyrd-skynyrd`
- `489-doobie-brothers`

## Usage

### Basic Usage (Skip Existing)
Fetches setlists for concerts that don't have them yet:

```bash
python3 scripts/fetch_setlists_enhanced.py
```

### Test Mode (Dry Run)
See what would happen without making changes:

```bash
python3 scripts/fetch_setlists_enhanced.py --dry-run
```

### Test with Limited Concerts
Process only first 10 concerts (for testing):

```bash
python3 scripts/fetch_setlists_enhanced.py --limit 10 --dry-run
```

### Re-fetch All Setlists
Re-fetch setlists for ALL concerts (including those with existing setlists):

```bash
python3 scripts/fetch_setlists_enhanced.py --all
```

⚠️ **Warning:** This will overwrite existing setlists!

### Options

| Option | Description |
|--------|-------------|
| `--limit N` | Process only first N concerts (for testing) |
| `--dry-run` | Test mode - show what would happen but don't write to Firestore |
| `--all` | Process all concerts, even those with existing setlists |

## What Gets Captured

### For Each Setlist:

```javascript
{
  "concert_id": "847",
  "artist_id": "481",
  "artist_name": "Rod Stewart",
  "setlistfm_id": "63eb562f",
  "setlistfm_url": "https://www.setlist.fm/setlist/...",
  "tour_name": "2018 North American Summer Tour",  // NEW!
  "song_count": 19,
  "has_encore": false,
  "songs": [
    {
      "position": 1,
      "name": "Infatuation",
      "set_name": "Set 1",
      "is_cover": false,
      "cover_artist": null,
      "guest_artist": null  // NEW! (if present)
    },
    {
      "position": 2,
      "name": "Some Guys Have All the Luck",
      "set_name": "Set 1",
      "is_cover": true,
      "cover_artist": "The Persuaders"  // NEW! Now populated
    }
  ]
}
```

## Co-Headliner Detection

The script identifies co-headliners by looking at the `role` field:

```python
headliners = [a for a in artists if a.get('role') == 'headliner']

if len(headliners) > 1:
    # This is a co-headliner show
    # Fetch separate setlists for each
```

### Known Co-Headliner Shows

From the `headliners_to_review.csv`:

- Concert 847: Rod Stewart / Cyndi Lauper ✅ (Already fixed)
- Concert 487: Kenny Chesney / Zac Brown Band
- Concert 489: Lynyrd Skynyrd / Doobie Brothers
- Concert 1056: Bruce Springsteen / Jann Wenner
- Concert 1111: The Eagles + Steely Dan
- Concert 1112: Sting + Joe Sumner

## Output Example

```
================================================================================
ENHANCED SETLIST FETCHER - WITH CO-HEADLINER SUPPORT
================================================================================

📊 Loading concerts...
   Found 1275 concerts
   391 concerts need setlists
   Estimated time: 3.9 minutes

🔍 Starting setlist fetch...

🎤 [1/391] Concert 1234: Bruce Springsteen
      2023-09-15 at Madison Square Garden
      ✅ Found: Bruce Springsteen (28 songs)

🎭 [2/391] Concert 847: Rod Stewart, Cyndi Lauper
      2018-08-07 at Madison Square Garden
      ✅ Found 2 setlists: Rod Stewart (19), Cyndi Lauper (11)

🎤 [3/391] Concert 456: The Rolling Stones
      2022-10-20 at MetLife Stadium
      ❌ No setlists found for 1 headliner(s)

📈 Progress: 10/391 (2%)
   Success: 8 | Not found: 1 | Errors: 1
   Co-headliners: 1 | Total setlists created: 9
```

## Search Logic

For each headliner, the script uses progressive fallback:

### Attempt 1: Full Details
```
artist_name + date + venue_name + city + state
```

### Attempt 2: No Venue
```
artist_name + date + city + state
```

### Attempt 3: Date Only
```
artist_name + date
```

Returns the **first result** from the first successful search.

## Rate Limiting

- **2 requests per second** (setlist.fm API limit)
- Built-in delay of **0.6 seconds** between requests
- Automatic retry on rate limit errors (HTTP 429)

## Workflow

### 1. First Time Setup
```bash
# Test with a few concerts first
python3 scripts/fetch_setlists_enhanced.py --limit 10 --dry-run

# If results look good, run for real
python3 scripts/fetch_setlists_enhanced.py --limit 10
```

### 2. Fetch All Missing Setlists
```bash
# Fetch setlists for all concerts that don't have them
python3 scripts/fetch_setlists_enhanced.py
```

### 3. Export and Deploy
```bash
# Export to JSON
python3 scripts/export_to_web.py

# Deploy to Firebase
firebase deploy --only hosting
```

### 4. Re-fetch Specific Concert (If Needed)
To re-fetch a specific concert, delete its setlist document(s) in Firestore, then run:

```bash
python3 scripts/fetch_setlists_enhanced.py --limit 1000
```

Or manually fetch for a specific concert using the co-headliner script pattern.

## Advantages Over Old Script

### Old Script (`fetch_missing_setlists.py`)
- ❌ Only fetched setlist for **first artist**
- ❌ Missed co-headliner setlists
- ❌ Didn't capture cover artist names properly
- ❌ Didn't capture tour names
- ❌ Didn't capture guest artists

### New Script (`fetch_setlists_enhanced.py`)
- ✅ Fetches setlists for **all headliners**
- ✅ Automatically handles co-headliners
- ✅ Captures cover artist names
- ✅ Captures tour names
- ✅ Captures guest artists
- ✅ Creates proper document structure for export
- ✅ Better progress reporting
- ✅ Dry-run mode for testing

## Common Scenarios

### Scenario 1: New Concert Added
Just run the script - it will skip concerts that already have setlists:
```bash
python3 scripts/fetch_setlists_enhanced.py
```

### Scenario 2: Artist Name Was Fixed
The old setlist has the wrong artist. Re-fetch:
```bash
# Delete the old setlist document in Firestore
# Then run the script
python3 scripts/fetch_setlists_enhanced.py
```

### Scenario 3: Convert Single to Co-Headliner
Example: Concert 489 was marked as single artist "Lynyrd Skynyrd/Doobie Brothers" but should be two headliners.

1. Fix the concert document to have two headliners
2. Delete old setlist document
3. Run fetch script:
   ```bash
   python3 scripts/fetch_setlists_enhanced.py
   ```

It will automatically create two setlist documents:
- `489-lynyrd-skynyrd`
- `489-doobie-brothers`

### Scenario 4: Test Before Mass Fetch
Always test first with a small batch:
```bash
# Dry run with 10 concerts
python3 scripts/fetch_setlists_enhanced.py --limit 10 --dry-run

# If good, run for real
python3 scripts/fetch_setlists_enhanced.py --limit 10

# Then gradually increase or remove limit
python3 scripts/fetch_setlists_enhanced.py
```

## Troubleshooting

### "No setlists found"
Reasons:
1. Setlist doesn't exist on setlist.fm
2. Artist name doesn't match (check spelling)
3. Date is wrong in database
4. Venue/city/state don't match

**Solution:** Check setlist.fm manually, adjust concert data if needed.

### Multiple Setlists Created but One is Wrong
If one artist's setlist was found but it's wrong:
1. Delete the incorrect setlist document
2. Fix the artist name in the concert document
3. Re-run the fetch script

### Co-Headliner Not Detected
Check that **both artists have `role: 'headliner'`** in the concert document.

If one has `role: 'opener'`, they won't be fetched.

## Next Steps After Fetching

1. **Export data**: `python3 scripts/export_to_web.py`
2. **Review concert 847**: Check website to ensure tour name, cover artists, etc. display correctly
3. **Deploy**: `firebase deploy --only hosting`
4. **Fix any co-headliners**: Use `headliners_to_review.csv` to identify shows that need splitting

## Integration with Existing Workflow

This script **replaces** `fetch_missing_setlists.py` and provides enhanced functionality.

**Old workflow:**
```bash
python3 scripts/fetch_missing_setlists.py
```

**New workflow:**
```bash
python3 scripts/fetch_setlists_enhanced.py
```

All other scripts remain the same:
- `export_to_web.py` - Already updated to handle co-headliners
- `concert.js` - Already updated to display new fields
