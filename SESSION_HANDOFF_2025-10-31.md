# Session Handoff - October 31, 2025

## Session Summary
Continued multi-artist setlist work and fixed several critical bugs related to auto-approval, UI interactions, and duplicate setlist creation.

---

## Issues Fixed This Session

### 1. Auto-Approval for Admin Setlist Submissions ✅
**Problem**: Admin users' setlist submissions were going to pending status instead of being auto-approved.

**Root Cause**:
- The `isOwner()` function is synchronous but relies on a cached variable set asynchronously
- All three submission code paths (single artist, multi-artist, update setlist) were using the synchronous `isOwner()` which returned `false` before the admin check completed

**Solution**:
- Created `checkIsAdmin()` async helper function that directly queries Firestore `admins` collection
- Updated all three submission paths to use `await checkIsAdmin()` instead of `isOwner()`
- Added `submittedBy` field with user UID to all submission documents
- Added console logging for debugging: shows user UID, admin status, and submission status

**Files Modified**:
- `website/js/setlist-submission.js`:
  - Lines 6-17: Added `checkIsAdmin()` helper
  - Line 100: Single-artist submission uses `await checkIsAdmin()`
  - Line 111: Added `submittedBy` field
  - Line 282: Multi-artist submission uses `await checkIsAdmin()`
  - Line 297: Added `submittedBy` field
  - Line 444: Update setlist uses `await checkIsAdmin()`
  - Line 456: Added `submittedBy` field

**Deployed**: Yes (cache version v=1761882967)

---

### 2. Update Setlist Button Not Working ✅
**Problem**: Clicking "Update Setlist" button didn't do anything.

**Root Cause**:
- `initUpdateSetlist()` was called immediately when module loaded
- Button is created asynchronously by `concert.js` after data loads
- Event listener was trying to attach to a button that didn't exist yet

**Solution**:
- Added `waitForButton()` promise in `initUpdateSetlist()` that polls for button existence with 100ms intervals
- Only attaches event listeners after button is confirmed to exist

**Files Modified**:
- `website/js/setlist-submission.js` (lines 341-354)

**Deployed**: Yes

---

### 3. Edit Concert Modal Closing When Highlighting Text ✅
**Problem**: When highlighting text in input fields, if the mouse release happened outside the modal content area (on the modal background), the modal would close.

**Root Cause**:
- Modal click handler was closing on any click event
- When dragging to select text, mousedown occurs on input, mouseup occurs on modal background
- This triggered the close handler even though user was just selecting text

**Solution**:
- Track where mousedown occurs using a flag
- Modal only closes if BOTH mousedown AND mouseup happen on modal background
- Also check for active text selection using `window.getSelection().toString()`

**Files Modified**:
- `website/concert.html` (lines 509-522)

**Deployed**: Yes

---

### 4. Duplicate Setlist Creation for Same Artist ✅
**Problem**: Resubmitting a setlist for the same artist created duplicate documents (e.g., concert 905 had both "905" and "905-o-a-r" for O.A.R.).

**Root Cause**:
- Cloud Function logic checked if ANY existing setlists exist
- Used multi-artist format whenever existing setlists found, even for same artist
- Should only use multi-artist format when DIFFERENT artists exist

**Solution**:
- Updated `processApprovedSetlist` to check if existing setlists are for different artist names
- Use `.some()` to check if any existing setlist has a different `artist_name`
- Only use multi-artist format if different artists detected

**Logic**:
- First submission for Artist A → docId = "concertId" (simple format)
- Resubmission for Artist A → docId = "concertId" (updates existing)
- First submission for Artist B on same concert → docId = "concertId-artist-b-slug" (multi-artist format)

**Files Modified**:
- `functions/index.js` (lines 262-269)

**Deployed**: Yes (Cloud Functions deployed)

**Cleanup**: Deleted duplicate setlist "905-o-a-r", kept "905"

---

## Issues Fixed in Continuation Session (Oct 31, 12:30 AM)

### ✅ Artist Name Editing Not Working Properly - FIXED
**Status**: RESOLVED

**Root Cause Identified**:
- Firestore was updating correctly ✓
- Export/deployment was triggered ✓
- Page did `window.location.reload()` immediately ✗
- Static JSON files hadn't regenerated yet (takes 2-5 minutes) ✗
- User saw stale data from old JSON files ✗

**Solution Implemented**:
- Created `reloadConcertFromFirestore()` function (concert.html:601-671)
- After saving edit, loads updated data directly from Firestore instead of page reload
- Updates header display in-place (artist, venue, city, state, festival)
- Shows changes to user instantly
- Still triggers export in background for static files
- Updated success message to explain export timing
- Falls back to page reload if Firestore read fails

**Files Modified**:
- `website/concert.html` (lines 601-671, 713, 716)
- Cache-busting version updated to v=1761884990

**Deployed**: Yes (commit 353edc7)

---

## Remaining Issues to Fix

### Priority 1: Tour Name Not Captured from Setlist.fm
**Status**: Not yet investigated

**User Report**:
- Concert 905 setlist was fetched from setlist.fm
- Tour name should have been captured but wasn't
- Need to store tour information when available

**Next Steps**:
1. Check if setlist.fm API returns tour data
2. Verify Cloud Function `fetchSetlist` extracts tour info
3. Add tour_name field to setlist documents
4. Update concert display to show tour name
5. Update export script to include tour data

---

### Priority 3: Opener Not Added to Concert When Submitting Headliner Setlist
**Status**: Not yet investigated

