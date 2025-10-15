# Deployment Guide

This document explains all the ways to deploy updates to the concert archive website.

## Overview

The website is hosted on **Firebase Hosting** as a static site. The deployment process involves:

1. **Export** data from Firestore to JSON files
2. **Deploy** the website folder to Firebase Hosting

## Deployment Methods

### Method 1: Automated Deployment (Recommended)

**When it happens**: Automatically when you approve a setlist submission.

**How it works**:
1. You approve a pending setlist in the admin panel
2. Cloud Function `processApprovedSetlist` runs:
   - Fetches setlist data from setlist.fm API
   - Saves to Firestore (concerts + setlists collections)
   - Triggers GitHub Actions workflow via repository dispatch
3. GitHub Actions workflow runs:
   - Exports Firestore data to JSON files
   - Deploys to Firebase Hosting
4. Website updates automatically (2-3 minutes)

**Monitoring**:
- GitHub Actions: https://github.com/Former-Stranger/concert-website/actions
- Cloud Functions logs: `gcloud functions logs read processApprovedSetlist --region=us-central1 --project=earplugs-and-memories --limit=20`

**When to use**: This is the primary deployment method. Most updates happen automatically.

---

### Method 2: Manual Deployment Script

**When to use**:
- After manually adding concerts via `python3 scripts/add_concert.py`
- When you make direct changes to website files (HTML, JS, CSS)
- If automated deployment fails
- For immediate deployment without waiting for Cloud Function

**Prerequisites**:
1. Firebase CLI installed: `npm install -g firebase-tools`
2. Authenticated with Firebase: `firebase login`
3. Authenticated with Google Cloud: `gcloud auth application-default login`
4. Environment variable set (already in deploy.sh)

**Command**:
```bash
./deploy.sh
```

**What it does**:
1. Sets `GOOGLE_CLOUD_PROJECT=earplugs-and-memories`
2. Runs `python3 scripts/export_to_web.py`:
   - Connects to Firestore
   - Exports all collections to JSON files in `website/data/`
   - Generates: concerts.json, artists.json, venues.json, songs.json, stats.json
   - Generates detail files for each concert/artist/venue
3. Runs `firebase deploy --only hosting`:
   - Uploads all files in `website/` folder
   - Deploys to Firebase Hosting
   - Updates live website

**Expected output**:
```
🚀 Deploying Concert Archive Updates
=======================================

📊 Exporting data from Firestore...
Exporting Firestore database to JSON...
============================================================

1. Exporting concerts...
   Exported 1274 concerts

2. Exporting concert details with setlists...
   Exported 845 concert details

3. Exporting artists...
   Exported 612 artists

4. Exporting venues...
   Exported 192 venues

5. Generating statistics...
   Generated statistics

6. Exporting songs...
   Exported 7209 unique songs

7. Exporting venue details...
   Exported 192 venue details

8. Exporting artist details...
   Exported 669 artist details

============================================================
Export complete!
Files written to: /Users/akalbfell/Documents/Jay/concert-website/website/data

🌐 Deploying to Firebase Hosting...

=== Deploying to 'earplugs-and-memories'...

i  deploying hosting
i  hosting[earplugs-and-memories]: beginning deploy...
i  hosting[earplugs-and-memories]: found 1732 files in website
✔  hosting[earplugs-and-memories]: file upload complete
i  hosting[earplugs-and-memories]: finalizing version...
✔  hosting[earplugs-and-memories]: version finalized
i  hosting[earplugs-and-memories]: releasing new version...
✔  hosting[earplugs-and-memories]: release complete

✔  Deploy complete!

✅ Deploy complete! Your website is updated.
🔗 https://earplugs-and-memories.web.app
```

**Time**: ~2-3 minutes total

---

### Method 3: GitHub Actions Manual Trigger

**When to use**:
- Deploy.sh fails due to local environment issues
- Deploying from a different computer
- Want to use GitHub's infrastructure instead of local

**Steps**:
1. Go to https://github.com/Former-Stranger/concert-website/actions
2. Click "Deploy to Firebase" workflow
3. Click "Run workflow" button (if available)
4. Select branch (usually `main`)
5. Click green "Run workflow" button

**Note**: This method requires `workflow_dispatch` to be enabled in `.github/workflows/deploy.yml` (it is).

**What it does**: Same as deploy.sh, but runs in GitHub's cloud environment.

---

### Method 4: Firebase CLI Direct

**When to use**: Only if you need to deploy without exporting data (rare).

**Command**:
```bash
firebase deploy --only hosting
```

**Warning**: This skips the data export step, so any Firestore changes won't appear on the website.

---

## What Gets Deployed

When you deploy, these files are uploaded to Firebase Hosting:

```
website/
├── index.html
├── concerts.html
├── artists.html
├── venues.html
├── songs.html
├── concert.html
├── artist.html
├── venue.html
├── add-concert.html
├── admin-setlists.html
├── js/
│   ├── firebase-config.js
│   ├── auth.js
│   ├── concert.js
│   ├── concerts.js
│   ├── setlist-submission.js
│   └── concert-notes.js
└── data/                    # Generated by export script
    ├── concerts.json
    ├── artists.json
    ├── venues.json
    ├── songs.json
    ├── stats.json
    ├── concert_details/
    │   └── [id].json
    ├── artist_details/
    │   └── [id].json
    └── venue_details/
        └── [id].json
```

