# Session Handoff Document - October 29, 2025

## Executive Summary

Today's session completed the setlist.fm integration work and resolved several critical bugs. The system now successfully fetches setlists from setlist.fm API, processes submissions via web form, and deploys automatically via GitHub Actions.

**Key Achievements:**
- ✅ Completed batch 3 setlist fetch (759 concerts processed)
- ✅ Total setlists in database: 542 concerts (42.5% coverage)
- ✅ Fixed web form submission workflow
- ✅ Fixed GitHub Actions auto-deployment
- ✅ Fixed cache issues for JSON data
- ✅ Fixed URL encoding for setlist.fm search links
- ✅ Cleaned up Dead & Company artist name issues

---

## What Was Done Today

### 1. Completed Setlist.fm Integration (Batch 3)

**Context:**
Previous session had completed batches 1 and 2. Batch 3 was started but hit API rate limits.

**What We Did:**
- Switched API key from `_Q380wqoYXFLsXALU_vlNSUTjwy7j7KQ6Bx9` to `DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE`
- Completed batch 3: processed 759 concerts (final batch)
- Success rate: 217/759 (28.6%) - lower than batch 1 because older concerts

**Results:**
- Batch 1: 241/300 concerts (80% success)
- Batch 2: 0/59 concerts (0% success - all special events)
- Batch 3: 217/759 concerts (28.6% success)
- **Total: 458/1,118 concerts found on setlist.fm**
- **Total concerts with setlists: 542** (includes some manually added)
- **Total unique songs: 5,565**

**Files Modified:**
- `scripts/fetch_setlists_enhanced.py` - API key updated
- All data JSON files exported and deployed

**Git Commits:**
- `a8df1f0` - Add batch 3 setlist data (296 additional setlists from 217 concerts)

---

### 2. Fixed Artist Name: Dead and Company → Dead & Company

**Issue:**
17 Dead and Company concerts had artist name "Dead and Company" (with "and") but setlist.fm uses "Dead & Company" (with ampersand). This prevented setlist matching during automated fetch.

**Solution:**
Updated all 17 concerts in Firestore to use "Dead & Company".

**Affected Concerts:**
- 659, 660, 701, 702, 762, 798, 833, 834, 918, 953, 957, 982, 1093, 1094, 1171, 1172, 1173

**Git Commits:**
- `e71e756` - Fix artist name: Dead and Company → Dead & Company (17 concerts)

---

### 3. Fixed URL Encoding for setlist.fm Search Links

**Issue:**
The "Find This Show on setlist.fm" button was not properly encoding special characters. For "Dead & Company", the "&" was interpreted as URL parameter separator, so only "Dead" was searched.

**Solution:**
Changed from manual space replacement to proper `encodeURIComponent()` in JavaScript:
```javascript
// Before
const searchQuery = `${concert.artists} ${concert.venue} ${concert.date}`.replace(/ /g, '+');
findSetlistLink.href = `https://www.setlist.fm/search?query=${searchQuery}`;

// After
const searchQuery = `${concert.artists} ${concert.venue} ${concert.date}`;
findSetlistLink.href = `https://www.setlist.fm/search?query=${encodeURIComponent(searchQuery)}`;
```

**Files Modified:**
- `website/js/concert.js:333-334`

**Git Commits:**
- `7717040` - Fix setlist.fm search link URL encoding for special characters

---

### 4. Disabled JSON Data Caching

**Issue:**
JSON data files were being cached for 5-10 minutes, so users wouldn't see updates after deployments.

**Solution:**
Changed Cache-Control headers in `firebase.json`:
```json
// Before
"value": "public, max-age=300, s-maxage=600"