**User Report**:
- Submit headliner setlist for a show with an opener
- Multi-artist detection finds the opener and fetches their setlist
- Opener setlist is saved to database
- BUT: Opener is not added to the concert's artists array

**Suspected Cause**:
- Cloud Function creates setlist documents for both artists
- But doesn't update the concert's `artists` array to include opener
- Concert metadata not being synchronized with setlist data

**Next Steps**:
1. Review `processApprovedSetlist` Cloud Function
2. Add logic to update concert's `artists` array when new artist setlist is added
3. Determine correct artist role (opener vs headliner vs co-headliner)
4. Ensure export script reflects updated artist list

---

## Data Cleanup Needed

### Old Format Setlists (60 concerts)
There are 60 concerts with old-format setlist documents (document ID = concertId, no artist_name field) that also have newer multi-artist format setlists. These old documents should be cleaned up.

**To view list**:
```bash
python3 -c "
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {'projectId': 'earplugs-and-memories'})
db = firestore.client()

setlists = db.collection('setlists').stream()
for setlist in setlists:
    data = setlist.to_dict()
    if data.get('artist_name') is None and '-' not in setlist.id:
        concert_id = data.get('concert_id')
        newer_setlists = db.collection('setlists').where('concert_id', '==', concert_id).stream()
        newer_count = sum(1 for s in newer_setlists if s.id != setlist.id)
        if newer_count > 0:
            print(f'Concert {concert_id}: old doc \"{setlist.id}\" - has {newer_count} newer versions')
"
```

**Recommended Action**: Create a cleanup script to delete old format setlists when newer versions exist.

---

## Technical Notes

### Cache-Busting Version
Current deployed version: `v=1761882967`
- All JavaScript files use this version
- Hard refresh required for users to get latest code

### Deployment Process Issues
- Sometimes `firebase deploy --only hosting` doesn't properly upload all files
- concert.html specifically seems to have caching issues
- Recommendation: Always verify deployed version with curl after deployment
- Command: `curl -s 'https://earplugs-and-memories.web.app/concert.html' | grep -o "v=[0-9]*" | head -1`

### Auto-Approval Debugging
Console logs now show:
- `[Setlist Submission] Current user: <UID>`
- `[Setlist Submission] User is owner: <true/false>`
- `[Setlist Submission] Status: <approved/pending>`

Similar logs for multi-artist and update setlist flows.

---

## Files Changed This Session

### JavaScript
- `website/js/setlist-submission.js` - Auto-approval fixes, submittedBy field, waitForButton logic
- `website/concert.html` - Modal mousedown tracking, cache-busting version updates

### Cloud Functions
- `functions/index.js` - Fixed duplicate setlist creation logic

### Data
- Deleted duplicate setlist document `905-o-a-r`
- Re-exported all static JSON files (991 concert details now)

---

## Commits Created
1. `fa074df` - Fix modal closing when dragging text selection outside content area
2. `76a483e` - Fix three UI issues with setlist submission and concert editing
3. `1893766` - Fix duplicate setlist creation for same artist

---

## Testing Recommendations

Before continuing with remaining issues:

1. **Test Auto-Approval**: Submit a setlist and verify it auto-approves with console logs showing correct UID
2. **Test Update Setlist**: Click Update Setlist button and verify it works
3. **Test Modal Text Selection**: Highlight text in edit modal and release mouse outside - modal should stay open
4. **Test Duplicate Prevention**: Resubmit a setlist for same artist - should update existing, not create duplicate

---

## Next Session Priorities

1. **Tour Name Capture** (High Priority)
   - Enhances setlist data completeness
   - Relatively straightforward if API provides the data
   - Check if setlist.fm API returns tour data
   - Add tour_name field to setlist documents
   - Update concert display to show tour name

2. **Opener Detection & Addition** (High Priority)
   - Affects multi-artist show accuracy
   - When submitting headliner setlist, opener's setlist is fetched but opener is not added to concert's artists array
   - Need concert metadata synchronization
   - Determine correct artist role assignment

3. **Old Setlist Cleanup** (Medium Priority)
   - Data hygiene issue
   - Can be batch processed with script
   - 60 concerts affected with old-format setlist documents

4. **Simplify Setlist Lookup Scripts** (Low Priority)
   - Multiple overlapping scripts exist: fetch_setlists.py (old SQLite version), fetch_setlists_enhanced.py (main Firestore version), fetch_missing_setlists.py, and fetch_missing_setlists_with_rotation.py
   - Should consolidate into single script with options for: initial fetch, missing only, API key rotation
   - Remove deprecated SQLite-based script
   - Add clear documentation on which script to use when

---

## Questions for Next Session

1. **Tour Names**: Do all setlists have tour data, or is it optional? Where should tour names be displayed?

2. **Opener Addition**: Should openers be automatically added to the concert when their setlist is detected, or should it require manual confirmation?

---

## End of Session
Date: October 31, 2025

**Initial Session** (~4:15am EST):
- All critical bugs fixed (auto-approval, update setlist button, modal highlighting, duplicate prevention)
- Three enhancement issues remained (artist editing, tour names, opener addition)

**Continuation Session** (12:30am - 12:50am EST):
- ✅ Fixed artist name editing to show changes immediately
- Added `reloadConcertFromFirestore()` function
- Deployed with cache version v=1761884990
- Added TODO for simplifying setlist lookup scripts

**Still Remaining**:
- Tour name capture from setlist.fm
- Opener addition to concert when multi-artist setlist detected
- Old setlist cleanup (60 concerts)
- Simplify setlist lookup scripts
