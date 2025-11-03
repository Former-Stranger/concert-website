Please perform a comprehensive project review:

1. Review all documentation files (README, docs, etc.) to understand the project's purpose and setup
2. Examine the project structure and key files to understand the architecture and implementation
3. Analyze the last 3 git commits to understand recent changes and development direction
4. Provide a summary of:
   - What this project does
   - Key technologies and architecture
   - Recent development activity and changes
   - Current state of the project

Take as much time as needed for a thorough analysis. Use the Explore agent for codebase exploration tasks.

---

## CRITICAL: Deployment and Cache Busting Workflow

This project uses a Service Worker for PWA capabilities and aggressive caching. **Cache busting is CRITICAL** to ensure users see changes after deployment.

### Why Cache Busting Matters

The Service Worker caches all static files (HTML, CSS, JS) for offline access. Without updating the cache version:
- Users will continue seeing old cached content even after deployment
- Changes won't appear until users manually clear their browser cache
- This causes confusion and makes it appear that deployments "didn't work"

The cache version is stored in `website/service-worker.js`:
```javascript
const CACHE_NAME = 'earplugs-memories-v23';  // ← This MUST increment on every deploy
```

### Three Deployment Methods

**RULE: Always use a deploy script. Never run `firebase deploy` directly.**

#### 1. Full Deployment: `./deploy.sh`
**Use when data changes** (new concerts, setlists, photos, etc.)

What it does:
1. ✅ Runs `python3 scripts/update_cache_version.py` (auto-increments: v23 → v24)
2. ✅ Exports Firestore data to JSON (`scripts/export_to_web.py`)
3. ✅ Clears Firebase CLI cache
4. ✅ Deploys to Firebase Hosting

Command:
```bash
./deploy.sh
```

#### 2. Quick Hosting Deploy: `./deploy-hosting.sh`
**Use when ONLY HTML/CSS/JS files changed** (no data changes)

What it does:
1. ✅ Runs `python3 scripts/update_cache_version.py` (auto-increments)
2. ❌ No data export (faster)
3. ✅ Clears Firebase CLI cache
4. ✅ Deploys to Firebase Hosting

Command:
```bash
./deploy-hosting.sh
```

Use cases:
- UI fixes (layout, styling, dropdown issues)
- JavaScript logic changes
- HTML structure changes
- Any frontend-only changes

#### 3. Automatic Deployment (GitHub Actions)
**Triggered automatically** by Cloud Functions

Triggers:
- Photo uploaded/deleted → `onPhotoUpload`, `onPhotoDelete`
- Setlist approved → `triggerDeploy`
- Concert added/edited → `processNewConcert`
- Manual trigger → `triggerManualDeploy`

What it does (defined in `.github/workflows/deploy.yml`):
1. ✅ Runs `python3 scripts/update_cache_version.py`
2. ✅ Exports Firestore data
3. ✅ Deploys to Firebase Hosting

### ⚠️ NEVER Do This

```bash
# ❌ WRONG - Does NOT update cache version
firebase deploy --only hosting

# ❌ WRONG - Does NOT update cache version
firebase deploy --only functions
```

These commands skip the cache busting step, causing users to see stale cached content.

### Correct Manual Deployment

If you must deploy manually without the script:

```bash
# 1. Update cache version first
python3 scripts/update_cache_version.py

# 2. Then deploy
firebase deploy --only hosting
```

But it's better to use `./deploy-hosting.sh` which does both automatically.

### How Cache Busting Works

1. **Script runs**: `update_cache_version.py` increments version in `service-worker.js`
   - `v22` → `v23` → `v24` (auto-increments)
   - Updates both `CACHE_NAME` and `DATA_CACHE_NAME`

2. **Service Worker detects change**: Browser sees new version number
   - Old Service Worker detects it's outdated
   - Downloads new Service Worker
   - Installs and activates on next page load

3. **Old cache cleared**: Service Worker's `activate` event
   ```javascript
   // Delete old caches that don't match current version
   caches.keys().then(names => {
     names.forEach(name => {
       if (name !== CACHE_NAME && name !== DATA_CACHE_NAME) {
         caches.delete(name);  // Remove old cached files
       }
     });
   });
   ```

4. **Fresh content served**: Users get new HTML/CSS/JS files

### Verifying Deployment

