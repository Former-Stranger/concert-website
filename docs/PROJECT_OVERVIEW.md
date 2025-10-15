# Concert Archive Website - Project Overview

## What This Project Does

This is a **live concert archive website** that displays 35+ years of concert attendance history with setlists, statistics, and interactive features. Users can browse concerts, view detailed setlists, search by artist/venue/song, and even submit new setlists for approval.

**Live Site**: https://earplugs-and-memories.web.app

## Architecture Overview

This is a **Firebase-based serverless web application** with automated deployment pipelines.

### Technology Stack

- **Frontend**: Static HTML/CSS/JavaScript with Tailwind CSS
- **Hosting**: Firebase Hosting (static file hosting with CDN)
- **Database**: Cloud Firestore (NoSQL database)
- **Cloud Functions**: Node.js serverless functions for automation
- **Authentication**: Firebase Auth (Google Sign-In)
- **CI/CD**: GitHub Actions for automated deployment
- **External API**: Setlist.fm API for importing concert setlists

### Key Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    FIREBASE HOSTING                              │
│         https://earplugs-and-memories.web.app                   │
│                                                                  │
│  Static Website:                                                │
│  - HTML pages (concerts.html, artist.html, etc.)               │
│  - JavaScript (concert.js, auth.js, etc.)                       │
│  - JSON data files (concerts.json, artists.json, etc.)         │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Deploys
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    GITHUB ACTIONS                                │
│                                                                  │
│  Workflow: Deploy to Firebase                                   │
│  1. Export Firestore → JSON files                              │
│  2. Deploy website to Firebase Hosting                         │
│                                                                  │
│  Triggered by:                                                  │
│  - Cloud Function (when setlist approved)                      │
│  - Manual trigger (workflow_dispatch)                          │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Triggers
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   CLOUD FUNCTIONS                                │
│                                                                  │
│  processApprovedSetlist:                                        │
│  - Fetches setlist from setlist.fm API                         │
│  - Imports to Firestore                                         │
│  - Triggers GitHub Actions deployment                           │
│                                                                  │
│  fetchSetlist:                                                  │
│  - HTTP endpoint for client-side setlist validation            │
│                                                                  │
│  triggerDeploy:                                                 │
│  - HTTP endpoint for manual deployment trigger                 │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Writes
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   CLOUD FIRESTORE                                │
│                                                                  │
│  Collections:                                                   │
│  - concerts (basic concert data)                               │
│  - setlists (song-by-song setlist data)                       │
│  - artists (normalized artist names)                           │
│  - venues (normalized venue names)                             │
│  - pending_setlist_submissions (user submissions)              │
│  - concert_notes (owner's private notes)                       │
│  - concert_comments (public comments)                          │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Data Import (One-Time Setup)
```
Excel Spreadsheet → Python scripts → SQLite database → Firestore
```
Original concert data was normalized using Python scripts, stored in SQLite, then migrated to Firestore.

### 2. Live Data Flow
```
User submits setlist URL → Firestore (pending_setlist_submissions)
  ↓
Owner approves in admin panel
  ↓
Cloud Function triggers → Fetches from setlist.fm API
  ↓
Saves to Firestore (concerts + setlists collections)
  ↓
Triggers GitHub Actions workflow
  ↓
Export script reads Firestore → Generates JSON files
  ↓
Firebase Hosting deployment → Website updated
```

### 3. Manual Concert Addition
```
Owner runs: python3 scripts/add_concert.py
  ↓
Prompts for concert details
  ↓
Saves to Firestore (concerts collection)
  ↓
Owner runs: ./deploy.sh (or manual deployment)
  ↓
Website updated with new concert
```

## Project Structure

```
concert-website/
├── website/                    # Static website files
│   ├── *.html                 # Page templates
│   ├── js/                    # JavaScript modules
│   │   ├── firebase-config.js # Firebase SDK setup
│   │   ├── auth.js            # Authentication
│   │   ├── concert.js         # Concert detail page
│   │   ├── setlist-submission.js # Setlist submission
│   │   └── concert-notes.js   # Notes & comments
│   └── data/                  # Exported JSON files (generated)
│       ├── concerts.json      # List of all concerts
│       ├── concert_details/   # Individual concert setlists
│       ├── artists.json       # Artist list with counts
│       ├── artist_details/    # Per-artist concert lists
│       ├── venues.json        # Venue list with counts
│       ├── venue_details/     # Per-venue concert lists
│       ├── songs.json         # Song statistics
│       └── stats.json         # Overall statistics
│
├── functions/                 # Cloud Functions
│   └── index.js              # All Cloud Functions
│
├── scripts/                   # Automation scripts
│   ├── export_to_web.py      # Firestore → JSON export
│   ├── add_concert.py        # Add concert via CLI
│   ├── migrate_to_firestore.py # SQLite → Firestore (one-time)
│   └── fetch_setlists.py     # Bulk setlist import
│
├── database/                  # SQLite database (legacy)
│   └── concerts.db           # Original normalized data
│
├── docs/                      # Documentation
│   ├── PROJECT_OVERVIEW.md   # This file
│   ├── FIRESTORE_SCHEMA.md   # Database schema
│   ├── DEPLOYMENT.md         # Deployment guide
│   └── AUTOMATION_SETUP_GITHUB.md # Setup instructions
│
├── .github/workflows/         # GitHub Actions
│   └── deploy.yml            # Deployment workflow
│
├── firebase.json             # Firebase configuration
├── firestore.rules           # Firestore security rules
└── deploy.sh                 # Manual deployment script
```

## Key Features

### Public Features
- **Browse Concerts**: Searchable list of 1,200+ concerts
- **View Setlists**: Song-by-song setlists for 800+ concerts
- **Artist Pages**: See all concerts by a specific artist
- **Venue Pages**: See all concerts at a specific venue
- **Song Statistics**: Most-played songs, opening/closing songs
- **Comments**: Authenticated users can comment on concerts
- **Submit Setlists**: Anyone can submit setlist.fm URLs for approval

### Owner-Only Features (Authentication Required)
- **Add Concerts**: Form to add new concerts to database
- **Approve Setlists**: Review and approve user submissions
- **Private Notes**: Add personal notes to concerts (owner only)
- **Manage Content**: Edit/delete as needed

### Automated Features
- **Setlist Import**: Automatically fetches from setlist.fm API
- **Data Export**: Generates static JSON from Firestore
- **Auto-Deploy**: Website updates automatically when setlists approved
- **Real-time Updates**: Pending setlist count badge updates live

## Deployment Methods

### Method 1: Automated (Recommended)
When owner approves a setlist submission, Cloud Function automatically:
1. Imports setlist to Firestore
2. Triggers GitHub Actions
3. Exports JSON and deploys to hosting

**No manual intervention needed!**

### Method 2: Manual Script
```bash
./deploy.sh
```

This will:
1. Export Firestore data to JSON files
2. Deploy website to Firebase Hosting

**When to use**: After manually adding concerts, or if automated deployment fails.

**Requirements**:
- `GOOGLE_CLOUD_PROJECT=earplugs-and-memories` environment variable (set in deploy.sh)
- Firebase CLI installed and authenticated
- Application Default Credentials configured

### Method 3: GitHub Actions Manual Trigger
Go to GitHub Actions → Deploy to Firebase → Run workflow

**When to use**: If deploy.sh doesn't work locally, or deploying from different machine.

## Environment Setup

### Required Tools
- Python 3.11+
- Node.js 18+ (for Cloud Functions)
- Firebase CLI: `npm install -g firebase-tools`
- Google Cloud SDK (gcloud CLI)

### Authentication Setup
```bash
# Firebase authentication
firebase login

# Google Cloud authentication (for Firestore access)
gcloud auth application-default login

# Set default project
gcloud config set project earplugs-and-memories
```

### Environment Variables
Set in your shell profile (~/.zshrc or ~/.bashrc):
```bash
export GOOGLE_CLOUD_PROJECT=earplugs-and-memories
```

Or use inline when running scripts:
```bash
GOOGLE_CLOUD_PROJECT=earplugs-and-memories ./deploy.sh
```

## Common Tasks

### Add a New Concert
```bash
python3 scripts/add_concert.py
```
Follow the prompts, then run `./deploy.sh` to publish.

### Approve Pending Setlists
1. Sign in to website as owner
2. Click "Pending Setlists" in navigation
3. Review and approve submissions
4. Website auto-deploys in 2-3 minutes

### Manually Deploy Website
```bash
./deploy.sh
```

### View Cloud Function Logs
```bash
/Users/akalbfell/google-cloud-sdk/bin/gcloud functions logs read --region=us-central1 --project=earplugs-and-memories --limit=30
```

### Test Firestore Connection
```bash
python3 -c "
import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {'projectId': 'earplugs-and-memories'})
db = firestore.client()
concerts = list(db.collection('concerts').limit(1).stream())
print(f'Successfully connected! Found {len(concerts)} concert(s)')
"
```

## Security & Access Control

### Firestore Rules
- **concerts**: Owner can write, everyone can read
- **setlists**: Owner can write, everyone can read
- **pending_setlist_submissions**: Anyone can create, owner can read/update/delete
- **concert_notes**: Owner only
- **concert_comments**: Authenticated users can create, anyone can read

### Owner UID
The owner's Firebase Auth UID is hardcoded in:
- `website/js/auth.js` (line 12): `OWNER_UID = 'jBa71VgYp0Qz782bawa4SgjHu1l1'`
- `firestore.rules` (line 12): Same UID

To find your UID:
```bash
python3 scripts/get_user_uid.py
```

## External Dependencies

### Setlist.fm API
- API Key stored in Cloud Functions environment
- Used for fetching setlist data
- Rate limited: Be careful with bulk imports

### Firebase Services Used
- Hosting (static files + CDN)
- Firestore (database)
- Cloud Functions (serverless compute)
- Authentication (Google Sign-In)
- Security Rules (access control)

### GitHub
- Repository: https://github.com/Former-Stranger/concert-website
- Actions: Automated deployment workflow
- Secrets: FIREBASE_TOKEN, GOOGLE_APPLICATION_CREDENTIALS

## Troubleshooting

### "Project ID is required to access Firestore"
Set the environment variable:
```bash
export GOOGLE_CLOUD_PROJECT=earplugs-and-memories
```

### Deploy script fails with authentication error
Run:
```bash
gcloud auth application-default login
firebase login
```

### Website not updating after deployment
Check:
1. GitHub Actions run status
2. Cloud Function logs for errors
3. Browser cache (hard refresh: Cmd+Shift+R)

### Setlist submission not triggering deployment
Check Cloud Function logs:
```bash
/Users/akalbfell/google-cloud-sdk/bin/gcloud functions logs read processApprovedSetlist --region=us-central1 --project=earplugs-and-memories --limit=20
```

## Performance Considerations

- **Static JSON files**: Fast page loads, no database queries from client
- **CDN caching**: Firebase Hosting uses global CDN
- **Client-side rendering**: All pages rendered in browser, no server load
- **Denormalized data**: JSON files include all needed data (no joins)

## Cost Estimate

With current usage (1,200 concerts, <100 monthly visitors):
- Firebase Hosting: Free tier (10GB storage, 360MB/day transfer)
- Firestore: Free tier (1GB storage, 50k reads/day)
- Cloud Functions: Free tier (2M invocations/month)
- Authentication: Free tier (unlimited)

**Total monthly cost: $0** (well within free tiers)

## Future Enhancement Ideas

- **Mobile app**: React Native or Flutter
- **Social features**: User profiles, concert check-ins
- **Photo uploads**: Concert photos with gallery
- **Audio clips**: Link to recordings when available
- **Advanced search**: Full-text search across all fields
- **Export functionality**: PDF concert history, CSV exports
- **API**: Public API for programmatic access

## Getting Help

For issues or questions about this codebase:
1. Check this documentation in `/docs`
2. Review relevant scripts in `/scripts`
3. Check Cloud Function logs
4. Check GitHub Actions logs
5. Review Firestore security rules

## Additional Documentation

- [Firestore Schema](FIRESTORE_SCHEMA.md) - Database structure
- [Deployment Guide](DEPLOYMENT.md) - Detailed deployment instructions
- [Automation Setup](AUTOMATION_SETUP_GITHUB.md) - GitHub Actions setup
