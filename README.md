# Concert Archive Website

A comprehensive web application for tracking and managing concert history, built with Firebase and vanilla JavaScript.

## Project Overview

This is a full-featured concert archive website that allows tracking 35+ years of concert history with features including:
- Concert database with setlists, photos, and personal notes
- Artist and venue tracking with statistics
- User authentication with Google, Email/Password, and Email Link (passwordless)
- Photo uploads with automatic deployment
- Setlist submission workflow
- Edit and delete functionality for concert data
- Automatic data export and deployment pipeline

**Live Site:** https://earplugsandmemories.com

## Tech Stack

### Frontend
- **HTML/CSS/JavaScript** - Vanilla JS, no framework
- **Tailwind CSS** - Utility-first CSS framework (via CDN)
- **Font Awesome** - Icons
- **Google Fonts** - Bebas Neue & Roboto Slab

### Backend & Database
- **Firebase Firestore** - NoSQL database for all concert data
- **Firebase Authentication** - User authentication (Google, Email/Password, Email Link)
- **Firebase Storage** - Photo storage with automatic resizing
- **Firebase Hosting** - Static site hosting
- **Firebase Cloud Functions** - Serverless functions for triggers
- **Resend** - Email service for notifications (100 emails/day free)

### Deployment & CI/CD
- **GitHub Actions** - Automated deployment on data changes
- **Python** - Data export scripts
- **Firebase CLI** - Deployment tooling

## Project Structure

```
concert-website/
├── .github/
│   └── workflows/
│       └── deploy.yml              # GitHub Actions workflow
├── functions/
│   ├── index.js                    # Cloud Functions (triggers, auth)
│   └── package.json
├── scripts/
│   ├── export_to_web.py           # Export Firestore → JSON
│   ├── fix_*.py                    # Data correction scripts
│   └── deploy.sh                   # Full deployment script
├── website/                        # Static website files
│   ├── data/                       # Exported JSON data
│   │   ├── concerts.json
│   │   ├── artists.json
│   │   ├── venues.json
│   │   ├── songs.json
│   │   ├── stats.json
│   │   ├── concert_details/       # Individual concert files
│   │   ├── artist_details/        # Individual artist files
│   │   └── venue_details/         # Individual venue files
│   ├── js/                         # JavaScript modules
│   │   ├── firebase-config.js     # Firebase initialization
│   │   ├── auth.js                # Authentication module
│   │   ├── main.js                # Home page logic
│   │   ├── concerts.js            # Concerts list page
│   │   ├── concert.js             # Concert detail page
│   │   ├── concert-photos.js      # Photo upload module
│   │   ├── concert-notes.js       # Notes & comments
│   │   ├── setlist-submission.js  # Setlist submission
│   │   └── ...
│   ├── index.html                  # Home page
│   ├── concerts.html               # Concerts list
│   ├── concert.html                # Concert detail
│   ├── artists.html                # Artists list
│   ├── artist.html                 # Artist detail
│   ├── venues.html                 # Venues list
│   ├── venue.html                  # Venue detail
│   ├── songs.html                  # Songs list
│   ├── add-concert.html            # Add new concert
│   ├── admin-setlists.html         # Pending setlists admin
│   └── favicon.svg                 # Site icon
├── firestore.rules                 # Firestore security rules
├── storage.rules                   # Storage security rules
├── firebase.json                   # Firebase configuration
└── README.md                       # This file
```

## Key Features

### 1. Concert Management
- **View concerts** - Chronological list with search and filters
- **Concert details** - Full setlist, venue, date, artists
- **Add concerts** - Form to add new concerts to database
- **Edit concerts** - Owner can edit date, venue, artist, supporting act
- **Delete concerts** - Owner can remove concerts

### 2. Setlist Management
- **Setlist display** - Organized by sets and encores
- **Setlist submission** - Users can submit setlist.fm URLs
- **Admin approval** - Owner reviews and approves submissions
- **Auto-import** - Setlists imported from setlist.fm API

### 3. Photo Features
- **Photo uploads** - Authenticated users can upload concert photos
- **Auto-resize** - Client-side image resizing before upload
- **Photo gallery** - Display photos in concert detail pages
- **Photo deletion** - Uploader or owner can delete photos
- **Automatic deployment** - Photo uploads trigger site rebuild

