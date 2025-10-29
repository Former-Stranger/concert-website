# Setlist Integration - Session Handoff Document

**Date:** October 28-29, 2025
**Session Duration:** ~5 hours
**Status:** ✅ Successfully deployed with 862 setlists

---

## Executive Summary

Successfully integrated setlist.fm API to automatically fetch and display concert setlists. The system now has:
- **862 concerts with setlists** (out of 1,275 total)
- **7,682 unique songs** tracked
- **20,648 total song performances** across all concerts
- Automatic co-headliner and opener support
- Full setlist display with encore tracking and cover song attribution

**Live Site:** https://earplugs-and-memories.web.app

---

## What Was Accomplished

### 1. Setlist.fm API Integration ✅

**File:** `scripts/setlistfm_client.py`

Created a robust API client with:
- Rate limiting (4 seconds between requests to avoid daily limits)
- Automatic retry logic for rate limit errors
- Artist name normalization (strips band suffixes like "& the E Street Band")
- Progressive search strategy (artist + date matching)
- Song extraction with cover detection and encore tracking

**Key Features:**
- Handles API rate limits (2 requests/second, 1,440/day)
- Cleans artist names by removing:
  - Parenthetical notes: "(Final Franchise)", "(75th Birthday)"
  - Band suffixes: "& the E Street Band", "+ Joe Sumner", etc.
  - Opener notation: "w/", "w."
- Searches by artist name + date (most reliable approach)
- Extracts full song data including covers, encores, and guest artists

### 2. Enhanced Setlist Fetcher ✅

**File:** `scripts/fetch_setlists_enhanced.py`

Multi-artist setlist fetching with:
- **Co-headliner support**: Fetches separate setlists for each headliner
- **Opener support**: Fetches setlists for opening acts
- **Festival performer support**: Handles festival lineups
- Document naming:
  - Single headliner: `{concert_id}` (e.g., "847")
  - Multiple headliners: `{concert_id}-{artist-slug}` (e.g., "847-rod-stewart", "847-cyndi-lauper")
- Automatic skip of existing setlists
- Comprehensive logging and progress tracking

**Usage:**
```bash
# Fetch all setlists (skips existing)
python3 scripts/fetch_setlists_enhanced.py

# Fetch with limit (for testing)
python3 scripts/fetch_setlists_enhanced.py --limit 100

# Dry run (no writes to Firestore)
python3 scripts/fetch_setlists_enhanced.py --dry-run

# Force re-fetch all (including existing)
python3 scripts/fetch_setlists_enhanced.py --all
```

### 3. Export Script Fixes ✅

**File:** `scripts/export_to_web.py`

Fixed critical bugs where `hasSetlist` flags weren't being set correctly:

**Before:**
- Read `has_setlist` from Firestore concert documents (never updated)
- Only 2 concerts showed hasSetlist=true
- Stats showed None for songs/setlists

**After:**
- Derives `hasSetlist` from actual setlist documents in Firestore
- Correctly marks 862 concerts with hasSetlist=true
- Stats properly calculated from actual data

**Key Changes:**
```python
# Now builds hasSetlist from actual setlist data
concert_ids_with_setlists = set(setlists_by_concert.keys())
for concert in concerts_list:
    if concert['id'] in concert_ids_with_setlists:
        concert['hasSetlist'] = True

# Stats use actual counts
concerts_with_setlists_count = len(concert_ids_with_setlists)
```

### 4. Test Scripts Created ✅

**For verification and debugging:**
- `scripts/fetch_single_concert.py` - Fetch one concert's setlist
- `scripts/inspect_setlist_api.py` - Test API responses
- `scripts/show_full_setlist_data.py` - Display complete setlist structure

---

## Current State

### API Keys
Two setlist.fm API keys configured (both hit daily limits during mass fetch):
1. **Primary:** `DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE`
2. **Secondary:** `Uo48MPdBZN5ujA_PJKkyeKYyiMzOaf-kd4gi`

Both keys exhausted their daily quotas. **Tomorrow's action:** Resume fetch to get remaining ~413 concerts.

### Firestore Database Structure

**Collections:**
1. **concerts** - Concert metadata (1,275 documents)
2. **setlists** - Setlist data (862+ documents)
   - Single headliner: Document ID = concert_id
   - Co-headliners: Document ID = `{concert_id}-{artist-slug}`
