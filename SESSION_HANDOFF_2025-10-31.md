# Session Handoff - October 31, 2025

## Session Overview
**MAJOR UPDATE - All Core Features Complete**

Completed implementation and testing of tour name capture, automatic opener detection, and delete setlist functionality. Fixed critical Service Worker caching issues that prevented deployments. All requested features from the session handoff are now working.

## What Was Accomplished

### 1. Tour Name Capture ✅ COMPLETE
**Status**: Working perfectly

**Implementation**:
- `functions/index.js` lines 253-255: Extract tour name from setlist.fm API response (`setlistData.tour.name`)
- `functions/index.js` line 290: Store `tour_name` in setlist document
- `website/js/concert.js` line 163: Display tour name under artist name on concert page
- `scripts/export_to_web.py` lines 165-168, 233-235: Export tour name to JSON for both single and multi-setlist formats

**Testing**: Concert 938 (Brad Paisley, 2019-08-29) successfully displays "2019 World Tour"

**Note**: Tour name is optional - only set if exists in setlist.fm data.

### 2. Automatic Opener Detection & Addition ✅ COMPLETE
**Status**: Working - all 3 setlists created, artists added to concert

**How It Works**:
1. User submits headliner's setlist URL
2. Cloud Function queries setlist.fm for ALL setlists at that venue/date
3. For each setlist found:
   - Creates setlist document in Firestore
   - Adds artist to concert's `artists` array if not already present
   - Determines role (opener vs headliner) by comparing song counts
   - Uses proper document ID format (single: `concertId`, multi: `concertId-artistSlug`)

**Implementation**:
- `functions/index.js` lines 265-291: Duplicate prevention logic - checks if THIS specific artist already has a setlist before creating new one
- `functions/index.js` lines 300-378: Artist addition to concert - creates/finds artist in artists collection, determines role, adds to concert's artists array
- `website/js/concert.js` lines 209-232: Multi-setlist rendering with correct document IDs
- `scripts/export_to_web.py` lines 175-188: Sort setlists by role (openers first), map roles by artist_name

**Role Determination**: Compares song counts of all setlists for the concert. If another setlist has more songs, marks artist as "opener".

**Testing - Concert 938**: Successfully created all 3 setlists:
- Brad Paisley (doc ID: `938`) - 24 songs, headliner, "2019 World Tour"
- Chris Lane (doc ID: `938-chris-lane`) - 8 songs, opener
- Riley Green (doc ID: `938-riley-green`) - 7 songs, opener

**Testing - Concert 969**: Created single setlist:
- Eagles (doc ID: `969`) - 32 songs

### 3. Delete Setlist Functionality ✅ COMPLETE
**Status**: Working (with known limitations)

**Features**:
- Delete buttons visible to admin users only
- Confirmation dialog before deletion
- Removes setlist from Firestore immediately
- Updates concert's `has_setlist` flag
- Triggers deployment in background via Cloud Function
- Different messages for last setlist (2-min auto-reload) vs multiple setlists

**Implementation**:
- `website/concert.html` lines 400-474: `setupDeleteButtons()` function with handler attachment
- `website/concert.html` lines 476-499: Auth callback initializes delete buttons and MutationObserver
- `website/js/concert.js` lines 171-173, 244-246: Delete button rendering in HTML (hidden by default)

**MutationObserver**: Watches DOM for new delete buttons being added (handles async data loading) and automatically shows them to admin users.

**Known Limitation**: Deleted setlist remains visible on page until export completes (~2 min) or manual refresh. This is due to:
- Complex HTML structure with wrapper divs and `<hr>` separators makes selective DOM removal difficult
- Page loads from static JSON files anyway, so DOM changes are temporary
- Acceptable workaround: For last setlist, page auto-reloads after 2 minutes

**Code Location**: `website/concert.html` lines 447-462 (delete logic and success messages)

### 4. Export Script Improvements ✅ COMPLETE
**Status**: Working - auto-deletes stale files

**Problem Solved**: When all setlists deleted from a concert, old concert detail JSON files remained, causing website to show deleted data for 10-20 minutes until manual cleanup.

**Solution**:
- `scripts/export_to_web.py` lines 244-256: After exporting concerts with setlists, scan existing detail files in `website/data/concert_details/` directory
- Delete any JSON files for concerts NOT in the current export set (concerts without setlists)
- Log deleted files for visibility

