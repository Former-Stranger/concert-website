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