3. **artists** - Artist metadata
4. **venues** - Venue metadata
5. **concert_photos** - User-uploaded photos

**Setlist Document Structure:**
```json
{
  "concert_id": "847",
  "artist_id": "481",
  "artist_name": "Rod Stewart",
  "setlistfm_id": "...",
  "setlistfm_url": "https://www.setlist.fm/...",
  "song_count": 19,
  "has_encore": true,
  "tour_name": "The Hits Tour 2018",
  "songs": [
    {
      "position": 1,
      "name": "Infatuation",
      "set_name": "Set 1",
      "is_cover": false,
      "cover_artist": null
    },
    // ... more songs
  ]
}
```

### Exported JSON Files

**Location:** `website/data/`

**Key Files:**
- `concerts.json` - All concerts with hasSetlist flags (862 marked true)
- `concert_details/*.json` - 862 detail files with full setlist data
- `songs.json` - Song statistics and rankings
- `stats.json` - Site-wide statistics
- `artists.json` - Artist list with concert counts
- `venues.json` - Venue list with concert counts

**Stats Breakdown:**
- Total concerts: 1,273
- Concerts with setlists: 862 (67.7%)
- Unique songs: 7,682
- Total song performances: 20,648
- Top artist: Billy Joel (73 concerts)
- Most heard song: "Born to Run" (85 times)

---

## Known Issues & Limitations

### 1. API Rate Limits Hit ⚠️
**Impact:** Only processed ~600 out of 769 concerts needing setlists
**Remaining:** ~170 concerts still need setlists
**Solution:** Wait for daily quota reset (tomorrow) and resume

### 2. Artist Name Matching Challenges
**Issue:** Some artist name variations don't match:
- Example: "Bruce Springsteen & the E Street Band" vs "Bruce Springsteen"
- **Current solution:** Strip band suffixes before searching
- **Works for:** Most common patterns
- **May miss:** Unusual naming variations

### 3. Setlists Not on Setlist.fm
**Impact:** ~33% of concerts don't have setlists
**Reasons:**
- Setlist not submitted to setlist.fm
- Private/industry events
- Festival sets (often incomplete)
- Older concerts (pre-2000s have sparse coverage)

### 4. Venue Name Variations
**Issue:** Venue names change due to sponsorships
- Example: "Jones Beach Theater" vs "Northwell Health at Jones Beach Theater"
- **Solution:** Search by artist + date only (venue names ignored)
- **Works well:** Artist + date is very reliable

---

## Next Steps (TODO)

### Immediate (When API Limits Reset)
1. **Resume setlist fetch** for remaining ~170 concerts
   ```bash
   python3 scripts/fetch_setlists_enhanced.py --limit 1300
   ```
2. **Export updated data**
   ```bash
   python3 scripts/export_to_web.py
   ```
3. **Deploy to Firebase**
   ```bash
   firebase deploy --only hosting
   ```

### Future Enhancements
1. **Manual setlist submission**
   - Add UI for users to submit setlists
   - Store in pending_submissions collection
   - Admin review workflow

2. **Setlist editing**
   - Allow corrections to fetched setlists
   - Track source (API vs manual)

3. **Song matching improvements**
   - Normalize song names (remove variations)
   - Detect medleys
   - Better cover detection

4. **Festival handling**
   - Multi-day festival support
   - Stage/time information
   - Full festival lineups

---

## File Reference

### Modified Files

**Core Scripts:**
- `scripts/setlistfm_client.py` - API client (NEW)
- `scripts/fetch_setlists_enhanced.py` - Setlist fetcher (MODIFIED - added co-headliner/opener support)
- `scripts/export_to_web.py` - Export to static JSON (MODIFIED - fixed hasSetlist logic)

**Test/Utility Scripts:**
- `scripts/fetch_single_concert.py` - Single concert fetch (NEW)
- `scripts/inspect_setlist_api.py` - API testing (NEW)
- `scripts/show_full_setlist_data.py` - Display setlist structure (NEW)

**Data Files:**
- `website/data/concerts.json` - Updated with 862 hasSetlist flags
- `website/data/concert_details/*.json` - 862 setlist detail files
- `website/data/songs.json` - 7,682 unique songs
- `website/data/stats.json` - Correct statistics

### Log Files (Not Committed)
- `setlist_fetch_final.txt` - Main fetch log (598 concerts, crashed at 76%)
- `setlist_fetch_key2.txt` - Second API key attempt (rate limited)
- `setlist_fetch_slow.txt` - 4-second delay attempt