**Testing**: Concerts 938 and 1230 - verified stale files are now auto-deleted on export run.

### 5. Service Worker Cache Management ✅ FIXED
**Status**: Critical fix - deployments now work

**Problem**: Browser Service Worker was aggressively caching old JavaScript files. Even after multiple `firebase deploy` commands, users (including admin) were loading ancient version v=1761875488 instead of latest updates.

**Root Causes**:
1. Service Worker cached all HTML/JS files on first install
2. Cache version wasn't being bumped between deployments
3. Firebase Hosting had stale files cached (required `--force` flag)
4. No clear cache mechanism for users

**Solution**:
- Bumped Service Worker cache version: v8 → v9
- `website/service-worker.js` lines 1-5: Version 1.0.8, CACHE_NAME and DATA_CACHE_NAME both updated to v9
- Forced fresh Firebase deployment with `firebase deploy --only hosting --force`
- All HTML files updated to cache version v=1761957023
- Documented cache clearing procedure for users

**How to Clear Cache** (for reference):
1. DevTools → Application tab → Clear storage → "Clear site data" button
2. OR: DevTools → Application → Service Workers → "Unregister"
3. Close ALL browser tabs
4. Wait 10 seconds
5. Reopen browser and visit site
6. Verify version: Check console for `concert.js?v=1761957023`

**Prevention**: Always bump Service Worker CACHE_NAME when deploying breaking changes.

## Files Modified Summary

### Cloud Functions
- **functions/index.js**:
  - Lines 253-255: Tour name extraction from setlist.fm API
  - Lines 265-291: Duplicate setlist prevention (checks if same artist already has setlist)
  - Lines 300-378: Artist addition to concert with role determination

### Frontend HTML
- **website/concert.html**:
  - Lines 400-474: `setupDeleteButtons()` function with MutationObserver support
  - Lines 476-499: Auth callback with delete button initialization and DOM mutation watching
  - Cache version updated throughout: v=1761957023

### Frontend JavaScript
- **website/js/concert.js**:
  - Line 163: Tour name display in setlist header
  - Lines 166, 294-298: Artist name display (handles both 'name' and 'artist_name' properties)
  - Lines 171-173, 244-246: Delete button rendering in setlist HTML
  - Lines 209-232: Multi-setlist rendering with `getSetlistDocId()` helper

- **website/service-worker.js**:
  - Lines 1-5: Version bumped to 1.0.8, cache names updated to v9

