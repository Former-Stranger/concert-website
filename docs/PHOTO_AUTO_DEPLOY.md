# Photo Auto-Deployment Feature

## Overview

Photos now automatically trigger website deployment! When you upload or delete a photo, the site will automatically update within 2-3 minutes without any manual intervention.

## How It Works

### Upload Flow

1. **User uploads photo** → Saved to Firebase Storage + Firestore
2. **Cloud Function triggers** (`onPhotoUpload`) → Detects new photo
3. **GitHub Actions triggered** → Runs export and deployment workflow
4. **Website updates** → Photo appears in ~2-3 minutes

### Delete Flow

1. **User/owner deletes photo** → Removed from Storage + Firestore
2. **Cloud Function triggers** (`onPhotoDelete`) → Detects deletion
3. **GitHub Actions triggered** → Runs export and deployment workflow
4. **Website updates** → Photo removed in ~2-3 minutes

## Cloud Functions

### `onPhotoUpload`
- **Trigger**: Firestore `onCreate` on `concert_photos/{photoId}`
- **Action**: Triggers GitHub Actions workflow
- **Event Type**: `photo-upload`
- **Payload**: Concert ID

### `onPhotoDelete`
- **Trigger**: Firestore `onDelete` on `concert_photos/{photoId}`
- **Action**: Triggers GitHub Actions workflow
- **Event Type**: `photo-delete`
- **Payload**: Concert ID

## GitHub Actions Integration

The Cloud Functions trigger the existing GitHub Actions workflow via repository dispatch:

```javascript
// Sends POST to GitHub API
https://api.github.com/repos/Former-Stranger/concert-website/dispatches

// With payload
{
  event_type: "photo-upload", // or "photo-delete"
  client_payload: {
    entity_id: concertId
  }
}
```

The GitHub Actions workflow (`.github/workflows/deploy.yml`) handles the deployment:
1. Exports Firestore data to JSON files
2. Deploys to Firebase Hosting
3. Updates live website

## Monitoring

### View Function Logs

```bash
# View all function logs
firebase functions:log

# View specific function
firebase functions:log --only onPhotoUpload
firebase functions:log --only onPhotoDelete

# Or use gcloud
gcloud functions logs read onPhotoUpload --region=us-central1 --limit=20
gcloud functions logs read onPhotoDelete --region=us-central1 --limit=20
```

### Check GitHub Actions

View deployment progress:
https://github.com/Former-Stranger/concert-website/actions

### Typical Log Output

**Successful deployment:**
```
New photo uploaded: abc123 for concert 1063
Triggering automatic deployment to update static site...
GitHub Actions workflow triggered for photo-upload: 1063
Website will be automatically updated in a few minutes.
Deployment triggered successfully. Site will update in 2-3 minutes.
```

**Failed deployment:**
```
Error triggering deployment for photo abc123: GitHub API error: 401
AUTOMATIC DEPLOYMENT FAILED. Manual deployment required: ./deploy.sh
```

## Fallback to Manual Deployment

If automatic deployment fails (GitHub API issues, token expired, etc.), you can always deploy manually:

```bash
./deploy.sh
```

The photo is still uploaded successfully - it just won't appear on the static site until you run manual deployment.

## User Experience

### From User's Perspective

1. **Upload photo** → Sees "Photo uploaded successfully!" message
2. **Photo appears immediately** in gallery (loaded from Firestore)
3. **Wait 2-3 minutes** → Photo persists in static site JSON
4. **Refresh page** → Photo still there (now from JSON)

**Note:** Photos appear immediately because they load dynamically from Firestore. The automatic deployment ensures they persist in the static JSON files for faster loading.

## Configuration

### GitHub Token

The Cloud Functions use a GitHub personal access token stored in Firebase config:

```bash
# View current config
firebase functions:config:get

# Set GitHub token (if needed)
firebase functions:config:set github.token="YOUR_GITHUB_TOKEN"

# Deploy functions to use new config
firebase deploy --only functions
```

