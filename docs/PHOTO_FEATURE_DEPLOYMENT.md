# Photo Upload Feature - Deployment Guide

## Overview

This guide walks through deploying the new concert photo upload feature to your Firebase project.

## What Was Added

### New Files Created
1. **storage.rules** - Firebase Storage security rules
2. **website/js/concert-photos.js** - Photo upload/display module
3. **docs/PHOTO_UPLOAD_FEATURE.md** - Comprehensive feature documentation

### Files Modified
1. **firestore.rules** - Added rules for concert_photos collection
2. **website/js/firebase-config.js** - Added Storage imports
3. **website/concert.html** - Added photo gallery UI
4. **scripts/export_to_web.py** - Added photo metadata export
5. **docs/FIRESTORE_SCHEMA.md** - Added concert_photos schema

## Deployment Steps

### Step 1: Deploy Security Rules

Deploy both Firestore and Storage security rules:

```bash
# From project root directory
cd /Users/akalbfell/Documents/Jay/concert-website

# Deploy Firestore rules
firebase deploy --only firestore:rules

# Deploy Storage rules
firebase deploy --only storage
```

Expected output:
```
✔  Deploy complete!

Firestore Rules: Released
Storage Rules: Released
```

### Step 2: Update firebase.json (Optional)

Add storage rules configuration to firebase.json if not already present:

```json
{
  "firestore": {
    "rules": "firestore.rules"
  },
  "storage": {
    "rules": "storage.rules"
  },
  "functions": {
    "source": "functions"
  },
  "hosting": {
    "public": "website",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ]
  }
}
```

### Step 3: Deploy Website Files

Deploy the updated website with new photo functionality:

```bash
./deploy.sh
```

This will:
1. Export Firestore data to JSON (including photos)
2. Deploy website files to Firebase Hosting

### Step 4: Verify Deployment

1. Visit your website: https://earplugs-and-memories.web.app
2. Sign in with Google
3. Navigate to any concert page
4. You should see:
   - "Photos" section
   - "Upload Photo" button (when signed in)
   - Photo gallery (if photos exist)

### Step 5: Test Photo Upload

1. Click "Upload Photo" button
2. Select an image file
3. Optionally add a caption
4. Click "Upload"
5. Photo should appear in gallery immediately

## Firestore Index Creation

The first time you load photos, Firestore may require a composite index. If you see an error in the browser console:

1. Click the index creation link in the error message, OR
2. Manually create index in Firebase Console:
   - Collection: `concert_photos`
   - Fields to index:
     - `concert_id` (Ascending)
     - `uploaded_at` (Descending)
   - Query scope: Collection

## Troubleshooting

### Issue: "Missing or insufficient permissions" when uploading

**Solution**: Deploy storage rules
```bash
firebase deploy --only storage
```

### Issue: "Failed to create index" error when loading photos

**Solution**: Create the required Firestore index (see Step 5 above)

### Issue: Upload button doesn't appear

**Check**:
1. User is signed in (click "Sign In" button)
2. Browser console for JavaScript errors
3. firebase-config.js includes Storage imports

### Issue: Photos don't persist after page refresh

**Check**:
1. Firestore rules are deployed
2. Browser console for Firestore write errors
3. Photo metadata is being saved to Firestore collection

### Issue: "Storage bucket not found"

**Solution**: Verify Firebase Storage is enabled in Firebase Console:
1. Go to https://console.firebase.google.com/project/earplugs-and-memories/storage
2. If prompted, click "Get Started" to enable Storage
3. Accept default security rules (we'll override with storage.rules)

## Testing Checklist

After deployment, test the following:

- [ ] Sign in with Google
- [ ] Navigate to a concert page
- [ ] See "Upload Photo" button
- [ ] Click upload button, form appears
- [ ] Select image file (< 5MB)
- [ ] Upload completes successfully
- [ ] Photo appears in gallery
- [ ] Click photo to view full size
- [ ] Delete own photo (trash icon appears)
- [ ] Sign out, verify photo still visible
- [ ] Sign in as different user, verify can't delete other's photos
- [ ] Owner can delete any photo

## Cost Monitoring

Monitor Firebase usage in the Firebase Console:

### Storage Usage
- Location: Firebase Console > Storage
- Free tier: 5GB storage, 1GB/day downloads
- Monitor: Total storage used, daily downloads

### Firestore Usage
- Location: Firebase Console > Firestore Database > Usage
- Free tier: 1GB storage, 50k reads/day, 20k writes/day
- Monitor: Document reads, writes, deletes

### Setting Up Alerts

1. Go to Firebase Console > Project Settings > Usage and Billing
2. Set up budget alerts for:
   - Storage: Alert at 80% of free tier (4GB)
   - Downloads: Alert at 80% of free tier (800MB/day)

## Optional Enhancements

### Automatic Deployment on Photo Upload

To automatically deploy the static site when photos are uploaded, add a Cloud Function:

```javascript
// functions/index.js
exports.onPhotoUpload = functions.firestore
  .document('concert_photos/{photoId}')
  .onCreate(async (snap, context) => {
    // Trigger GitHub Actions deployment
    await triggerGitHubDeployment();
  });
```

### Photo Count Display

Update concerts.json to include photo counts:

```python
# In export_to_web.py, section 1 (Export concerts)
# Add photo count to each concert
photos_count_query = db.collection('concert_photos').where('concert_id', '==', concert_id)
photo_count = len(list(photos_count_query.stream()))

concerts.append({
    # ... existing fields ...
    'photo_count': photo_count
})
```

### Thumbnail Generation

For better performance with many photos, consider generating thumbnails using Cloud Functions:

```javascript
exports.generateThumbnail = functions.storage
  .object()
  .onFinalize(async (object) => {
    // Generate thumbnail using Sharp library
    // Save to thumbnails/ directory
  });
```

## Rollback Instructions

If you need to rollback the photo feature:

### Rollback Website
```bash
firebase hosting:rollback
```

### Rollback Firestore Rules
```bash
# Edit firestore.rules to remove concert_photos section
firebase deploy --only firestore:rules
```

### Rollback Storage Rules
```bash
# Edit storage.rules to remove concert_photos section
firebase deploy --only storage
```

## Support & Documentation

For detailed information about the photo upload feature:

- **Feature Documentation**: See [PHOTO_UPLOAD_FEATURE.md](PHOTO_UPLOAD_FEATURE.md)
- **Database Schema**: See [FIRESTORE_SCHEMA.md](FIRESTORE_SCHEMA.md)
- **General Deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md)

## Next Steps

After successful deployment:

1. Announce the feature to users
2. Upload some example photos to seed content
3. Monitor usage and costs
4. Consider implementing suggested enhancements above

## Change Log

**2024-01-XX** - Photo upload feature added
- New Firestore collection: concert_photos
- New Firebase Storage directory: /concert_photos
- Updated security rules for Firestore and Storage
- Added photo gallery to concert pages
- Updated export script to include photo metadata