### 4. Artist & Venue Tracking
- **Artist pages** - Shows all concerts per artist with statistics
- **Venue pages** - Shows all concerts per venue
- **Top artists** - Ranked by concert count
- **Top venues** - Ranked by visit count
- **Artist linking** - Concerts properly linked via artist_id

### 5. Authentication & Permissions
- **Google Sign-In** - OAuth authentication
- **Email/Password Authentication** - Standard email/password signup and login
- **Owner privileges** - Special permissions for site owner
- **User photos** - All authenticated users can upload photos
- **Admin functions** - Edit/delete concerts, approve setlists, delete any comment/photo

### 6. Comments & Community
- **User comments** - Authenticated users can comment on concerts
- **Edit comments** - Users can edit their own comments
- **Delete comments** - Users can delete their own comments, owner can delete any
- **Comment moderation** - Admin can remove inappropriate comments
- **Persistent history** - Comments remain visible even if user deletes account

### 7. Email Notifications
- **Welcome emails** - New users receive welcome email on signup
- **Photo upload notifications** - Admin receives email when photos are uploaded
- **Comment notifications** - Admin receives email when comments are posted
- **Professional sender** - All emails from noreply@earplugsandmemories.com
- **Powered by Resend** - Free tier (100 emails/day)

### 8. Personal Features
- **Personal notes** - Owner can add private notes to concerts
- **"On This Date"** - Shows concerts from this date in history
- **User account management** - Admin can disable/delete user accounts

## Data Architecture

### Firestore Collections

**concerts**
```javascript
{
  id: "1063",
  show_number: 1062,
  date: "2022-10-07",
  venue_name: "Capitol Theatre",
  venue_id: "84",
  city: "Port Chester",
  state: "NY",
  festival_name: "Multi-Artist Show",
  artists: [
    {
      artist_id: "266",
      artist_name: "Jeff Beck",
      role: "headliner",  // or "opener", "festival_performer"
      position: 1
    }
  ],
  has_setlist: true,
  created_at: timestamp,
  updated_at: timestamp
}
```

**artists**
```javascript
{
  id: "48",
  canonical_name: "Billy Joel",
  created_at: timestamp
}
```

**venues**
```javascript
{
  id: "84",
  canonical_name: "Capitol Theatre",
  city: "Port Chester",
  state: "NY",
  created_at: timestamp
}
```

**setlists**
```javascript
{
  id: "auto-generated",
  concert_id: "1063",
  setlistfm_url: "https://www.setlist.fm/...",
  song_count: 20,
  has_encore: true,
  songs: [
    {
      position: 1,
      name: "Freeway Jam",
      set_name: "Main Set",
      encore: 0,
      is_cover: true,
      cover_artist: "Jeff Beck"
    }
  ]
}
```

**concert_photos**
```javascript
{
  id: "auto-generated",
  concert_id: "1063",
  user_id: "abc123",
  user_name: "John Doe",
  user_photo: "https://...",
  storage_path: "concert_photos/1063/filename.jpg",
  download_url: "https://...",
  caption: "Great show!",
  file_size: 2048576,
  file_type: "image/jpeg",
  uploaded_at: timestamp
}
```

**pending_setlist_submissions**
```javascript
{
  id: "auto-generated",
  concert_id: "1063",
  setlistfm_url: "https://www.setlist.fm/...",
  submitted_by: "user@example.com",
  submitted_at: timestamp,
  status: "pending"  // or "approved", "rejected"
}
```

**concert_notes**
```javascript
{
  id: "concert_id",  // Same as concert ID
  notes: "Personal notes about this concert",
  created_at: timestamp,
  updated_at: timestamp
}
```

**concert_comments**
```javascript
{
  id: "auto-generated",
  concert_id: "1063",
  user_id: "abc123",
  user_name: "John Doe",
  user_photo: "https://...",  // Optional
  comment: "Great concert!",
  created_at: timestamp,
  updated_at: timestamp  // Only set when edited
}
```

### Static JSON Files

