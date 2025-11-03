# Claude Handoff Document - Earplugs & Memories V1.0

**Last Updated**: November 3, 2024
**Version**: 1.0 (Out of Beta)
**Project**: Jason's Concert Archive - Personal concert tracking with setlist management

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Key Files and Directories](#key-files-and-directories)
4. [Data Flow](#data-flow)
5. [Critical Systems](#critical-systems)
6. [Development Workflow](#development-workflow)
7. [Common Tasks](#common-tasks)
8. [Known Issues and Solutions](#known-issues-and-solutions)
9. [Important Patterns](#important-patterns)
10. [Testing and Debugging](#testing-and-debugging)

---

## Project Overview

### What This Is
A Progressive Web App (PWA) for tracking concerts attended by Jason. Users can:
- View concert history with dates, venues, artists
- Import setlists from setlist.fm
- Upload and manage concert photos
- Track songs played across all concerts
- View artist and venue statistics

### Tech Stack
- **Frontend**: Vanilla JavaScript (ES6 modules), Tailwind CSS, HTML5
- **Backend**: Firebase (Firestore, Cloud Functions, Storage, Hosting, Auth)
- **Deployment**: GitHub Actions → Firebase Hosting
- **Data Pipeline**: Firestore (live) → Python export → Static JSON (deployed)

### Project Structure
```
concert-website/
├── website/              # Frontend static files
│   ├── data/            # Exported JSON (deployed, in Git)
│   ├── js/              # Client-side JavaScript modules
│   └── *.html           # Page templates
├── functions/           # Firebase Cloud Functions (Node.js)
├── scripts/             # Python maintenance scripts
└── .github/workflows/   # GitHub Actions automation
```

---

## Architecture

### Three-Layer System

```
┌─────────────────────────────────────────────┐
│  User Browser (PWA)                         │
│  - Reads static JSON from website/data/    │
│  - Service Worker for offline support       │
└─────────────────────────────────────────────┘
                    ↓ (reads)
┌─────────────────────────────────────────────┐
│  Firebase Hosting                           │
│  - Serves static HTML/JS/JSON               │
│  - CDN-distributed                          │
└─────────────────────────────────────────────┘
                    ↑ (deploys)
┌─────────────────────────────────────────────┐
│  GitHub Actions                             │
│  - Triggered by Cloud Functions             │
│  - Runs export_to_web.py                   │
│  - Deploys to Firebase Hosting             │
└─────────────────────────────────────────────┘
                    ↑ (triggers)
┌─────────────────────────────────────────────┐
│  Firebase Cloud Functions                   │
│  - processApprovedSetlist (imports)        │
│  - triggerDeploy (automation)              │
│  - updateSetlistStatuses (batch jobs)      │
└─────────────────────────────────────────────┘
                    ↓ (writes)
┌─────────────────────────────────────────────┐
│  Firestore Database (Source of Truth)      │
│  - concerts, setlists, artists, etc.       │
└─────────────────────────────────────────────┘
```

### Why This Architecture?
- **Static JSON**: Fast, cacheable, works offline, no database queries on client
- **Firestore**: Easy admin interface, real-time updates, structured data
- **Cloud Functions**: Server-side processing for setlist imports
- **GitHub Actions**: Automated deployment pipeline, version control

---

## Key Files and Directories

### Frontend (website/)

#### HTML Pages
| File | Purpose | Key Features |
|------|---------|--------------|
| `index.html` | Homepage | Stats dashboard, recent concerts |
| `concerts.html` | Concert list | Filterable table, status icons |
| `concert.html` | Concert detail | Setlist display, photo gallery, edit form |
| `artists.html` | Artist list | Performance counts, search |
| `artist.html` | Artist detail | Concert history, song statistics |
| `venues.html` | Venue list | Concert counts by venue |
| `venue.html` | Venue detail | Concerts at venue |
| `songs.html` | Song catalog | Play counts, cover detection |
| `add-concert.html` | Add concert form | Admin only, manual entry |
| `admin-setlists.html` | Setlist review | Approve/reject imported setlists |
| `help.html` | User guide | Instructions, FAQ |

#### JavaScript Modules (website/js/)
| File | Purpose | Exports |
|------|---------|---------|
| `firebase-config.js` | Firebase initialization | Firebase app instance |
| `auth.js` | Authentication | `initAuth()`, role management |
| `main.js` | Homepage logic | Stats display |
| `concerts.js` | Concert list page | `loadConcerts()`, filtering |
| `concert.js` | Concert detail page | Setlist display, edit form |
| `concert-photos.js` | Photo management | Upload, delete, display |
| `concert-notes.js` | Notes system | Add/edit/delete notes |
| `artist.js` | Artist page | Performance history |
| `venue.js` | Venue page | Venue history |
| `songs.js` | Songs page | Song catalog |
| `setlist-submission.js` | Setlist import | Parse setlist.fm URLs |

#### Data Files (website/data/)
**IMPORTANT**: These are auto-generated by `scripts/export_to_web.py`. Never edit manually!

| File/Directory | Contents | Updated When |
|----------------|----------|--------------|
| `concerts.json` | Concert list with summary data | Every export |
| `artists.json` | Artist list with show counts | Every export |
| `venues.json` | Venue list with show counts | Every export |
| `songs.json` | Song catalog with play counts | Every export |
| `stats.json` | Global statistics | Every export |
| `concert_details/*.json` | Individual concert full details | Every export |
| `artist_details/*.json` | Artist performance history | Every export |
| `venue_details/*.json` | Venue concert history | Every export |

#### Service Worker
| File | Purpose | Current Version |
|------|---------|-----------------|
| `service-worker.js` | PWA offline support, caching | v37 |

**Cache Strategy**:
- Static assets: Cache-first (HTML, JS, CSS)
- Data JSON: Network-first with cache fallback
- Firebase: Always network

### Backend (functions/)

#### Cloud Functions (functions/index.js)
| Function | Trigger | Purpose |
|----------|---------|---------|
| `processApprovedSetlist` | Firestore onCreate/onUpdate | Imports approved setlists from pending submissions |
| `triggerDeploy` | Firestore onUpdate | Triggers GitHub Actions when setlist is processed |
| `updateSetlistStatuses` | HTTPS | Batch update concert setlist statuses |

**Key Implementation Details**:

**processApprovedSetlist** (Lines 136-411):
- Triggered when `pending_setlist_submissions` document is approved
- Parses setlist.fm data structure
- **CRITICAL**: Uses artist-specific document ID format `{concertId}-{artistSlug}` to prevent race conditions
- Handles multi-artist concerts (headliners + openers)
- Creates/updates setlist in `setlists` collection
- Updates concert's artists array with fuzzy matching
- Updates song play counts

**triggerDeploy** (Lines 703-764):
- Watches `pending_setlist_submissions` for `processed: true` flag
- Triggers GitHub Actions via `repository_dispatch` API
- **Enables automation**: Setlist import → export → deploy (2-3 minutes)

### Scripts (scripts/)

#### Data Export
| Script | Purpose | When to Run |
|--------|---------|-------------|
| `export_to_web.py` | Main export - Firestore → JSON | Auto via GitHub Actions |
| `export_firestore_backup.py` | Full Firestore backup | Manual backups |
| `backup_all.sh` | Complete backup script | Monthly recommended |

#### Maintenance
| Script | Purpose | When to Run |
|--------|---------|-------------|
| `find_duplicate_artists.py` | Find/merge duplicate artists | When duplicates detected |
| `update_cache_version.py` | Increment service worker cache | Every deployment (auto) |
| `init_setlist_status.py` | Initialize setlist_status field | One-time migration |
| `detect_openers.py` | Find concerts with multiple artists | Analysis |

#### Analysis
| Script | Purpose |
|--------|---------|
| `check_artist_duplicates.py` | List potential duplicates |
| `preview_duplicates.py` | Preview merge plan |
| `execute_merge_plan.py` | Execute artist merge |

### Configuration Files

| File | Purpose | Important Settings |
|------|---------|-------------------|
| `firebase.json` | Firebase config | Hosting rewrites, function settings |
| `.firebaserc` | Firebase project | `earplugs-and-memories` |
| `functions/package.json` | Cloud Functions deps | Node.js 20, firebase-admin, node-fetch |
| `manifest.json` | PWA manifest | App name, icons, theme colors |
| `.github/workflows/deploy.yml` | CI/CD pipeline | Auto-deploy on `deploy-setlist` event |

---

## Data Flow

### Complete Setlist Import Flow

```
1. User submits setlist URL on concert.html
   ↓
2. setlist-submission.js parses URL, creates pending_setlist_submissions doc
   ↓
3. Admin reviews on admin-setlists.html, clicks Approve
   ↓
4. Document updated with approved: true
   ↓
5. processApprovedSetlist Cloud Function triggers
   ↓
6. Function processes setlist:
   - Creates setlist document (id: {concertId}-{artistSlug})
   - Updates concert.artists array (fuzzy matching)
   - Updates song play counts
   - Marks submission as processed: true
   ↓
7. triggerDeploy Cloud Function detects processed: true
   ↓
8. Function calls GitHub API with repository_dispatch event
   ↓
9. GitHub Actions workflow (.github/workflows/deploy.yml) triggers:
   - Updates service worker cache version
   - Runs export_to_web.py (Firestore → JSON)
   - Deploys to Firebase Hosting
   ↓
10. Site updates in 2-3 minutes
```

### Data Consistency Model

**Source of Truth**: Firestore Database

**Read Path**:
- Website reads from static JSON files (fast, cacheable)
- Admin pages read from Firestore (real-time)

**Write Path**:
- All writes go to Firestore
- Export script regenerates JSON
- Deployment pushes new JSON to hosting

**Important**: Changes to Firestore don't appear on public site until export runs!

---

## Critical Systems

### 1. Multi-Artist Concert Support

**Problem Solved**: Concerts can have multiple performers (headliner + openers). Each needs separate setlist.

**Solution**: Artist-specific setlist document IDs

```javascript
// ALWAYS use this format (functions/index.js:287)
docId = `${concertId}-${artistSlug}`;

// Examples:
// Concert 859: "859-dierks-bentley", "859-brothers-osborne", "859-lanco"
// Concert 994: "994-phil-lesh-friends"
```

**Why This Matters**:
- Prevents race conditions when importing multiple setlists concurrently
- Each artist gets their own setlist document
- Previously used conditional logic that caused overwrites

**Related Files**:
- `functions/index.js` lines 276-291 (docId assignment)
- `website/concert.html` lines 659-665 (getSupportingAct function)

### 2. Setlist Status Tracking

Concerts have a `setlist_status` field with these values:

| Status | Icon | Meaning | Color |
|--------|------|---------|-------|
| `has_setlist` | ✅ fa-circle-check | Setlist imported | Green |
| `verified_none_on_setlistfm` | ⊘ fa-circle-minus | Checked, no setlist exists on site | Amber |
| `verified_show_didnt_happen` | ❓ fa-question-circle | Show was canceled/didn't happen | Red |
| `verified_without_setlist` | 🚫 fa-eye-slash | Show not on setlist.fm | Blue |
| `not_researched` | ⭕ fa-circle | Haven't checked yet | Gray |

**Implementation**:
- `concerts.html` lines 194-201 (filter dropdown)
- `concerts.html` (concert.js) lines 122-128 (icon mapping)
- `concert.html` lines 250-256 (status dropdown in edit form)

**Filtering**: Users can filter concert list by status to see what needs research.

### 3. Artist Fuzzy Matching

**Problem**: setlist.fm uses different artist names than user's database
- Example: "Brothers Osborne" vs "The Brothers Osborne"

**Solution**: Levenshtein distance matching (functions/index.js:72-133)

```javascript
// Matches if similarity > 85%
const similarityThreshold = 0.85;
```

**How It Works**:
1. Try exact match first
2. Try case-insensitive match
3. Calculate similarity for all artists
4. Use best match if > 85%
5. Skip adding if similar match found

**Edge Cases Handled**:
- Whitespace differences
- "The" prefix
- Ampersand vs "and"
- Typos within 15% difference

### 4. Photo Management

**Storage**: Firebase Storage bucket `concert_photos/{concertId}/`

**Metadata**: Stored in Firestore `concert_photos` collection

**Features**:
- Drag-and-drop upload (concert-photos.js)
- Thumbnail generation (client-side)
- Photo deletion with confirmation
- Gallery modal view

**Limitations**:
- Max 10MB per photo
- JPEG/PNG only
- Client-side resizing before upload

### 5. Service Worker Caching

**Current Version**: v37 (service-worker.js:2)

**Cache Strategy by Resource**:
- Static assets (HTML/JS/CSS): Cache-first + background update
- Data JSON (`/data/*`): Network-first with cache fallback
- Firebase APIs: Always network (no cache)

**Cache Names**:
- `earplugs-memories-v37` - Static cache
- `earplugs-memories-data-v37` - Data cache

**Version Increment**:
- Auto-incremented by `scripts/update_cache_version.py` on every deploy
- Forces browser to fetch new assets
- Old caches automatically deleted on activate

**Manual Cache Clear**: User can clear cache via browser message handler:
```javascript
navigator.serviceWorker.controller.postMessage({ type: 'CLEAR_CACHE' });
```

### 6. Authentication and Roles

**System**: Firebase Authentication (Google Sign-In)

**Roles** (stored in Firestore `users` collection):
- `viewer` - Can view all content
- `contributor` - Can add concerts, submit setlists, upload photos
- `admin` - Full access including approving setlists

**Role Checks**:
```javascript
// auth.js:75-91
async function checkUserRole() {
    const userDoc = await db.collection('users').doc(user.uid).get();
    const userData = userDoc.data();
    return userData?.role || 'viewer';
}
```

**UI Elements by Role**:
- Navigation: "Add Show" link (contributor+)
- Navigation: "Pending Setlists" link (admin only)
- Concert page: Edit button (contributor+)
- Admin setlists: Approve/reject buttons (admin only)

**Role Assignment**: Manual via Firestore console (add user doc with role field)

---

## Development Workflow

### Local Development

```bash
# 1. Start local Firebase emulators (optional)
firebase emulators:start

# 2. Serve website locally
cd website
python3 -m http.server 8000
# Visit http://localhost:8000

# 3. Edit files
# - HTML/JS/CSS changes are instant (refresh browser)
# - Cloud Functions need deployment

# 4. Test changes
# - Use browser DevTools console
# - Check Network tab for API calls
# - Service Worker tab for cache issues
```

### Deployment Process

**Option 1: Full Deploy** (deploys everything)
```bash
firebase deploy
```

**Option 2: Selective Deploy**
```bash
# Functions only
firebase deploy --only functions

# Hosting only
firebase deploy --only hosting

# Specific function
firebase deploy --only functions:processApprovedSetlist
```

**Option 3: Automated Deploy** (preferred for setlist imports)
- Happens automatically via GitHub Actions
- Triggered by `triggerDeploy` Cloud Function
- Includes export + cache version bump

### Making Changes

#### Frontend Changes (HTML/JS/CSS)
```bash
# 1. Edit files in website/
# 2. Test locally
# 3. Commit to git
git add website/
git commit -m "Description of changes"
git push origin main

# 4. Deploy
firebase deploy --only hosting
```

#### Cloud Function Changes
```bash
# 1. Edit functions/index.js
# 2. Test locally with emulators (optional)
firebase emulators:start --only functions

# 3. Deploy functions
firebase deploy --only functions

# 4. Commit to git
git add functions/
git commit -m "Description of changes"
git push origin main
```

#### Data Export Script Changes
```bash
# 1. Edit scripts/export_to_web.py
# 2. Test manually
python3 scripts/export_to_web.py

# 3. Commit to git
git add scripts/
git commit -m "Description of changes"
git push origin main

# 4. Changes take effect on next automated deploy
```

### Cache Busting

**CRITICAL**: Always increment cache version when deploying frontend changes!

```bash
# Automatic (recommended)
python3 scripts/update_cache_version.py
# This updates service-worker.js cache version

# Manual
# Edit service-worker.js lines 2, 4, 5
# Change v37 to v38 in CACHE_NAME and DATA_CACHE_NAME
```

**Why**: Browsers cache service worker aggressively. New version forces update.

---

## Common Tasks

### Add a New Concert Manually

**Via Website**:
1. Sign in as contributor/admin
2. Navigate to "Add Show" (add-concert.html)
3. Fill in: date, venue, city, state, artists
4. Submit form
5. Redirects to new concert page

**Via Firestore Console**:
1. Open Firebase Console → Firestore
2. Add document to `concerts` collection
3. Required fields: `date`, `venue`, `city`, `state`, `artists` (array)
4. Run export: `python3 scripts/export_to_web.py`
5. Deploy: `firebase deploy --only hosting`

### Import a Setlist

**Standard Flow**:
1. Go to concert page (concert.html?id=XXX)
2. Click "Find This Show on setlist.fm"
3. Find correct setlist, copy URL
4. Paste URL in "Import Setlist" section
5. Click "Fetch & Preview Setlist"
6. Review parsed data
7. Click "Submit for Review"
8. Admin approves on admin-setlists.html
9. Wait 2-3 minutes for automatic deployment
10. Refresh concert page to see setlist

**Direct Admin Import** (skip approval):
- Modify `pending_setlist_submissions` document with `approved: true` immediately

### Merge Duplicate Artists

**Example**: "Brothers Osborne" and "Brothers Osbourne" are the same artist

```bash
# 1. Find duplicates
python3 scripts/find_duplicate_artists.py

# Output shows potential matches with IDs

# 2. Merge (keep first ID, merge second into it)
python3 scripts/find_duplicate_artists.py --auto-merge 86 87

# This:
# - Updates all references to ID 87 → ID 86
# - Deletes ID 87
# - Recalculates stats

# 3. Export and deploy
python3 scripts/export_to_web.py
firebase deploy --only hosting
```

### Update Concert Details

**Via Website**:
1. Go to concert page
2. Click "Edit Concert Details" button (contributor+)
3. Modify fields in form
4. Click "Save Changes"
5. Wait for export + deploy

**Via Firestore Console**:
1. Find concert in `concerts` collection
2. Edit fields directly
3. Run export + deploy

### Add Photos to Concert

1. Go to concert page
2. Scroll to "Concert Photos" section (contributor+)
3. Click "Add Photos" or drag files
4. Photos upload to Firebase Storage
5. Thumbnails appear immediately (no export needed)

### Check Automation Status

```bash
# 1. Check if triggerDeploy fired
gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=triggerDeploy" --limit 5 --project earplugs-and-memories

# 2. Check GitHub Actions status
# Visit: https://github.com/Former-Stranger/concert-website/actions

# 3. Check if data exported
ls -lht website/data/concert_details/*.json | head -5

# 4. Check live site
curl -I https://earplugsandmemories.com/data/concerts.json
# Look at Last-Modified header
```

### Backup Everything

```bash
# Quick backup (recommended monthly)
./scripts/backup_all.sh

# Manual steps (if script fails)
# 1. Export Firestore
python3 scripts/export_firestore_backup.py backups/firestore-$(date +%Y-%m-%d)

# 2. Backup photos
gsutil -m cp -r gs://earplugs-and-memories.firebasestorage.app/concert_photos backups/photos-$(date +%Y-%m-%d)

# 3. Commit code
git add -A
git commit -m "Backup checkpoint"
git push origin main
```

See `BACKUP_GUIDE.md` for full details.

---

## Known Issues and Solutions

### Issue 1: Setlist Not Appearing After Import

**Symptoms**:
- Setlist shows as "approved" and "processed" in Firestore
- Concert page doesn't show setlist
- No GitHub Actions workflow ran

**Causes**:
1. GitHub token expired
2. `triggerDeploy` function not deployed
3. GitHub Actions workflow failed

**Solutions**:
```bash
# Check if triggerDeploy is deployed
firebase functions:list | grep triggerDeploy

# Redeploy if missing
firebase deploy --only functions:triggerDeploy

# Check logs
gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=triggerDeploy" --limit 3

# Manual trigger (emergency)
python3 scripts/export_to_web.py
firebase deploy --only hosting
```

### Issue 2: Race Condition with Multiple Openers

**Symptoms**:
- Concert has 3 artists
- Only 1 or 2 setlists appear after import
- processApprovedSetlist logs show multiple executions

**Cause**: Concurrent Cloud Function executions overwrote each other (FIXED in V1.0)

**Solution**: Already implemented! Document ID now always uses `{concertId}-{artistSlug}` format.

**Verification**:
```bash
# Check function code
grep -A 5 "ALWAYS use artist-specific" functions/index.js
# Should see: docId = `${concertId}-${artistSlug}`;
```

### Issue 3: Edit Form Shows Only First Opener

**Symptoms**:
- Concert has multiple openers
- Edit form only shows first opener in "Supporting Act" field

**Cause**: `getSupportingAct()` used `find()` instead of `filter()` (FIXED in V1.0)

**Solution**: Already fixed in website/concert.html:659-665

```javascript
function getSupportingAct(artists) {
    if (!artists || !Array.isArray(artists)) return '';
    const openers = artists.filter(a => a.role === 'opener');  // filter, not find!
    return openers.map(a => a.artist_name).join(', ');
}
```

### Issue 4: Service Worker Caches Old Data

**Symptoms**:
- Changes deployed but user sees old data
- Hard refresh doesn't help

**Solution**:
```javascript
// In browser console:
navigator.serviceWorker.getRegistrations().then(registrations => {
    registrations.forEach(r => r.unregister());
});
location.reload();
```

**Prevention**: Always increment cache version on deploy (scripts/update_cache_version.py)

### Issue 5: Duplicate Artists in Database

**Symptoms**:
- Same artist appears twice with different IDs
- Concert references wrong artist ID

**Solution**: Use merge script
```bash
python3 scripts/find_duplicate_artists.py --auto-merge <keep_id> <merge_id>
```

**Prevention**: Fuzzy matching in processApprovedSetlist reduces duplicates automatically

### Issue 6: Firebase Quota Exceeded

**Symptoms**:
- Cloud Functions fail with quota error
- Firestore reads/writes rejected

**Solutions**:
```bash
# Check quota usage
firebase projects:list
# Visit Firebase Console → Usage & Billing

# Temporary: Wait for quota reset (daily)
# Permanent: Upgrade to Blaze plan (pay-as-you-go)
```

### Issue 7: GitHub Actions Workflow Fails

**Symptoms**:
- triggerDeploy fires successfully
- Workflow starts but fails
- Site doesn't update

**Common Causes**:
1. Firebase token expired
2. Python script error in export_to_web.py
3. Google Cloud credentials expired

**Debug**:
```bash
# View workflow logs
# Visit: https://github.com/Former-Stranger/concert-website/actions

# Check secrets are set
# GitHub → Settings → Secrets → Actions
# Required: FIREBASE_TOKEN, GOOGLE_APPLICATION_CREDENTIALS

# Regenerate Firebase token
firebase login:ci
# Update FIREBASE_TOKEN secret in GitHub
```

---

## Important Patterns

### Pattern 1: Firestore Document IDs

**Concerts**: Auto-generated or string ID
```javascript
// Create with auto ID
db.collection('concerts').add({ ... });

// Create with specific ID (rare)
db.collection('concerts').doc('1000').set({ ... });
```

**Setlists**: MUST use `{concertId}-{artistSlug}` format
```javascript
const artistSlug = artistName.toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
const docId = `${concertId}-${artistSlug}`;
db.collection('setlists').doc(docId).set({ ... });
```

**Artists**: Usually auto-generated, can have MBID from setlist.fm

### Pattern 2: Concert Artists Array

```javascript
{
    "id": "859",
    "date": "2024-10-15",
    "venue": "Red Rocks",
    "artists": [
        {
            "artist_id": "abc123",
            "artist_name": "Dierks Bentley",
            "role": "headliner"
        },
        {
            "artist_id": "def456",
            "artist_name": "Brothers Osborne",
            "role": "opener"
        },
        {
            "artist_id": "ghi789",
            "artist_name": "LANCO",
            "role": "opener"
        }
    ]
}
```

**Rules**:
- Exactly one `role: "headliner"`
- Zero or more `role: "opener"`
- `artist_id` references `artists` collection
- Order matters: headliner first, then openers in performance order

### Pattern 3: Setlist Data Structure

```javascript
{
    "concert_id": "859",
    "artist_id": "abc123",
    "artist_name": "Dierks Bentley",
    "artist_role": "headliner",
    "setlistfm_url": "https://www.setlist.fm/setlist/...",
    "song_count": 23,
    "has_encore": true,
    "songs": [
        {
            "position": 1,
            "name": "Song Title",
            "set_name": "Main Set",
            "encore": 0,
            "is_cover": false,
            "cover_artist": null
        },
        {
            "position": 22,
            "name": "Final Song",
            "set_name": "Main Set",
            "encore": 1,  // First encore
            "is_cover": true,
            "cover_artist": "Original Artist"
        }
    ],
    "tour_name": "Tour Name Here"  // Optional
}
```

**Key Fields**:
- `encore`: 0 = main set, 1 = first encore, 2 = second encore, etc.
- `is_cover`: Boolean indicating if song is a cover
- `cover_artist`: Original artist if is_cover is true
- `position`: Sequential numbering across entire setlist

### Pattern 4: Exported JSON Structure

**List Files** (concerts.json, artists.json, etc.):
```javascript
[
    { "id": "1", ... },
    { "id": "2", ... },
    { "id": "3", ... }
]
```

**Detail Files** (concert_details/123.json):
```javascript
{
    "id": "123",
    "show_number": 122,
    "date": "2024-10-15",
    "venue": "Venue Name",
    "artists": [...],
    "setlists": [...],  // Full setlist data embedded
    "photos": [...],
    "photo_count": 5,
    "has_encore": true,
    "total_song_count": 45
}
```

**Why**: Detail files are complete, self-contained. List files are lightweight for browsing.

### Pattern 5: Error Handling in Cloud Functions

```javascript
try {
    // Main logic
    await db.collection('concerts').doc(concertId).update({ ... });
    console.log('Success message');
} catch (error) {
    console.error('Error description:', error);
    // Don't throw - mark as failed instead
    await db.collection('pending_setlist_submissions').doc(submissionId).update({
        processed: false,
        error: error.message
    });
}
```

**Why**: Cloud Functions timeout after 60s. Throwing errors can leave data in inconsistent state.

### Pattern 6: Frontend Data Loading

```javascript
// concerts.js pattern
async function loadConcerts() {
    try {
        const response = await fetch(`data/concerts.json?v=${Date.now()}`);
        allConcerts = await response.json();
        renderConcerts();
    } catch (error) {
        console.error('Error loading concerts:', error);
        // Show user-friendly error
    }
}
```

**Key Points**:
- Cache-busting with `?v=${Date.now()}` on critical updates
- Graceful error handling
- No direct Firestore queries (except admin pages)

---

## Testing and Debugging

### Frontend Debugging

**Browser DevTools**:
```javascript
// Check if service worker is active
navigator.serviceWorker.getRegistration().then(reg => console.log(reg));

// View cached data
caches.keys().then(keys => console.log(keys));

// Force reload without cache
location.reload(true);

// Check Firebase auth state
firebase.auth().currentUser;
```

**Common Issues**:
1. **404 on JSON files**: Check if export ran, check Network tab
2. **Old data showing**: Clear cache, check cache version
3. **Auth errors**: Check Firebase Console → Authentication → Settings

### Cloud Functions Debugging

**View Logs**:
```bash
# Recent logs for specific function
gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=processApprovedSetlist" --limit 20

# Filter by severity
gcloud logging read "resource.type=cloud_function AND severity>=ERROR" --limit 10

# Live tail (watch real-time)
gcloud logging tail "resource.type=cloud_function"
```

**Local Testing**:
```bash
# Start emulators
firebase emulators:start

# Functions run on http://localhost:5001
# Firestore UI on http://localhost:4000

# Call function with curl
curl -X POST http://localhost:5001/earplugs-and-memories/us-central1/functionName \
  -H "Content-Type: application/json" \
  -d '{"data": {...}}'
```

### Data Export Debugging

**Test export locally**:
```bash
# Run export script
python3 scripts/export_to_web.py

# Check output
ls -lh website/data/
cat website/data/stats.json

# Validate JSON
python3 -m json.tool website/data/concerts.json > /dev/null && echo "Valid JSON"
```

**Common Issues**:
1. **Missing collections**: Check Firestore has data
2. **Empty arrays**: Check collection names match
3. **Encoding errors**: Check for special characters in data

### GitHub Actions Debugging

**View workflow run**:
1. Go to https://github.com/Former-Stranger/concert-website/actions
2. Click on recent workflow run
3. Expand failed step
4. Check error message

**Common Failures**:
```bash
# Firebase deploy fails
# → Check FIREBASE_TOKEN secret is valid

# Python script fails
# → Check export_to_web.py for errors
# → Check Firestore data structure

# Permission denied
# → Check GOOGLE_APPLICATION_CREDENTIALS secret
```

**Manual re-run**:
1. GitHub → Actions → Select workflow
2. Click "Re-run failed jobs"

### Performance Monitoring

**Check site speed**:
```bash
# Lighthouse in Chrome DevTools
# Run audit, check PWA score

# Check JSON file sizes
du -h website/data/*.json

# Check image sizes
gsutil du -s gs://earplugs-and-memories.firebasestorage.app/concert_photos
```

**Optimization Tips**:
- Keep JSON files under 1MB each
- Use concert_details/*.json for large data
- Compress images before upload
- Monitor Firestore read counts

---

## Quick Reference

### File URLs
- **GitHub**: https://github.com/Former-Stranger/concert-website
- **Live Site**: https://earplugsandmemories.com
- **Firebase Console**: https://console.firebase.google.com/project/earplugs-and-memories
- **GitHub Actions**: https://github.com/Former-Stranger/concert-website/actions

### Important Constants
- **Cache Version**: v37 (service-worker.js:2)
- **Project ID**: earplugs-and-memories
- **Region**: us-central1
- **Node Version**: 20

### Command Cheat Sheet
```bash
# Deploy everything
firebase deploy

# Deploy specific parts
firebase deploy --only hosting
firebase deploy --only functions
firebase deploy --only functions:processApprovedSetlist

# Export data
python3 scripts/export_to_web.py

# Backup everything
./scripts/backup_all.sh

# View logs
gcloud logging read "resource.type=cloud_function" --limit 20

# Check git status
git status
git log --oneline -5

# Merge duplicate artists
python3 scripts/find_duplicate_artists.py --auto-merge <keep_id> <remove_id>

# Update cache version
python3 scripts/update_cache_version.py
```

---

## Version History

### V1.0 (November 3, 2024)
**Released: Out of Beta**

Key Features:
- ✅ Multi-artist concert support (headliner + multiple openers)
- ✅ Automatic setlist import via setlist.fm
- ✅ Race condition fix for concurrent imports
- ✅ Status tracking with visual icons
- ✅ Fuzzy artist name matching
- ✅ Photo upload and management
- ✅ PWA with offline support
- ✅ Automated deployment pipeline
- ✅ Comprehensive backup system

Known Limitations:
- No mobile app (PWA only)
- Photos stored in Firebase Storage (not CDN)
- Single admin approval workflow
- No API for external access
- No automated testing

Recent Fixes:
- Fixed race condition in multi-artist setlist imports (functions/index.js:287)
- Fixed edit form to show all openers (concert.html:659-665)
- Fixed triggerDeploy automation by deploying all functions
- Standardized status icons across all pages

---

## Next Steps (Future Enhancements)

Potential features for V2.0+:
- [ ] Mobile app (React Native or Flutter)
- [ ] Public API for external access
- [ ] Social features (share setlists, follow friends)
- [ ] Advanced statistics (trends, charts, insights)
- [ ] Tour tracking and predictions
- [ ] Setlist.fm two-way sync
- [ ] Automated testing (Jest, Cypress)
- [ ] Performance optimizations (CDN, image compression)
- [ ] Multi-user support (friends, groups)
- [ ] Spotify integration (link songs to tracks)

---

## Questions to Ask the User

When starting work on this project, consider asking:

1. **What are you trying to accomplish?**
   - Is this a bug fix, feature addition, or maintenance task?

2. **Are there any active deployments or users?**
   - Should I avoid deploying during peak hours?

3. **Have there been recent changes?**
   - Any new concerts, setlists, or data since last session?

4. **Are backups current?**
   - When was the last backup run?

5. **Any known issues?**
   - Are there open bugs or pending tasks?

---

## Emergency Contacts & Resources

- **Project Owner**: Jason (akalbfell@gmail.com)
- **Firebase Project**: earplugs-and-memories
- **GitHub Repo**: https://github.com/Former-Stranger/concert-website
- **Backup Guide**: See BACKUP_GUIDE.md
- **Service Worker Cache**: v37

**If something breaks badly**:
1. Check GitHub Actions logs
2. Check Cloud Functions logs: `gcloud logging read "resource.type=cloud_function AND severity>=ERROR"`
3. Restore from backup: See BACKUP_GUIDE.md
4. Redeploy last known good: `git checkout v1.0 && firebase deploy`

---

**END OF HANDOFF DOCUMENT**

*This document should be read by Claude at the start of each session to understand the project context. Keep it updated as the project evolves.*
