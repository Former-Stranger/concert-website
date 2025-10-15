# Setting Up Firebase Admin SDK Credentials

To run the migration script, you need to set up Firebase Admin SDK credentials. Here are the steps:

## Option 1: Using gcloud CLI (Recommended if you have it)

If you have the Google Cloud SDK installed:

```bash
gcloud auth application-default login
```

Then run the migration script:
```bash
python3 scripts/migrate_to_firestore.py --dry-run
```

## Option 2: Using a Service Account Key

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `earplugs-and-memories`
3. Click the gear icon (Settings) → **Project settings**
4. Go to the **Service accounts** tab
5. Click **Generate new private key**
6. Save the JSON file to your computer (e.g., `firebase-admin-key.json`)
7. **DO NOT commit this file to git!**
8. Set the environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/firebase-admin-key.json"
```

9. Run the migration script:
```bash
python3 scripts/migrate_to_firestore.py --dry-run
```

## Quick Test

Once you've set up credentials, test with a dry run first:

```bash
# Dry run (no data written)
python3 scripts/migrate_to_firestore.py --dry-run

# Actual migration
python3 scripts/migrate_to_firestore.py
```