The website uses exported JSON files for fast loading:
- `concerts.json` - All concerts (basic info)
- `artists.json` - All artists with concert counts
- `venues.json` - All venues with concert counts
- `songs.json` - All songs with play counts
- `stats.json` - Overall statistics
- `concert_details/{id}.json` - Individual concert with full setlist
- `artist_details/{id}.json` - Individual artist with all concerts
- `venue_details/{id}.json` - Individual venue with all concerts

## Setup & Installation

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Firebase CLI: `npm install -g firebase-tools`
- Google Cloud account with Firebase project

### 1. Clone Repository
```bash
git clone https://github.com/Former-Stranger/concert-website.git
cd concert-website
```

### 2. Install Dependencies
```bash
# Install Cloud Functions dependencies
cd functions
npm install
cd ..

# Install Python dependencies for export script
pip install firebase-admin
```

### 3. Firebase Setup

Create a Firebase project at https://console.firebase.google.com

Enable these services:
- **Firestore Database** - Production mode
- **Authentication** - Enable Google and Email/Password providers
- **Storage** - Production mode
- **Hosting** - Enable hosting

### 4. Configure Firebase Locally

```bash
# Login to Firebase
firebase login

# Initialize project (select existing project)
firebase init

# Select:
# - Firestore
# - Functions
# - Hosting
# - Storage
```

### 5. Set Up Environment Variables

Create service account key from Firebase Console:
1. Project Settings → Service Accounts
2. Generate new private key
3. Save as `~/gcloud-key.json`

```bash
export GOOGLE_APPLICATION_CREDENTIALS=~/gcloud-key.json
export GOOGLE_CLOUD_PROJECT=your-project-id
```

### 6. Update Configuration Files

**firebase.json** - Already configured

**firestore.rules** - Update owner UID:
```javascript
function isOwner() {
  return isAuthenticated() && request.auth.uid == 'YOUR_UID_HERE';
}
```

**website/js/firebase-config.js** - Add your Firebase config:
```javascript
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abcdef"
};
```

**website/js/auth.js** - Update owner UID:
```javascript
const OWNER_UID = 'YOUR_UID_HERE';
```

### 7. Deploy Firebase Rules & Functions

```bash
# Deploy Firestore rules
firebase deploy --only firestore:rules

# Deploy Storage rules
firebase deploy --only storage:rules

# Deploy Cloud Functions
firebase deploy --only functions
```

### 8. Add Your Domain (Optional)

In Firebase Console:
1. Hosting → Add custom domain
2. Follow DNS setup instructions
3. Add domain to Authentication → Authorized domains

## Deployment

### Automatic Deployment (GitHub Actions)

The project uses GitHub Actions to automatically deploy when data changes:

1. **Triggers:**
   - Photo upload
   - Photo delete
   - Setlist approval
   - New concert added
   - Concert edited
   - Manual deploy

2. **Process:**
   - Cloud Function sends `repository_dispatch` to GitHub
   - GitHub Actions workflow runs
   - Exports Firestore data to JSON
   - Deploys to Firebase Hosting

**Setup GitHub Actions:**

1. Get Firebase token:
```bash
firebase login:ci
```

2. Add secrets to GitHub repository:
   - `FIREBASE_TOKEN` - Token from above
   - `GOOGLE_APPLICATION_CREDENTIALS` - Service account JSON (entire file content)

3. Push `.github/workflows/deploy.yml` to repository

### Manual Deployment

```bash
# Full deployment (export + deploy)
./deploy.sh

# Or step by step:
python3 scripts/export_to_web.py
firebase deploy --only hosting
```

## Development Workflow

### Adding a New Concert

1. Navigate to https://yourdomain.com/add-concert.html
2. Fill in concert details
3. Submit form
4. Concert added to Firestore
5. Automatic deployment triggered

### Editing a Concert

1. Navigate to concert detail page
2. Click "Edit" button (owner only)
3. Modify fields:
   - Date
   - Artist name (automatically updates artist_id)
   - Venue name
   - City / State
   - Supporting act
   - Festival name
4. Save changes
5. Automatic deployment triggered

### Adding Setlist

**Option 1: Owner adds directly**
1. Add setlist data to Firestore `setlists` collection
2. Export and deploy