After deploying, verify cache busting worked:

```bash
# Check deployed version
curl -s https://earplugsandmemories.com/service-worker.js | head -5
# Should show: // Version: 1.0.24 (or latest)

# Check if it's running
# Open DevTools → Application → Service Workers
# Should see new version number
```

### Summary for Claude Sessions

**When making changes that require deployment:**

1. **Data changes** (concerts, setlists, photos) → Use `./deploy.sh`
2. **Frontend changes** (HTML/CSS/JS) → Use `./deploy-hosting.sh`
3. **Function changes only** → `firebase deploy --only functions` is OK (no cache needed)
4. **Never** run `firebase deploy --only hosting` directly without cache busting

**Why this matters:** Users rely on the Service Worker cache for fast loading and offline access. Without proper cache busting, they'll see old cached content indefinitely, breaking the site for them after updates.

---

## CRITICAL: Data Flow & Architecture

This project uses a **hybrid architecture** combining static JSON files with Firebase real-time features. Understanding this data flow is ESSENTIAL to avoid confusion about why changes aren't appearing.

### Architecture Overview

```
Firestore Database (Source of Truth)
         ↓
Export Script (export_to_web.py)
         ↓
Static JSON Files (website/data/*.json)
         ↓
Firebase Hosting (CDN)
         ↓
User's Browser
```

### Two Data Sources

**1. Firestore (Real-time) - Used by:**
- Edit/admin interfaces (add-concert.html, concert.html admin settings)
- Photo upload/management
- Setlist submission system
- Authentication
- Any write operations

**2. Static JSON (Read-only) - Used by:**
- **concerts.html** (list page) → reads `data/concerts.json`
- **concert.html** (detail page) → reads `data/concert_details/{id}.json`
- **artists.html** → reads `data/artists.json`
- **venues.html** → reads `data/venues.json`
- All public-facing pages

### Critical Understanding: The "Two Worlds" Problem

**PROBLEM:** Changes made to Firestore don't automatically appear on public pages!

**Example Scenario:**
1. User adds a setlist for concert 893 → Updates Firestore ✓
2. Edit window shows the change → Reads from Firestore ✓
3. **Concert detail page shows old data** → Still reading old static JSON ✗

**WHY:** The static JSON files in `website/data/` are snapshots from the last export. They don't update until you run the export script and deploy.

### The Export Process

**File:** `scripts/export_to_web.py`

**What it exports:**
1. **concerts.json** - All concerts with basic info (list page)
2. **concert_details/{id}.json** - Individual concert files with setlists, photos, etc.
3. **artists.json** - All artists with concert counts
4. **venues.json** - All venues with concert counts
5. **songs.json** - All unique songs across all concerts
6. **stats.json** - Statistics (total concerts, songs, etc.)

**Key Rule:** Export script now includes **all setlists, even empty ones** (as of this session)
- Previously skipped setlists with 0 songs
- Now includes them to show supporting acts and multi-artist concerts

**When exports happen:**
- Running `./deploy.sh` manually
- Running `./deploy-hosting.sh` manually (⚠️ NO export - hosting only!)
- Automatic GitHub Actions deployment (triggered by Cloud Functions)

### Automatic Deployment System

The system automatically exports and deploys when these events occur in Firestore:

#### Trigger 1: Setlist Approved
- **File:** `functions/index.js:702` (`triggerDeploy`)
- **Event:** `pending_setlist_submissions/{id}` marked as `processed`
- **GitHub Action:** `deploy-setlist`
- **Result:** Export + Deploy (2-3 minutes)

#### Trigger 2: New Concert Added
- **File:** `functions/index.js:766` (`processNewConcert`)
- **Event:** New document in `concerts` collection
- **GitHub Action:** `new-concert`
- **Result:** Export + Deploy (2-3 minutes)

#### Trigger 3: Photo Upload/Delete
- **File:** `functions/index.js:943` (`onPhotoUpload`), `functions/index.js:966` (`onPhotoDelete`)
- **Event:** Document created/deleted in `concert_photos` collection
- **GitHub Action:** `photo-upload` or `photo-delete`
- **Result:** Export + Deploy (2-3 minutes)