// After
"value": "no-cache, no-store, must-revalidate"
```

**Files Modified:**
- `firebase.json`

**Git Commits:**
- `d5cbfd4` - Disable caching for JSON data files to ensure fresh content

---

### 5. Fixed Web Form Setlist Submission

**Issue:**
Setlist submissions via web form were creating empty records in Firestore (all fields were `None/null`).

**Root Cause:**
The Cloud Function was working correctly and processing submissions automatically. However, there was a type mismatch - `concertId` was being saved as a string instead of integer.

**Solution:**
Added debugging logs and changed `concertId` to use `parseInt()`:
```javascript
const submissionData = {
    concertId: parseInt(concertId),  // Changed from: concertId: concertId
    setlistfmUrl: url,
    setlistfmId: setlistId,
    submittedByEmail: submitterEmail,
    submittedByName: submitterName,
    submittedAt: new Date(),
    status: status,
    setlistData: setlistData
};
```

**Testing:**
Submitted concert 1173 (Dead & Company) successfully:
- Setlist fetched from Cloud Function ✅
- Auto-approved for admin user ✅
- Saved to Firestore with all data ✅
- 19 songs captured ✅

**Files Modified:**
- `website/js/setlist-submission.js` - Added debugging + parseInt fix

**Git Commits:**
- `4929520` - Add debugging to setlist submission form and fix concertId type

---

### 6. Fixed GitHub Actions Auto-Deployment

**Issue:**
GitHub Actions workflow wasn't triggering automatically after setlist submissions.

**Root Cause:**
Event type mismatch:
- Cloud Function sends: `deploy-setlist`
- Workflow was listening for: `setlist-updated`

**Solution:**
Updated workflow to listen for correct event type:
```yaml
on:
  repository_dispatch:
    types: [deploy-setlist]  # Changed from: types: [setlist-updated]
```

**Files Modified:**
- `.github/workflows/deploy-on-setlist-update.yml`

**How It Works Now:**
1. User submits setlist via website form
2. Cloud Function validates and processes (auto-approves for admins)
3. Cloud Function creates setlist document in Firestore
4. Cloud Function triggers GitHub Actions with `deploy-setlist` event
5. GitHub Actions runs: export data → deploy to Firebase
6. Changes visible on website in ~2-3 minutes

**Git Commits:**
- `ce417e2` - Fix GitHub Actions workflow trigger and export Dead & Company setlist

---

### 7. Fixed Dead & Company Artist Name Duplicates

**Issue:**
Concerts 1036, 1038, 1039 had malformed artist data:
- Concert 1036: "DEAD: Dead" + "Company" (2 artists)
- Concert 1038: "DEAD:  Dead" + "Company" (2 artists)
- Concert 1039: "Dead & Company" + "Company" (2 artists)

This caused website to display: "Dead & Company, Company"

**Solution:**
Python script to clean up:
1. Remove "DEAD:" prefix
2. Convert "Dead" to "Dead & Company"
3. Remove duplicate "Company" artist entries
4. Change role from "festival_performer" to "headliner"

**Git Commits:**
- `29ee776` - Fix Dead & Company artist name duplicates in concerts 1036, 1038, 1039

---

## Current System State

### Database Statistics
- **Total concerts:** 1,275
- **Concerts with setlists:** 542 (42.5%)
- **Concerts without setlists:** 733 (57.5%)
- **Unique songs:** 5,565
- **Total setlist documents:** 542+

### API Keys Status
All three setlist.fm API keys exhausted their daily quotas (1,440 requests each):
1. `_Q380wqoYXFLsXALU_vlNSUTjwy7j7KQ6Bx9` - Used in batches 1-2, EXHAUSTED
2. `DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE` - Used in batch 3, EXHAUSTED
3. `Uo48MPdBZN5ujA_PJKkyeKYyiMzOaf-kd4gi` - Not yet used, AVAILABLE

**Note:** API quotas reset at midnight UTC (likely already reset by tomorrow)

### Remaining Work
- 733 concerts still need setlists (many are special events/benefits that won't be on setlist.fm)
- 17 Dead & Company concerts with corrected artist names need setlists fetched

---

## Next Steps for Tomorrow

### 1. Fetch Dead & Company Setlists (Priority)

The 17 Dead & Company concerts now have correct artist names but still need setlists.

**Concert IDs:** 659, 660, 701, 702, 762, 798, 833, 834, 918, 953, 957, 982, 1093, 1094, 1171, 1172, 1173

**How to fetch:**
```bash
# Create a script to fetch just these 17 concerts
python3 -c "
from scripts.fetch_setlists_enhanced import *

concert_ids = [659, 660, 701, 702, 762, 798, 833, 834, 918, 953, 957, 982, 1093, 1094, 1171, 1172, 1173]

# Initialize
db = init_firebase()
client = SetlistFMClient('DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE')  # Use fresh API key

for concert_id in concert_ids:
    print(f'Fetching setlist for concert {concert_id}...')
    concert_ref = db.collection('concerts').document(str(concert_id))
    concert = concert_ref.get()

    if concert.exists:
        concert_data = concert.to_dict()
        fetch_setlists_for_concert(db, client, concert_id, concert_data, detect_openers=True)
