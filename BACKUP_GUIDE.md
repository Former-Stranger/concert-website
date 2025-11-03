# Backup & Recovery Guide - Earplugs & Memories V1.0

## What's Stored Where

### ✅ Already Backed Up in GitHub
- **Source Code**: All website files, Cloud Functions, scripts
- **Exported JSON Data**: `website/data/` (1,913 files, ~10MB total)
  - `concerts.json` - Concert list
  - `artists.json` - Artist list
  - `venues.json` - Venue list
  - `songs.json` - Song list
  - `concert_details/` - Individual concert details with setlists
  - `artist_details/` - Artist performance history
  - `venue_details/` - Venue concert history
- **Configuration**: Firebase config, GitHub Actions workflows
- **Version Tag**: `v1.0` marks the current stable release

### 🔥 Stored in Firebase (Needs Regular Backup)

#### Firestore Database (Live Data)
- `concerts` - Concert records
- `artists` - Artist records
- `venues` - Venue records
- `songs` - Song records
- `setlists` - Setlist data
- `pending_setlist_submissions` - Pending imports
- `concert_photos` - Photo metadata
- `users` - User accounts and roles

#### Firebase Storage
- `concert_photos/` - Uploaded concert photos (currently ~2 concerts with photos)

## Quick Backup (Automated)

Run the complete backup script:

```bash
./scripts/backup_all.sh
```

This will:
1. Export all Firestore collections to JSON
2. Download all photos from Firebase Storage
3. Commit and push current code to GitHub
4. Create a timestamped backup directory with everything

Backups are saved to: `backups/YYYY-MM-DD_HH-MM-SS/`

## Manual Backup Steps

### 1. Firestore Database Export

**Option A: Using the backup script**
```bash
python3 scripts/export_firestore_backup.py backups/firestore-$(date +%Y-%m-%d)
```

**Option B: Using Firebase CLI (requires billing account)**
```bash
gcloud firestore export gs://earplugs-and-memories-backups/$(date +%Y-%m-%d)
```

### 2. Firebase Storage (Photos)

```bash
gsutil -m cp -r gs://earplugs-and-memories.firebasestorage.app/concert_photos backups/photos-$(date +%Y-%m-%d)
```

### 3. GitHub Code Backup

Already automatic! Every deployment commits to GitHub. You can also:

```bash
git tag -a backup-$(date +%Y-%m-%d) -m "Backup checkpoint"
git push origin backup-$(date +%Y-%m-%d)
```

## Recovery Procedures

### Restore from Complete Backup

If you have a backup from `./scripts/backup_all.sh`:

```bash
# 1. Restore Firestore
cd backups/YYYY-MM-DD_HH-MM-SS/
firebase firestore:import firestore/

# 2. Restore Photos
gsutil -m cp -r photos/* gs://earplugs-and-memories.firebasestorage.app/

# 3. Restore Code (if needed)
git checkout v1.0
firebase deploy
```

### Restore from GitHub Only

If Firebase is lost but GitHub is intact:

```bash
# 1. Clone repository
git clone https://github.com/Former-Stranger/concert-website.git
cd concert-website
git checkout v1.0

# 2. The exported JSON files in website/data/ contain most of your data
# You can import this back to Firestore using:
python3 scripts/import_from_json.py

# 3. Deploy
npm install -g firebase-tools
firebase deploy
```

### Emergency: Rebuild from Exported JSON

The `website/data/` directory in GitHub contains a complete export of your data:
- All concerts with setlists
- All artists with performance history
- All venues with concert lists
- All songs with play counts

To rebuild Firestore from this data, create a script that reads these JSON files and writes to Firestore.

## Backup Schedule Recommendations

### Automated (Already Running)
- ✅ **Code**: Auto-committed on every deployment via GitHub Actions
- ✅ **Exported JSON**: Auto-exported on every setlist import (~2-3 minutes)

### Manual (Recommended Frequency)
- 📅 **Complete Backup**: Monthly (run `./scripts/backup_all.sh`)
- 📅 **Firestore Export**: Weekly (before major changes)
- 📅 **Photo Backup**: After each photo upload session

## What Happens If...

### GitHub Goes Down
- All code is in GitHub
- Clone to another service or keep local copy
- Recommendation: Fork the repo periodically

### Firebase Goes Down
- **Data**: Last export in `website/data/` + manual Firestore backups
- **Photos**: Manual `gsutil` backups (see above)
- **Site**: Can be hosted elsewhere (Netlify, Vercel, etc.)

### Your Computer Crashes
- ✅ Code is in GitHub
- ✅ Exported data is in GitHub
- ⚠️ Firestore live data needs cloud backups (run backup script to cloud storage)
- ⚠️ Photos need cloud backups

## Cloud Backup Storage Options

For production-grade backups, store backup files in:

1. **Google Cloud Storage** (recommended for Firebase users)
   ```bash
   gsutil cp -r backups/ gs://your-backup-bucket/
   ```

2. **AWS S3**
   ```bash
   aws s3 sync backups/ s3://your-backup-bucket/
   ```

3. **External Drive** (for local testing)
   ```bash
   cp -r backups/ /Volumes/ExternalDrive/concert-backups/
   ```

## Testing Your Backups

**IMPORTANT**: Periodically test that you can actually restore from backups!

```bash
# Create a test Firebase project
firebase projects:create test-restore

# Try restoring to test project
firebase use test-restore
firebase firestore:import backups/YYYY-MM-DD_HH-MM-SS/firestore/

# Verify data loaded correctly
firebase firestore:list-collections
```

## Backup Status Check

To see what's currently backed up:

```bash
# Check Git status
git status
git log --oneline -10

# Check last export time
ls -lht website/data/*.json | head -5

# Check Firestore document counts
python3 -c "
from google.cloud import firestore
db = firestore.Client()
print(f'Concerts: {len(list(db.collection(\"concerts\").stream()))}')
print(f'Setlists: {len(list(db.collection(\"setlists\").stream()))}')
print(f'Artists: {len(list(db.collection(\"artists\").stream()))}')
"

# Check photos
gsutil du -s gs://earplugs-and-memories.firebasestorage.app/concert_photos
```

## Support

For questions about backups:
1. Check this guide first
2. Review backup logs in `backups/*/README.txt`
3. Consult Firebase documentation: https://firebase.google.com/docs/firestore/manage-data/export-import