#### Trigger 4: Manual Trigger
- **File:** `functions/index.js:919` (`triggerManualDeploy`)
- **Called from:** `concert.html:441` (when changing setlist status dropdown)
- **GitHub Action:** `manual-deploy`
- **Result:** Export + Deploy (2-3 minutes)

### GitHub Actions Workflow

**File:** `.github/workflows/deploy.yml`

**Triggered by:** `repository_dispatch` events from Cloud Functions

**Steps:**
1. Update Service Worker cache version (`scripts/update_cache_version.py`)
2. **Export Firestore to JSON** (`scripts/export_to_web.py`) ← THIS IS KEY
3. Clear Firebase CLI cache
4. Deploy to Firebase Hosting

**Time:** Typically 2-3 minutes from trigger to live

### Troubleshooting: "Why isn't my change showing?"

If you make a change and it doesn't appear on the public site:

**Step 1: Check where the change was made**
- Firestore? → Need to export and deploy
- Static files? → Need to deploy (no export needed)

**Step 2: Verify the export happened**
```bash
# Check if concert detail file exists
ls -lh website/data/concert_details/893.json

# Check contents
cat website/data/concert_details/893.json | python3 -m json.tool | head -50
```

**Step 3: Check if automatic deployment triggered**
- View Cloud Function logs: `firebase functions:log --only triggerDeploy`
- Check GitHub Actions: https://github.com/Former-Stranger/concert-website/actions
- Look for recent workflow runs

**Step 4: Check cache version**
```bash
# Local file
grep "CACHE_NAME = " website/service-worker.js

# Deployed version
curl -s https://earplugsandmemories.com/service-worker.js | grep "CACHE_NAME = "
```

**Step 5: Manual intervention if needed**
```bash
# Full export + deploy
./deploy.sh

# Hosting only (if data already exported)
./deploy-hosting.sh
```

### Common Scenarios

**Scenario 1: Added setlist, not showing on concert page**
- **Cause:** Static JSON not exported yet
- **Solution:** Wait 2-3 minutes for auto-deploy, OR run `./deploy.sh`

**Scenario 2: Changed HTML/CSS, not appearing for users**
- **Cause:** Cache version not incremented
- **Solution:** Always use `./deploy-hosting.sh`, never `firebase deploy` directly

**Scenario 3: Empty setlists not creating detail files**
- **Cause:** Fixed in this session - export script now includes empty setlists
- **Solution:** Already fixed, no action needed

**Scenario 4: Edit window shows data, public page doesn't**
- **Cause:** Edit window reads Firestore (real-time), public page reads static JSON (snapshot)
- **Solution:** This is expected behavior. Wait for auto-deploy or run `./deploy.sh`

### Key Files Reference

**Export & Deployment:**
- `scripts/export_to_web.py` - Firestore → JSON export
- `scripts/update_cache_version.py` - Cache version incrementer
- `deploy.sh` - Full deployment script (export + deploy)
- `deploy-hosting.sh` - Quick deployment (deploy only, no export)
- `.github/workflows/deploy.yml` - GitHub Actions workflow

**Cloud Functions (Auto-deploy triggers):**
- `functions/index.js:702` - Setlist approved trigger
- `functions/index.js:766` - New concert trigger
- `functions/index.js:919` - Manual deploy trigger
- `functions/index.js:943` - Photo upload trigger
- `functions/index.js:966` - Photo delete trigger

**Frontend Data Sources:**
- `website/data/concerts.json` - Concert list page
- `website/data/concert_details/{id}.json` - Concert detail pages
- `website/data/artists.json` - Artist list
- `website/data/venues.json` - Venue list
- `website/data/songs.json` - Song database
- `website/data/stats.json` - Site statistics

### Summary for Future Sessions

**Golden Rules:**
1. **Firestore changes require export + deploy** to appear on public pages
2. **Always use deploy scripts**, never `firebase deploy` directly
3. **Automatic deployments take 2-3 minutes** - be patient
4. **Edit windows show real-time Firestore**, public pages show static JSON snapshots
5. **Export script includes empty setlists** (fixed in this session)

**Quick Decision Tree:**
- Changed Firestore data? → Wait for auto-deploy OR run `./deploy.sh`
- Changed HTML/CSS/JS only? → Run `./deploy-hosting.sh`
- Changed Cloud Functions only? → `firebase deploy --only functions`
- Unsure? → Run `./deploy.sh` (safest option)