"
```

Or create a dedicated script `scripts/fetch_deadco_setlists.py` with proper error handling.

**Expected Result:** Should find 15-16 of the 17 concerts (some might not be on setlist.fm)

---

### 2. Review Concerts Without Setlists

**Goal:** Identify which of the 733 remaining concerts are worth pursuing.

**Categories:**
1. **Regular concerts** - Should be on setlist.fm, try fetching
2. **Special events** - Won't be on setlist.fm (benefits, conversations, etc.)
3. **Manual entry needed** - Have setlist info but need manual submission

**How to analyze:**
```bash
python3 -c "
import json

concerts = json.load(open('website/data/concerts.json'))
no_setlist = [c for c in concerts if not c.get('hasSetlist')]

# Group by patterns
special_events = []
regular_concerts = []

for c in no_setlist:
    name = c.get('name', '')
    artists = c.get('artists', '')

    # Check for special event keywords
    if any(word in name.lower() or word in artists.lower() for word in
           ['benefit', 'light of day', 'stand up for heroes', 'conversation',
            'storyteller', 'in conversation', 'today show', 'sphere']):
        special_events.append(c)
    else:
        regular_concerts.append(c)

print(f'Special events (probably not on setlist.fm): {len(special_events)}')
print(f'Regular concerts (might be on setlist.fm): {len(regular_concerts)}')
print(f'\nSample regular concerts to try:')
for c in regular_concerts[:10]:
    print(f'  Concert {c[\"id\"]}: {c[\"artists\"]} - {c[\"date\"]}')
"
```

---

### 3. Optional: Batch Fetch Remaining Concerts

If you want to try fetching more setlists:

```bash
# Fetch all remaining concerts without setlists
python3 scripts/fetch_setlists_enhanced.py --detect-openers 2>&1 | tee fetch_log_remaining.txt

# This will:
# - Skip concerts that already have setlists
# - Try to find setlists for the 733 remaining concerts
# - Use opener detection
# - Take ~3-4 hours with rate limiting
```

**Note:** Success rate will be low (~15-20%) since most remaining concerts are:
- Special events not on setlist.fm
- Older concerts with poor documentation
- Small venue shows

---

### 4. Export and Deploy

After fetching new setlists:

```bash
# 1. Export data from Firestore to JSON
python3 scripts/export_to_web.py

# 2. Commit changes
git add -A
git commit -m "Add setlists for Dead & Company and other concerts"
git push

