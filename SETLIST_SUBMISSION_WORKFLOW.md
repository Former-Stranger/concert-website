# Setlist Submission Workflow

This document explains how the crowd-sourced setlist submission feature works.

## Overview

Anyone visiting the website can submit a setlist.fm URL for concerts that don't have setlists. The submissions are stored in Firestore and require admin approval before being added to the main database.

## User Workflow

1. **Visit a concert without a setlist**
   - Navigate to a concert detail page that doesn't have a setlist
   - You'll see "No Setlist Available" message

2. **Submit a setlist.fm URL**
   - Below the "No Setlist Available" message, there's a submission form
   - Paste the setlist.fm URL (e.g., `https://www.setlist.fm/setlist/artist/year/venue-city-ID.html`)
   - Click "Submit"
   - The system validates the URL and fetches the setlist data from setlist.fm
   - Submission is stored in Firestore for admin review

3. **Confirmation**
   - User sees a success message confirming their submission
   - The submission form disappears after successful submission

## Admin Review Workflow

### Option 1: Web Interface (Recommended for Quick Reviews)

1. **Access the admin page**
   - Sign in as an owner
   - Navigate to `/admin-setlists.html` (link appears in nav when signed in as owner)

2. **Review submissions**
   - See all pending submissions with:
     - Concert details (artist, venue, date)
     - Setlist preview
     - Submitter information
     - Setlist.fm URL

3. **Approve or Reject**
   - Click "Approve" to accept the submission
   - Click "Reject" to decline (with optional reason)
   - Status is updated in Firestore

### Option 2: Command Line (For Bulk Processing)

**Step 1: Sync from Firestore to SQLite**

```bash
# Run this to download pending submissions from Firestore to local database
python3 scripts/sync_firestore_submissions.py
```

This script:
- Connects to Firestore
- Fetches all pending submissions
- Stores them in the local SQLite `pending_setlist_submissions` table

**Step 2: Review Submissions**

```bash
# List all pending submissions
python3 scripts/review_setlist_submissions.py list

# View detailed information about a specific submission
python3 scripts/review_setlist_submissions.py view <submission_id>
```

**Step 3: Approve or Reject**

```bash
# Approve a submission (imports into database)
python3 scripts/review_setlist_submissions.py approve <submission_id> <your_email@example.com>

# Reject a submission
python3 scripts/review_setlist_submissions.py reject <submission_id> <your_email@example.com> "Reason for rejection"
```

When you approve a submission:
- Setlist data is imported into the `setlists` and `setlist_songs` tables
- The submission status is updated to "approved"

**Step 4: Regenerate Web Data**

```bash
# Export updated data to JSON for the website
python3 scripts/export_to_web.py

# Regenerate individual concert detail pages
python3 scripts/generate_concert_pages.py
```

**Step 5: Deploy Changes**

```bash
# Deploy the updated JSON files and concert detail pages
firebase deploy --only hosting
```

## Database Schema

### Firestore Collection: `pending_setlist_submissions`

```javascript
{
  concertId: number,           // Concert ID from the main database
  setlistfmUrl: string,        // Full URL to setlist.fm
  setlistfmId: string,         // Extracted ID from URL
  submittedByEmail: string,    // Email of submitter (or "anonymous")
  submittedByName: string,     // Name of submitter (or "Anonymous")
  submittedAt: timestamp,      // When submitted
  status: string,              // "pending", "approved", or "rejected"
  reviewedAt: timestamp?,      // When reviewed (optional)
  reviewedBy: string?,         // Email of reviewer (optional)
  rejectionReason: string?,    // Reason if rejected (optional)
  setlistData: object          // Full JSON from setlist.fm API
}
```

### SQLite Table: `pending_setlist_submissions`