**Token Requirements:**
- Scope: `repo` (full repository access)
- Permissions: Write access to trigger workflows

**Create token:**
1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate new token (classic)
3. Select `repo` scope
4. Copy token and set in functions config

### Disable Auto-Deployment

If you want to disable automatic deployment temporarily:

**Option 1: Delete the functions**
```bash
firebase functions:delete onPhotoUpload
firebase functions:delete onPhotoDelete
```

**Option 2: Comment out in code**
Edit `functions/index.js` and comment out the exports:
```javascript
// exports.onPhotoUpload = functions.firestore...
// exports.onPhotoDelete = functions.firestore...
```

Then redeploy:
```bash
firebase deploy --only functions
```

## Troubleshooting

### Deployment not triggering

**Check:**
1. Cloud Function deployed: `firebase functions:list`
2. GitHub token configured: `firebase functions:config:get`
3. Function logs for errors: `firebase functions:log --only onPhotoUpload`
4. GitHub Actions workflow exists: Check `.github/workflows/deploy.yml`

### Deployment triggered but failed

**Check:**
1. GitHub Actions logs: https://github.com/Former-Stranger/concert-website/actions
2. Workflow errors (permissions, secrets, etc.)
3. Firebase deploy errors in Actions log

### Photos appear but don't persist

**Symptom:** Photos show up immediately but disappear after refresh

**Cause:** Automatic deployment failed or didn't run

**Solution:**
1. Check function logs for errors
2. Run manual deployment: `./deploy.sh`
3. Verify photos in `website/data/concert_details/{id}.json`

### Function deployment fails

**Error:** `GitHub token not configured`

**Solution:**
```bash
firebase functions:config:set github.token="YOUR_TOKEN"
firebase deploy --only functions
```

## Cost Considerations

### Cloud Functions

**Free Tier:**
- 2M invocations/month
- 400k GB-seconds compute time
- 200k GHz-seconds compute time

**Typical Usage:**
- Photo upload: 1 invocation (~1 second runtime)
- Photo delete: 1 invocation (~1 second runtime)
- Well within free tier for normal usage

**Estimated:**
- 100 photos uploaded/month = 100 invocations
- Cost: $0 (within free tier)

### GitHub Actions

**Free Tier (Public Repositories):**
- Unlimited minutes
- Unlimited storage

**Cost:** $0 (public repo)

## Performance

### Deployment Time

Typical timeline after photo upload:
```
0:00 - Photo upload completes
0:01 - Cloud Function triggers
0:02 - GitHub Actions starts
0:15 - Firestore export completes
0:45 - Firebase deploy starts
2:00 - Deployment completes
2:30 - CDN propagates (global)
```

**Total time:** 2-3 minutes from upload to live

### Optimization

If you have many photos being uploaded simultaneously:
- Functions handle them individually
- Each triggers separate deployment
- GitHub Actions may queue multiple runs
- Consider batching if this becomes an issue

## Future Enhancements

### Possible Improvements

1. **Batch Deployments**: Wait 5 minutes and batch multiple photo uploads
2. **Selective Export**: Only export affected concert details
3. **Webhook Notifications**: Send notification when deployment completes
4. **Deployment Queue**: Show pending deployments in UI
5. **Manual Trigger**: Add "Deploy Now" button for immediate deployment

## Related Documentation

- **Photo Upload Feature**: See [PHOTO_UPLOAD_FEATURE.md](PHOTO_UPLOAD_FEATURE.md)
- **Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Cloud Functions**: See Firebase Console > Functions

## Summary

The automatic deployment feature ensures photos uploaded by users appear on the static website within 2-3 minutes without any manual intervention. This provides a seamless experience while maintaining the performance benefits of a static site with JSON data files.

**Benefits:**
- ✅ No manual deployment needed
- ✅ Photos appear automatically
- ✅ Works for uploads and deletions
- ✅ Fallback to manual if needed
- ✅ Free tier covers normal usage
- ✅ User-friendly experience