# 3. Deploy to Firebase
firebase deploy --only hosting
```

Or just push to GitHub and let the manual workflow trigger handle it.

---

## System Architecture Summary

### Data Flow

#### Setlist Submission via Web Form:
```
User submits URL → JavaScript validates → Cloud Function fetches data →
Firestore (pending_setlist_submissions) → Cloud Function processes →
Firestore (setlists collection) → Cloud Function triggers GitHub Actions →
GitHub Actions runs export + deploy → Website updated
```

#### Automated Fetch:
```
Python script → setlist.fm API → Firestore (setlists collection) →
Manual: export_to_web.py → JSON files → Deploy → Website updated
```

#### Manual Concert Edits:
```
iOS/Android app → Firestore (concerts collection) →
Manual: export_to_web.py → JSON files → Deploy → Website updated
```

### Key Files

**Python Scripts:**
- `scripts/fetch_setlists_enhanced.py` - Main fetch script with co-headliner + opener support
- `scripts/setlistfm_client.py` - API client with rate limiting
- `scripts/export_to_web.py` - Export Firestore → JSON files
- `scripts/process_approved_setlists.py` - Process pending submissions (backup, not needed now)
- `scripts/wipe_all_setlists.py` - Nuclear option to wipe all setlist data

**JavaScript Files:**
- `website/js/setlist-submission.js` - Web form submission logic
- `website/js/concert.js` - Concert page display logic

**Cloud Functions:**
- `functions/index.js` - Auto-processes approved setlist submissions, triggers GitHub Actions

**GitHub Actions:**
- `.github/workflows/deploy-on-setlist-update.yml` - Auto-deploys on setlist submission
- `.github/workflows/deploy.yml` - Manual deployment workflow

**Configuration:**
- `firebase.json` - Hosting config with cache headers
- `website/data/*.json` - Static JSON files served to website

---

## Important Notes & Gotchas

### 1. API Rate Limits
- Each API key limited to 1,440 requests/day
- 4-second delay between requests (very conservative)
- ~6 hours to process 1,000 concerts
- Quotas reset at midnight UTC

### 2. Concert ID vs String
- Firestore uses string document IDs ("1173")
- Some fields use integers (concert_id: 1173)
- Always use `str()` or `parseInt()` when converting

### 3. Artist Name Normalization
The `setlistfm_client.py` cleans artist names before searching:
- Removes parenthetical notes: "Bruce Springsteen (Final Show)" → "Bruce Springsteen"
- Removes opener notation: "Artist w/ Opener" → "Artist"
- Removes band suffixes: "Bruce Springsteen & the E Street Band" → "Bruce Springsteen"

**BUT it does NOT normalize "And" vs "&"** - this must be done manually in Firestore.

### 4. Cache Behavior
- HTML files: Browser cached normally
- JSON data files: **no-cache, no-store, must-revalidate** (always fresh)
- Images/CSS/JS: Browser cached normally

### 5. GitHub Actions Secrets Required
- `GOOGLE_APPLICATION_CREDENTIALS` - Service account JSON for Firestore access
- `FIREBASE_TOKEN` - Firebase CLI token for deployment

### 6. Opener Detection
The opener detection is probabilistic with confidence scoring:
- **100% confidence:** Artist appears as guest in headliner's setlist
- **85% confidence:** Song count < 50% of headliner + other factors
- **50% confidence:** Basic heuristics (fewer songs than headliner)

Always review HIGH confidence openers manually.

---

## Debugging Tips

### Check Setlist Submission Status
```bash
python3 -c "
import firebase_admin
from firebase_admin import credentials, firestore
import os

try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'earplugs-and-memories',
    })

db = firestore.client()

# Check pending submissions
pending = db.collection('pending_setlist_submissions').where('status', '==', 'approved').stream()
print('Approved submissions waiting to process:')
for p in pending:
    data = p.to_dict()
    print(f\"  {p.id}: Concert {data.get('concertId')}\")

# Check recent setlists
setlists = db.collection('setlists').order_by('created_at', direction='DESCENDING').limit(5).stream()
print('\nRecent setlists:')
for s in setlists:
    data = s.to_dict()
    print(f\"  Concert {data.get('concert_id')}: {data.get('song_count')} songs\")
"
```

### Check GitHub Actions Runs
https://github.com/Former-Stranger/concert-website/actions

### View Cloud Function Logs
```bash
firebase functions:log
```

Or in Firebase Console:
https://console.firebase.google.com/project/earplugs-and-memories/functions

### Test Setlist.fm API
```bash
python3 scripts/setlistfm_client.py DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE
```

---

## Quick Reference Commands

### Fetch Setlists
```bash
# Fetch all concerts without setlists
python3 scripts/fetch_setlists_enhanced.py --detect-openers

# Fetch with limit
python3 scripts/fetch_setlists_enhanced.py --limit 100 --detect-openers

# Fetch specific concerts (modify script)
# See "Next Steps" section above
```

### Export and Deploy
```bash
# Export Firestore → JSON
python3 scripts/export_to_web.py

# Deploy to Firebase
firebase deploy --only hosting

# Or combined
python3 scripts/export_to_web.py && firebase deploy --only hosting
```

### Database Operations
```bash
# Wipe all setlist data (DESTRUCTIVE!)
python3 scripts/wipe_all_setlists.py --dry-run  # Preview
python3 scripts/wipe_all_setlists.py --confirm  # Execute

# Process approved submissions (usually automatic)
python3 scripts/process_approved_setlists.py
```

### Git Operations
```bash
# Standard workflow
git add -A
git commit -m "Description of changes"
git push

# Check status
git status
git log --oneline -10
```

---

## Contact & Resources

**GitHub Repository:**
https://github.com/Former-Stranger/concert-website

**Live Website:**
https://earplugs-and-memories.web.app

**Firebase Console:**
https://console.firebase.google.com/project/earplugs-and-memories

**setlist.fm API Documentation:**
https://api.setlist.fm/docs/1.0/index.html

**Previous Handoff Document:**
`SETLIST_INTEGRATION_HANDOFF.md` - Original integration plan and details

---

## Session End Status

**All work committed:** ✅ Yes
**All changes deployed:** ✅ Yes
**Tests passing:** ✅ Yes
**Ready for tomorrow:** ✅ Yes

**Total commits today:** 7
- a8df1f0 - Batch 3 setlist data
- e71e756 - Dead & Company name fix
- 7717040 - URL encoding fix
- d5cbfd4 - Cache headers fix
- 4929520 - Form submission debugging
- ce417e2 - GitHub Actions workflow fix
- 29ee776 - Duplicate artist name cleanup

**Next session priority:** Fetch setlists for the 17 Dead & Company concerts

---

*Document created: October 29, 2025*
*Session duration: ~4 hours*
*Primary focus: Complete setlist.fm integration and fix critical bugs*