**Option 2: User submits for approval**
1. User visits concert without setlist
2. Pastes setlist.fm URL
3. Submission added to `pending_setlist_submissions`
4. Owner reviews at https://yourdomain.com/admin-setlists.html
5. Owner approves or rejects
6. If approved, setlist imported and deployed

### Uploading Photos

1. User signs in with Google
2. Navigate to concert detail page
3. Click "Upload Photo" button
4. Select image file
5. Add optional caption
6. Image automatically resized client-side
7. Uploaded to Firebase Storage
8. Metadata added to Firestore
9. Automatic deployment triggered

## Security

### Firestore Security Rules

The database uses strict security rules:

- **Concerts** - Read: all, Write: owner only
- **Artists** - Read: all, Write: owner only
- **Venues** - Read: all, Write: owner only
- **Setlists** - Read: all, Write: owner only
- **Photos** - Read: all, Upload: authenticated users, Delete: uploader or owner
- **Notes** - Read/Write: owner only
- **Comments** - Read: all, Create: authenticated users, Edit: author only, Delete: author or owner
- **Pending Submissions** - Read: owner, Create: anyone

### Storage Security Rules

- Photos stored in `concert_photos/{concert_id}/{filename}`
- Upload: authenticated users only
- Download: anyone
- Delete: uploader or owner
- Max size: 10MB

## Troubleshooting

### "Missing or insufficient permissions" error
- Check Firestore security rules are deployed
- Verify user is authenticated
- Check owner UID matches in rules and auth.js

### Photos not appearing
- Check Firebase Storage is enabled
- Verify storage rules are deployed
- Check composite index exists for concert_photos query
- Hard refresh browser (Cmd+Shift+R)

### Authentication not persisting
- Check auth state callback is properly initialized
- Verify custom domain is in Firebase authorized domains
- Clear browser cache and cookies

### Automatic deployment not triggering
- Check GitHub Actions secrets are set correctly
- Verify Cloud Functions are deployed
- Check GitHub Actions workflow file includes all trigger types
- Review Cloud Functions logs in Firebase Console

## Maintenance

### Adding New Concerts
Use the web form at `/add-concert.html` - no manual database work needed.

### Backing Up Data
```bash
# Export all Firestore data
firebase firestore:export gs://your-bucket/backups/$(date +%Y%m%d)
```

### Updating Statistics
Statistics are automatically regenerated on each deployment when `export_to_web.py` runs.

## API Reference

### Cloud Functions

**triggerManualDeploy**
- **URL:** `https://us-central1-your-project.cloudfunctions.net/triggerManualDeploy`
- **Method:** POST
- **Description:** Triggers GitHub Actions deployment

**onPhotoUpload**
- **Trigger:** Firestore onCreate on `concert_photos/{photoId}`
- **Action:** Triggers automatic deployment and sends notification email

**onPhotoDelete**
- **Trigger:** Firestore onDelete on `concert_photos/{photoId}`
- **Action:** Triggers automatic deployment

**sendWelcomeEmail**
- **Trigger:** Firebase Auth onCreate
- **Action:** Sends welcome email to new users

**notifyPhotoUpload**
- **Trigger:** Firestore onCreate on `concert_photos/{photoId}`
- **Action:** Sends notification email to admin

**notifyComment**
- **Trigger:** Firestore onCreate on `concert_comments/{commentId}`
- **Action:** Sends notification email to admin

**processApprovedSetlist**
- **Trigger:** Firestore onWrite on `pending_setlist_submissions/{submissionId}`
- **Action:** Auto-imports approved setlists from setlist.fm

## Future Enhancements

Potential features to add:
- [ ] Advanced search and filtering
- [ ] Concert statistics charts/visualizations
- [ ] Mobile app
- [ ] Export personal concert history
- [ ] Concert reminders for upcoming shows
- [ ] Sharing concerts on social media
- [ ] Venue maps integration
- [ ] Comment reply/threading functionality
- [ ] Email digest of recent activity
- [ ] User profiles with concert history

## Credits

- Built for tracking 35+ years of concert history
- Design inspired by vintage concert poster aesthetics
- Color scheme: Orange (#d4773e) and brown (#2d1b1b) tones

## License

Personal project - All rights reserved.
