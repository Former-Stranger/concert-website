# Full Automation Setup Guide

This guide will set up **completely automated deployment** when setlists are approved.

## What Gets Automated

When a setlist is approved:
1. ✅ Cloud Function imports setlist into Firestore (already working)
2. ✅ Cloud Function triggers Cloud Build
3. ✅ Cloud Build exports data to JSON
4. ✅ Cloud Build deploys to Firebase Hosting
5. ✅ Website is updated automatically (no manual intervention!)

## One-Time Setup Steps

### Step 1: Push Code to Cloud Source Repositories

```bash
cd /Users/akalbfell/Documents/Jay/concert-website

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit for automated deployment"

# Add Cloud Source Repository as remote
gcloud source repos create concert-website
git remote add google https://source.developers.google.com/p/earplugs-and-memories/r/concert-website
git push google main
```

### Step 2: Enable Required APIs

```bash
# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com --project=earplugs-and-memories

# Enable Cloud Source Repositories API
gcloud services enable sourcerepo.googleapis.com --project=earplugs-and-memories
```

### Step 3: Create Firebase CI Token

```bash
firebase login:ci
```

This will output a token like: `1//0abc...xyz`

Save this token - you'll need it in the next step.

### Step 4: Add Firebase Token to Cloud Build

```bash
# Replace YOUR_TOKEN_HERE with the token from step 3
gcloud builds submit --config=cloudbuild.yaml \
  --substitutions=_FIREBASE_TOKEN="YOUR_TOKEN_HERE" \
  --no-source
```

Or add it as a Secret Manager secret (more secure):

```bash
# Create secret
echo -n "YOUR_TOKEN_HERE" | gcloud secrets create firebase-token \
  --data-file=- \
  --project=earplugs-and-memories

# Grant Cloud Build access to the secret
gcloud secrets add-iam-policy-binding firebase-token \
  --member="serviceAccount@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=earplugs-and-memories
```

### Step 5: Grant Cloud Build Permissions

```bash
# Get the Cloud Build service account
PROJECT_NUMBER=$(gcloud projects describe earplugs-and-memories --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Grant necessary permissions
gcloud projects add-iam-policy-binding earplugs-and-memories \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/firebase.admin"
```

### Step 6: Deploy the Updated Cloud Function

```bash
firebase deploy --only functions
```

### Step 7: Test the Automation

1. Find a concert without a setlist
2. Submit a setlist.fm URL
3. Approve it in the admin panel
4. Wait 2-3 minutes
5. Check the website - the setlist should appear automatically!

## Monitoring

View Cloud Build logs:
```bash
gcloud builds list --project=earplugs-and-memories
```

View specific build:
```bash
gcloud builds log BUILD_ID --project=earplugs-and-memories
```

View Cloud Function logs:
```bash
firebase functions:log
```

## Troubleshooting

### Build fails with "repository not found"
Make sure you pushed code to Cloud Source Repositories in Step 1.

### Build fails with "permission denied"
Make sure you completed Step 5 (Grant Cloud Build Permissions).

### Function triggers but build doesn't start
Check the function logs: `firebase functions:log`

## Cost Estimate

With minimal traffic:
- Cloud Build: Free tier includes 120 build-minutes/day
- Each deployment takes ~2-3 minutes
- Cost: **$0/month** (well within free tier)

## Fallback

If automation fails, you can always run manually:
```bash
./deploy.sh
```
