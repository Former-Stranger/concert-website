# Full Automation Setup Guide (GitHub Version)

This guide will set up **completely automated deployment** when setlists are approved, using GitHub.

## What Gets Automated

When a setlist is approved:
1. ✅ Cloud Function imports setlist into Firestore (already working)
2. ✅ Cloud Function triggers Cloud Build
3. ✅ Cloud Build pulls code from GitHub
4. ✅ Cloud Build exports data to JSON
5. ✅ Cloud Build deploys to Firebase Hosting
6. ✅ Website is updated automatically (no manual intervention!)

## One-Time Setup Steps

### Step 1: Push Code to GitHub

```bash
cd /Users/akalbfell/Documents/Jay/concert-website

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit for automated deployment"

# Create a new repo on GitHub (go to github.com/new)
# Then add it as remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/concert-website.git
git branch -M main
git push -u origin main
```

### Step 2: Connect Cloud Build to GitHub

1. Go to [Cloud Build GitHub App](https://github.com/apps/google-cloud-build)
2. Click "Configure"
3. Select your GitHub account
4. Choose "Only select repositories"
5. Select the `concert-website` repository
6. Click "Save"

### Step 3: Enable Required APIs

```bash
# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com --project=earplugs-and-memories
```

### Step 4: Create Firebase CI Token

```bash
firebase login:ci
```

This will output a token like: `1//0abc...xyz`

**IMPORTANT:** Save this token securely - you'll need it in the next step.

### Step 5: Store Firebase Token in Secret Manager

```bash
# Replace YOUR_TOKEN_HERE with the token from step 4
echo -n "YOUR_TOKEN_HERE" | gcloud secrets create firebase-token \
  --data-file=- \
  --project=earplugs-and-memories

# Grant Cloud Build access to the secret
PROJECT_NUMBER=$(gcloud projects describe earplugs-and-memories --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding firebase-token \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=earplugs-and-memories
```

### Step 6: Grant Cloud Build Permissions

```bash
# Get the Cloud Build service account
PROJECT_NUMBER=$(gcloud projects describe earplugs-and-memories --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Grant necessary permissions
gcloud projects add-iam-policy-binding earplugs-and-memories \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/firebase.admin"
```

### Step 7: Update cloudbuild.yaml for GitHub

The `cloudbuild.yaml` file needs to be updated to work with GitHub and Secret Manager.

I'll provide the updated version - it should already be in your repo.

### Step 8: Update Cloud Function for GitHub

The Cloud Function needs to reference your GitHub repo instead of Cloud Source Repositories.

I'll provide the updated version.

### Step 9: Deploy the Updated Cloud Function

```bash
firebase deploy --only functions
```

### Step 10: Test the Automation

1. Find a concert without a setlist
2. Submit a setlist.fm URL
3. Approve it in the admin panel
4. Wait 2-3 minutes
5. Check Cloud Build: https://console.cloud.google.com/cloud-build/builds?project=earplugs-and-memories
6. Check the website - the setlist should appear automatically!

## Monitoring

### View Cloud Build history
https://console.cloud.google.com/cloud-build/builds?project=earplugs-and-memories

### View Cloud Function logs
```bash
firebase functions:log
```

### View specific build logs
```bash
gcloud builds log BUILD_ID --project=earplugs-and-memories
```

## Cost Estimate

With minimal traffic:
- Cloud Build: Free tier includes 120 build-minutes/day
- Each deployment takes ~2-3 minutes
- Cost: **$0/month** (well within free tier)

## Troubleshooting

### Build fails with "repository not found"
- Make sure you completed Step 2 (Connect Cloud Build to GitHub)
- Check that the repository name in the Cloud Function matches your GitHub repo

### Build fails with "permission denied"
- Make sure you completed Step 6 (Grant Cloud Build Permissions)
- Verify the Cloud Build service account has `roles/firebase.admin`

### Build fails with "secret not found"
- Make sure you completed Step 5 (Store Firebase Token)
- Verify the secret name is `firebase-token`

### Function triggers but build doesn't start
- Check the function logs: `firebase functions:log`
- Check Cloud Build logs: https://console.cloud.google.com/cloud-build/builds

## Fallback

If automation fails, you can always run manually:
```bash
./deploy.sh
```