## Caching & Propagation

### Browser Caching
Firebase Hosting sets cache headers:
- HTML files: 1 hour cache
- JS/CSS files: 1 year cache (with content hash)
- Data files: 1 hour cache

**To see latest changes**:
- Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
- Or open in incognito/private window

### CDN Propagation
Firebase uses a global CDN. After deployment:
- Most regions: 1-2 minutes
- All regions: 5-10 minutes

## Rollback

If you need to rollback to a previous version:

### Via Firebase Console
1. Go to https://console.firebase.google.com/project/earplugs-and-memories/hosting
2. Click on the "earplugs-and-memories" site
3. Go to "Release history" tab
4. Find the previous version
5. Click "⋮" menu → "Rollback"

### Via Firebase CLI
```bash
firebase hosting:rollback
```

## Troubleshooting

### Error: "Project ID is required to access Firestore"

**Cause**: GOOGLE_CLOUD_PROJECT environment variable not set.

**Fix**: The deploy.sh script now sets this automatically. If running export_to_web.py manually:
```bash
export GOOGLE_CLOUD_PROJECT=earplugs-and-memories
python3 scripts/export_to_web.py
```

Or add to your shell profile (~/.zshrc or ~/.bashrc):
```bash
export GOOGLE_CLOUD_PROJECT=earplugs-and-memories
```

---

### Error: "Could not use application default credentials"

**Cause**: Not authenticated with Google Cloud.

**Fix**:
```bash
gcloud auth application-default login
```

---

### Error: "Authentication Error" during firebase deploy

**Cause**: Not authenticated with Firebase.

**Fix**:
```bash
firebase login
```

---

### Error: "No project active"

**Cause**: Firebase CLI doesn't know which project to use.

**Fix**:
```bash
firebase use earplugs-and-memories
```

---

### Changes not appearing on website

**Possible causes**:
1. Browser cache
2. CDN cache
3. Deployment didn't complete
4. Wrong project deployed

**Debugging**:
1. Check deployment logs for errors
2. Hard refresh browser (Cmd+Shift+R)
3. Check in incognito window
4. Verify file uploaded:
   ```bash
   curl https://earplugs-and-memories.web.app/data/concerts.json | head -20
   ```
5. Check Firebase console for latest deployment

---

### GitHub Actions deployment failing

**Check**:
1. GitHub Actions logs: https://github.com/Former-Stranger/concert-website/actions
2. Secrets are set:
   - `FIREBASE_TOKEN`
   - `GOOGLE_APPLICATION_CREDENTIALS`
3. Cloud Function triggered correctly:
   ```bash
   gcloud functions logs read processApprovedSetlist --region=us-central1 --project=earplugs-and-memories --limit=20
   ```

---

## Deployment Checklist

Before deploying:
- [ ] Committed all local changes to git
- [ ] Tested changes locally if applicable
- [ ] Verified Firestore data is correct
- [ ] Environment variables set (if using deploy.sh)

After deploying:
- [ ] Check deployment logs for errors
- [ ] Hard refresh website in browser
- [ ] Verify changes appear correctly
- [ ] Test functionality (if changes affect features)

## Quick Reference

| Task | Command |
|------|---------|
| Full deployment (recommended) | `./deploy.sh` |
| Export data only | `python3 scripts/export_to_web.py` |
| Deploy hosting only | `firebase deploy --only hosting` |
| Deploy functions only | `firebase deploy --only functions` |
| Deploy everything | `firebase deploy` |
| View hosting logs | Check Firebase Console |
| View function logs | `gcloud functions logs read --region=us-central1` |
| Rollback deployment | `firebase hosting:rollback` |

## Monitoring Deployments

### Firebase Hosting Dashboard
https://console.firebase.google.com/project/earplugs-and-memories/hosting

Shows:
- Deployment history
- Current version
- Bandwidth usage
- Requests per day

### GitHub Actions
https://github.com/Former-Stranger/concert-website/actions

Shows:
- Automated deployment runs
- Build logs
- Success/failure status

### Cloud Functions
```bash
# Recent logs
gcloud functions logs read --region=us-central1 --project=earplugs-and-memories --limit=30

# Specific function
gcloud functions logs read processApprovedSetlist --region=us-central1 --project=earplugs-and-memories --limit=20

# Follow logs (live)
gcloud functions logs read --region=us-central1 --project=earplugs-and-memories --limit=10 --follow
```

## CI/CD Pipeline

The automated pipeline (when setlist approved):

```
1. User approves setlist in admin panel
   ↓
2. Firestore: pending_setlist_submissions status → 'approved'
   ↓
3. Cloud Function: processApprovedSetlist triggers
   ↓
4. Fetch setlist from setlist.fm API
   ↓
5. Save to Firestore (concerts + setlists)
   ↓
6. Trigger GitHub Actions via repository_dispatch
   ↓
7. GitHub Actions: export_to_web.py runs
   ↓
8. JSON files generated in website/data/
   ↓
9. GitHub Actions: firebase deploy runs
   ↓
10. Website updated on Firebase Hosting
   ↓
11. CDN cache refreshed globally (1-2 minutes)
```

Total time: **2-3 minutes** from approval to live update.