### Backend Scripts
- **scripts/export_to_web.py**:
  - Lines 165-168: Tour name export for single setlist format
  - Lines 179-180, 209: Artist role mapping by artist_name (not artist_id - MusicBrainz IDs don't match Firestore IDs)
  - Lines 233-235: Tour name export for multi-setlist format
  - Lines 244-256: Stale detail file cleanup logic

- **scripts/update_cache_version.py**:
  - Existing file - generates timestamp-based cache versions
  - Updates all `?v=` query parameters in HTML files

- **deploy.sh**:
  - Lines 9-16: Calls `update_cache_version.py` before export

## Current System State

### Cache Versions
- **Current deployed version**: v=1761957023
- **Service Worker cache**: v9 (earplugs-memories-v9, earplugs-memories-data-v9)
- **Previous versions** (obsolete): v=1761875488 (before session), v=1761938757 (intermediate)

### Test Concerts Status

**Concert 938** (Brad Paisley, 2019-08-29, Xfinity Center, Mansfield MA):
- ✅ 3 setlists created (Brad Paisley, Chris Lane, Riley Green)
- ✅ Tour name captured: "2019 World Tour"
- ✅ Correct document IDs: 938, 938-chris-lane, 938-riley-green
- ✅ Roles assigned correctly: Brad=headliner, others=opener
- ✅ All delete buttons visible to admin
- **Status**: Ready for continued testing

**Concert 969** (Eagles):
- ✅ 1 setlist created (32 songs)
- ✅ Delete button visible to admin
- **Status**: Active

**Concert 1230**:
- ✅ Clean slate (no setlists)
- **Status**: Ready for fresh testing

### Firestore Data Structure

**concerts Collection**:
```javascript
{
  id: "938",
  show_number: 937,
  date: "2019-08-29",
  venue_name: "Xfinity Center",
  city: "Mansfield",
  state: "MA",
  has_setlist: true,  // Updated when setlists added/removed
  artists: [           // Updated when setlists created
    {
      artist_id: "firestore-doc-id",  // From artists collection
      artist_name: "Brad Paisley",
      role: "headliner",              // Determined by song count comparison
      position: 1
    },
    {
      artist_id: "firestore-doc-id",
      artist_name: "Chris Lane",
      role: "opener",
      position: 2
    }
  ]
}
```

**setlists Collection**:
```javascript
{
  // Document ID: "938" (single) OR "938-chris-lane" (multi)
  concert_id: "938",
  artist_id: "musicbrainz-id",        // From setlist.fm (MusicBrainz)
  artist_name: "Chris Lane",
  song_count: 8,
  tour_name: null,                    // Optional - from setlist.fm
  setlistfm_url: "https://...",
  has_encore: false,
  songs: [
    {
      position: 1,
      name: "Song Title",
      set_name: "Main Set",
      encore: 0,
      is_cover: false,
      cover_artist: null
    }
  ]
}
```

**admins Collection**:
- akalbfell@gmail.com (uid: jBa71VgYp0Qz782bawa4SgjHu1l1)
- jlbisogni@gmail.com (uid: aiPsaFrLeRUBzJ9hoF7bNHcI6ss1)

### Static Files Architecture

**Data Flow**:
1. User submits setlist → Firestore
2. Cloud Function processes → Creates setlist docs, updates concert
3. Cloud Function triggers GitHub Actions → Runs export script
4. Export script generates JSON files from Firestore
5. GitHub Actions deploys to Firebase Hosting
6. Users load static JSON files (with no-cache headers for HTML/data)

**JSON Files** (in `website/data/`):
- `concerts.json` - All concerts with hasSetlist flags
- `concert_details/{id}.json` - Individual concert details with setlists (only for concerts with setlists)
- `artists.json` - All artists
- `venues.json` - All venues
- `songs.json` - All unique songs

**No-Cache Headers** (firebase.json):
- `**/*.html` → `Cache-Control: no-cache, no-store, must-revalidate`
- `data/**` → `Cache-Control: no-cache, no-store, must-revalidate`

**Cache-Busting**:
- JavaScript/CSS files use query string versioning: `?v=1761957023`
- Auto-updated by `scripts/update_cache_version.py` on each deployment

## Known Issues & Limitations

### 1. DOM Removal After Delete
**Issue**: When deleting a setlist, it remains visible on page until export completes (~2 min) or manual refresh.

**Root Cause**:
- Complex HTML structure: setlists rendered with wrapper divs, grouped by role (openers section), separated by `<hr>` elements
- Makes selective DOM removal difficult (can't just remove one div)
- Page loads from static JSON files anyway, so DOM changes are temporary

**Current Behavior**:
- Setlist deleted from Firestore immediately ✓
- Deployment triggered in background ✓
- Static JSON files updated in 2-3 minutes ✓
- Page still shows deleted setlist until manual refresh or auto-reload

**Workaround**:
- For last setlist: 2-minute auto-reload timer (wait for export to complete)
- For multiple setlists: User sees success message, can manually refresh
- Not a critical issue - data is correct in Firestore

**Code**: `website/concert.html` lines 447-462

### 2. Service Worker Caching (PARTIALLY MITIGATED)
**Issue**: Service Worker aggressively caches all files, can prevent updates from appearing.

**Mitigation**:
- Bump Service Worker cache version (CACHE_NAME) when deploying breaking changes
- Current version: v9
- Users must clear Service Worker cache after major updates

**Prevention**:
- Always increment cache version for breaking changes
- Document cache clearing procedure for users
- Consider automated Service Worker update notifications in future

**User Instructions**:
1. DevTools → Application → Clear storage → Clear site data
2. Close all browser tabs
3. Wait 10 seconds
4. Reopen browser

### 3. Artist Name Property Inconsistency
**Issue**: JSON export uses 'name' property, Firestore uses 'artist_name'.

**Why**: Historical - initial JSON export used 'name', Firestore schema uses 'artist_name'.

**Workaround**: Code checks both properties:
```javascript
const artistName = a.name || a.artist_name;
```

**Locations**: `website/js/concert.js` lines 166, 294-298

**Future**: Could standardize on one property name, but requires data migration.

### 4. Artist ID Type Mismatch
**Issue**: Firestore artist_id (Firestore document ID) ≠ setlist.fm artist_id (MusicBrainz ID)

**Why**: Two different systems:
- Firestore artists collection: Auto-generated document IDs
- setlist.fm API: Returns MusicBrainz IDs

**Impact**: Can't match artists by ID alone

**Solution**: Export script matches by artist_name instead of artist_id

**Code**: `scripts/export_to_web.py` lines 179-180, 209

## Pending Items

### From Previous Sessions (NOT STARTED)

**1. Old Format Setlist Cleanup**
- **Count**: 60 concerts
- **Issue**: Old-format setlist documents exist (document ID = concertId, no artist_name field) alongside newer multi-artist format
- **Impact**: Data duplication, confusion
- **Solution**: Create cleanup script to delete old format when newer versions exist
- **Priority**: Medium (data hygiene)

**2. Simplify Setlist Lookup Scripts**
- **Issue**: Multiple overlapping scripts exist:
  - `fetch_setlists.py` (old SQLite version - deprecated)
  - `fetch_setlists_enhanced.py` (main Firestore version)
  - `fetch_missing_setlists.py`
  - `fetch_missing_setlists_with_rotation.py`
- **Solution**: Consolidate into single script with options for:
  - Initial fetch
  - Missing only
  - API key rotation
- **Priority**: Low (convenience)

### New Items
**None** - All requested functionality from session handoff is complete and working!

## Testing Checklist

### Full End-to-End Flow

**1. Submit Setlist with Openers**:
- [ ] Go to concert without setlist (e.g., 1230)
- [ ] Click "Submit Setlist" button
- [ ] Enter headliner's setlist.fm URL
- [ ] Select all artists when prompted (headliner + openers)
- [ ] Submit
- [ ] Verify success message shows
- [ ] Check Firestore: All setlists created with correct doc IDs
- [ ] Check Firestore: Concert's artists array updated with all artists
- [ ] Wait 2-3 minutes for export/deployment
- [ ] Refresh page
- [ ] Verify: All setlists visible, tour name shown (if available), delete buttons visible

**2. Delete Individual Setlist**:
- [ ] Go to concert with multiple setlists (e.g., 938)
- [ ] Click delete button on one setlist (not the last one)
- [ ] Confirm deletion in dialog
- [ ] Verify: Success message appears
- [ ] Note: Setlist still visible on page (expected)
- [ ] Wait 2-3 minutes OR manually refresh
- [ ] Verify: Setlist removed from page
- [ ] Check Firestore: Setlist document deleted
- [ ] Check Firestore: Concert still has has_setlist=true

**3. Delete Last Setlist**:
- [ ] Go to concert with one setlist
- [ ] Click delete button
- [ ] Confirm deletion
- [ ] Verify: Message shows "2-min auto-reload"
- [ ] Wait 2 minutes (or refresh manually)
- [ ] Verify: Page shows "Submit Setlist" form
- [ ] Check Firestore: No setlists for concert
- [ ] Check Firestore: Concert has has_setlist=false

**4. Verify Delete Buttons After Refresh**:
- [ ] Go to concert with setlists
- [ ] Hard refresh (Cmd+Shift+R or Ctrl+Shift+R)
- [ ] Verify: Delete buttons appear immediately
- [ ] Check console: Should see debug messages from setupDeleteButtons

### Debugging Checklist

**Console Messages** (concert with setlists):
```
Admin status checked: Is admin
[Auth callback] isOwner: true
[Auth callback] Setting up delete buttons and observer
[setupDeleteButtons] Found 3 delete buttons
[setupDeleteButtons] Showing button for: Brad Paisley
[setupDeleteButtons] Showing button for: Chris Lane
[setupDeleteButtons] Showing button for: Riley Green
[MutationObserver] Detected X mutations
```

**If Delete Buttons Don't Appear**:
1. Check console for version: Should be `v=1761957023`
2. If seeing old version (v=1761875488), clear Service Worker cache
3. Check `isOwner()` in console: Should return `true`
4. Check if logged in as admin user
5. Verify Service Worker cache version is v9

**If Deleted Setlist Still Shows**:
1. Wait 2-3 minutes for export to complete
2. OR manually refresh page
3. Check Firestore to confirm deletion
4. If Firestore shows deleted but page shows it: Check for stale JSON file manually

## Debug Console Messages

When viewing a concert page with setlists, console shows:

```javascript
// Service Worker installation
[ServiceWorker] Installing...
[ServiceWorker] Caching static assets
[ServiceWorker] Skip waiting
[ServiceWorker] Activating...
[ServiceWorker] Claiming clients

// File versions being loaded
concert-photos.js?v=1761957023:251 Loading photos...
auth.js?v=1761957023:31 Admin status checked: Is admin

// Delete button setup (if admin)
concert.html:479 [Auth callback] isOwner: true
concert.html:484 [Auth callback] Setting up delete buttons and observer
concert.html:403 [setupDeleteButtons] Found 3 delete buttons
concert.html:408 [setupDeleteButtons] Showing button for: Brad Paisley
concert.html:408 [setupDeleteButtons] Showing button for: Chris Lane
concert.html:408 [setupDeleteButtons] Showing button for: Riley Green

// MutationObserver detecting DOM changes
concert.html:490 [MutationObserver] Detected 2 mutations
concert.html:403 [setupDeleteButtons] Found 3 delete buttons
```

**Debug logging intentionally left in place** per user request for future troubleshooting.

## Deployment Commands

### Full Deployment (Recommended)
```bash
./deploy.sh
```
**What it does**:
1. Updates cache versions (runs `update_cache_version.py`)
2. Exports Firestore data to JSON (runs `export_to_web.py`)
3. Deploys to Firebase Hosting

### Manual Step-by-Step
```bash
# 1. Update cache-busting versions
python3 scripts/update_cache_version.py

# 2. Export data from Firestore
python3 scripts/export_to_web.py

# 3. Deploy to Firebase
firebase deploy --only hosting

# 3a. Force deploy if hosting has stale cache
firebase deploy --only hosting --force
```

### Deploy Cloud Functions
```bash
firebase deploy --only functions
```

### Verify Deployment
```bash
# Check deployed version
curl -s 'https://earplugs-and-memories.web.app/concert.html' | grep -o "v=[0-9]*" | head -1

# Check Service Worker version
curl -s 'https://earplugs-and-memories.web.app/service-worker.js' | head -5

# Expected output:
# v=1761957023
# // Service Worker for Earplugs & Memories PWA
# // Version: 1.0.8
# const CACHE_NAME = 'earplugs-memories-v9';
```

## Git Commits from This Session

**In chronological order**:

1. **5faaa90** - Fix delete button visibility with MutationObserver
   - Added `setupDeleteButtons()` function
   - Added MutationObserver to detect new buttons
   - Prevents duplicate handler attachment

2. **06860c9** - Fix page reload timing when deleting last setlist
   - Changed immediate reload to 2-minute timer
   - Different success messages for last vs multiple setlists
   - Gives time for export to complete

3. **73dc503** - Auto-delete stale concert detail files on export
   - Scans for existing detail files after export
   - Deletes files for concerts without setlists
   - Logs deleted files for visibility

4. **61c6bd4** - Bump Service Worker cache version to force update
   - Service Worker: v8 → v9
   - All HTML: v=1761957023
   - Fixed deployment caching issues

**To view full commit history**:
```bash
git log --oneline --since="2025-10-31" --until="2025-11-01"
```

## Important Files Reference

### Configuration
- **firebase.json** - Firebase Hosting config, no-cache headers for HTML/data
- **firestore.rules** - Security rules for Firestore
- **.firebaserc** - Firebase project configuration

### Cloud Functions
- **functions/index.js** - Main Cloud Functions:
  - `processSetlistApproval` - Creates setlists, adds artists to concert
  - `triggerDeploy` - Triggers GitHub Actions for export/deploy
  - `fetchSetlistWithOpeners` - HTTP endpoint to fetch all setlists for venue/date
- **functions/package.json** - Dependencies (Node.js 20)

### Frontend Entry Points
- **website/index.html** - Home page
- **website/concerts.html** - Concert list
- **website/concert.html** - Individual concert detail page (MOST MODIFIED)
- **website/add-concert.html** - Admin add concert form
- **website/admin-setlists.html** - Pending setlist approvals

### Key JavaScript Modules
- **website/js/auth.js** - Authentication, admin checking (`isOwner()`, `checkAdminStatus()`)
- **website/js/concert.js** - Concert detail rendering, multi-setlist support
- **website/js/setlist-submission.js** - Setlist submission workflow, auto-approval
- **website/js/firebase-config.js** - Firebase initialization

### Scripts
- **scripts/export_to_web.py** - Main export script (Firestore → JSON)
- **scripts/update_cache_version.py** - Auto-generates cache-busting versions
- **deploy.sh** - One-click deployment wrapper

### Service Worker
- **website/service-worker.js** - PWA service worker, caches static assets

## Architecture Overview

### Data Flow
```
┌─────────────────┐
│ User Submits    │
│ Setlist URL     │
└────────┬────────┘
         │
         v
┌─────────────────────────────────┐
│ Firestore                       │
│ pending_setlist_submissions     │
│ (status: approved if admin)     │
└────────┬────────────────────────┘
         │
         v (onUpdate trigger)
┌─────────────────────────────────┐
│ Cloud Function:                 │
│ processSetlistApproval          │
│ 1. Fetch from setlist.fm        │
│ 2. Find all setlists (openers)  │
│ 3. Create setlist docs          │
│ 4. Add artists to concert       │
│ 5. Trigger deployment           │
└────────┬────────────────────────┘
         │
         v
┌─────────────────────────────────┐
│ GitHub Actions                  │
│ (via repository_dispatch)       │
│ 1. Checkout code                │
│ 2. Run export_to_web.py         │
│ 3. Deploy to Firebase Hosting   │
└────────┬────────────────────────┘
         │
         v
┌─────────────────────────────────┐
│ Static JSON Files               │
│ website/data/                   │
│ - concerts.json                 │
│ - concert_details/{id}.json     │
│ - artists.json, etc.            │
└────────┬────────────────────────┘
         │
         v
┌─────────────────────────────────┐
│ Firebase Hosting (CDN)          │
│ Users load static files         │
│ No-cache headers for HTML/data  │
└─────────────────────────────────┘
```

### Document ID Logic
```javascript
// Determine setlist document ID
if (existingSetlistForThisArtist) {
  // Update existing
  docId = existingSetlistId;
} else if (otherArtistHasSetlist) {
  // Multi-artist format
  docId = `${concertId}-${artistSlug}`;
} else {
  // First/only setlist
  docId = concertId;
}

// Examples:
// Concert 938 (Brad Paisley + openers):
// - "938" (Brad Paisley, first submitted)
// - "938-chris-lane" (Chris Lane, second artist)
// - "938-riley-green" (Riley Green, third artist)
```

## Next Session Recommendations

### High Priority
1. **Test full end-to-end flow** on a concert you care about
2. **Monitor for any issues** with the new features
3. **Consider removing debug logging** if console gets too noisy

### Medium Priority
4. **Old format setlist cleanup** - 60 concerts have duplicate data
5. **Script consolidation** - Simplify the 4 different setlist fetch scripts

### Low Priority
6. **Improve DOM removal** after delete (nice-to-have, current behavior is acceptable)
7. **Standardize artist name property** (consolidate 'name' vs 'artist_name')

### Questions to Consider
- Are tour names displaying correctly on all concerts?
- Should we add tour name to concert list view?
- Do opener roles need manual review/override capability?
- Should we auto-generate artist pages for new artists?

## Session Metadata

**Date**: October 31, 2025 (Halloween! 🎃)

**Duration**:
- Started: ~7:30 PM EST
- Ended: ~8:30 PM EST
- Total: ~1 hour

**User**: Jay (akalbfell@gmail.com)

**Status at End**: ✅ ALL CORE FEATURES WORKING
- ✅ Tour name capture
- ✅ Automatic opener detection
- ✅ Delete setlist functionality
- ✅ Export script improvements
- ✅ Service Worker cache fixed

**Remaining Work**: Only cleanup tasks (old format setlists, script consolidation)

---

## Quick Start for Next Session

```bash
# Check current deployment
curl -s 'https://earplugs-and-memories.web.app/concert.html' | grep -o "v=[0-9]*" | head -1

# Should see: v=1761957023

# If you make changes and want to deploy:
./deploy.sh

# To test locally:
firebase serve --only hosting

# To view Cloud Function logs:
firebase functions:log

# To check Firestore data for a concert:
python3 -c "
from google.cloud import firestore
import os
os.environ['GOOGLE_CLOUD_PROJECT'] = 'earplugs-and-memories'
db = firestore.Client()
setlists = list(db.collection('setlists').where('concert_id', '==', '938').stream())
for s in setlists:
    data = s.to_dict()
    print(f'{s.id}: {data.get(\"artist_name\")} ({data.get(\"song_count\")} songs)')
"
```

---

**End of Session Handoff**