```sql
CREATE TABLE pending_setlist_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concert_id INTEGER NOT NULL,
    setlistfm_url TEXT NOT NULL,
    setlistfm_id TEXT NOT NULL,
    submitted_by_email TEXT,
    submitted_by_name TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',
    reviewed_by_email TEXT,
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    setlist_data TEXT,  -- JSON string
    FOREIGN KEY (concert_id) REFERENCES concerts(id),
    UNIQUE(concert_id, setlistfm_id)
);
```

## Files

### Frontend
- `website/concert.html` - Concert detail page with submission form
- `website/js/setlist-submission.js` - Handles submission to Firestore
- `website/js/concert.js` - Shows submission form for concerts without setlists
- `website/admin-setlists.html` - Admin interface for reviewing submissions

### Backend Scripts
- `scripts/submit_setlist.py` - Direct submission to SQLite (for testing/admin use)
- `scripts/sync_firestore_submissions.py` - Sync Firestore to SQLite
- `scripts/review_setlist_submissions.py` - Review, approve, or reject submissions
- `scripts/export_to_web.py` - Export database to JSON for website
- `scripts/generate_concert_pages.py` - Generate individual concert detail pages

### Database
- `database/migrations/add_pending_setlists.sql` - Schema for pending submissions table
- `firestore.rules` - Security rules allowing anyone to submit, only owners to review

## Security

- **Submissions**: Anyone can create submissions (anonymous or authenticated)
- **Reviews**: Only authenticated owners can read, approve, or reject submissions
- **Validation**:
  - URL format is validated before submission
  - Setlist data is fetched from setlist.fm API to verify it exists
  - Duplicate submissions for the same concert are prevented

## API Key

The setlist.fm API key is stored in:
- `website/js/setlist-submission.js` (for web submissions)
- `scripts/submit_setlist.py` (for direct submissions)

**API Key:** `DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE`

## Testing

### Test the Web Submission

1. Find a concert without a setlist (red X icon in concerts list)
2. Click on that concert
3. Scroll down to see the submission form
4. Paste a valid setlist.fm URL
5. Click Submit
6. Check Firestore console to see the submission

### Test the CLI Workflow

```bash
# Create a test submission directly
python3 scripts/submit_setlist.py 307 "https://www.setlist.fm/setlist/phish/2025/hampton-coliseum-hampton-va-3449d4b.html" "test@example.com" "Test User"

# List pending
python3 scripts/review_setlist_submissions.py list

# View details
python3 scripts/review_setlist_submissions.py view 1

# Approve
python3 scripts/review_setlist_submissions.py approve 1 "admin@example.com"

# Export and deploy
python3 scripts/export_to_web.py
python3 scripts/generate_concert_pages.py
firebase deploy --only hosting
```

## Troubleshooting

### "Invalid setlist.fm URL format"
- Make sure the URL follows this pattern: `https://www.setlist.fm/setlist/artist/year/venue-city-ID.html`
- The ID at the end is required (alphanumeric, usually 7-8 characters)

### "Could not find setlist on setlist.fm"
- The setlist might have been deleted or made private on setlist.fm
- Double-check the URL in a browser first

### "A setlist has already been submitted for this concert"
- Someone already submitted a setlist for this concert
- Check the admin interface for pending submissions

### Firestore permissions error
- Make sure you're signed in as an owner to access the admin interface
- Check that Firestore rules were deployed: `firebase deploy --only firestore:rules`

### Sync script can't connect to Firestore
- Make sure Firebase Admin SDK is installed: `pip3 install firebase-admin`
- Set up Application Default Credentials or set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- You may need to download a service account key from Firebase Console

## Future Enhancements

Possible improvements for the future:

1. **Email notifications** when a setlist is submitted
2. **Automatic import** for trusted submitters after X approved submissions
3. **Edit submissions** before approval (fix song names, etc.)
4. **Search setlist.fm directly** from the submission form
5. **Batch approval** of multiple submissions at once
6. **Statistics** on submission activity and contributors
7. **Reward system** for frequent, accurate contributors