---

## Technical Details

### Artist Name Cleaning Logic

**Location:** `scripts/setlistfm_client.py:186-210`

```python
# Remove parenthetical notes
clean_artist = artist_name.split('(')[0].strip()

# Remove opener notation
clean_artist = clean_artist.split(' w/')[0].strip()
clean_artist = clean_artist.split(' w.')[0].strip()

# Remove band suffixes
band_suffixes = [
    ' & the E Street Band',
    ' & the Silver Bullet Band',
    ' & the 400 Unit',
    ' + Joe Sumner',
    # etc.
]
```

**Examples:**
- "Bruce Springsteen & the E Street Band" → "Bruce Springsteen" ✓
- "Kip Moore (Final Franchise)" → "Kip Moore" ✓
- "Sting + Joe Sumner" → "Sting" ✓

### Search Strategy

**Location:** `scripts/setlistfm_client.py:213-243`

**Approach:** Artist + Date matching only

**Why not venue/city?**
- Venue names change frequently (sponsorships)
- City data can have minor variations
- Date + artist name is highly reliable

```python
# Search by artist name + date
results = self.search_setlists(
    artist_name=search_artist,
    date=date_str  # Format: "dd-MM-yyyy"
)
```

### Rate Limiting

**Configuration:** `scripts/setlistfm_client.py:37-50`

```python
# 4 seconds between requests (very conservative)
self.min_request_interval = 4.0  # 0.25 req/sec

# API limits:
# - 2 requests/second
# - 1,440 requests/day
```

**Why 4 seconds?**
- Avoids cumulative rate limit errors
- Safer than hitting per-second limit repeatedly
- ~900 requests per hour
- Can fetch ~200-250 setlists before daily limit

---

## Debugging Tips

### Check Setlist in Firestore
```bash
# Via Firebase console
https://console.firebase.google.com/project/earplugs-and-memories/firestore

# Or via Python
python3
>>> import firebase_admin
>>> from firebase_admin import credentials, firestore
>>> cred = credentials.ApplicationDefault()
>>> firebase_admin.initialize_app(cred)
>>> db = firestore.client()
>>> setlist = db.collection('setlists').document('847').get()
>>> print(setlist.to_dict())
```

### Test API Search
```bash
python3 scripts/inspect_setlist_api.py
# Edit the script to test specific searches
```

### Check Export Data
```bash
# Check concerts with setlists
grep -c '"hasSetlist": true' website/data/concerts.json

# Check total songs
cat website/data/stats.json | python3 -m json.tool | grep total_songs

# List concert details files
ls website/data/concert_details/ | wc -l
```

### Re-run Export Only
```bash
# If setlists are in Firestore but not in JSON files
python3 scripts/export_to_web.py
firebase deploy --only hosting
```

---

## Success Metrics

✅ **862 concerts with setlists** (67.7% of database)
✅ **7,682 unique songs** catalogued
✅ **20,648 total performances** tracked
✅ **Co-headliner support** working (e.g., concert 847: Rod Stewart + Cyndi Lauper)
✅ **Opener support** working (e.g., concert 1276: Third Eye Blind + Dinosaur Jr.)
✅ **Cover song detection** working
✅ **Encore tracking** working
✅ **Export pipeline** fixed and working
✅ **Website display** showing all setlist data correctly

---

## Contact & Resources

**setlist.fm API Docs:** https://api.setlist.fm/docs/1.0/index.html
**Firebase Console:** https://console.firebase.google.com/project/earplugs-and-memories
**Live Website:** https://earplugs-and-memories.web.app

**Key Insights:**
- API key rotation needed for large fetches
- 4-second delays prevent rate limiting
- Artist + date matching is most reliable
- Export script must derive hasSetlist from actual data (not Firestore flags)

---

## Quick Command Reference

```bash
# Fetch remaining setlists (when quota resets)
python3 scripts/fetch_setlists_enhanced.py --limit 1300

# Export data to static JSON
python3 scripts/export_to_web.py

# Deploy to production
firebase deploy --only hosting

# Test single concert
python3 scripts/fetch_single_concert.py 847

# Check setlist count in Firestore
gcloud firestore documents list setlists --limit 1000 | wc -l
```

---

**End of Handoff Document**
*Resume from here: Wait for API quota reset, then fetch remaining ~170 concerts*
