# Concert Archive Website - User Guide

**For Admin/Owner Use**

This guide will walk you through how to manage your concert archive website. Everything is designed to be simple - just click, type, and save!

---

## Table of Contents
1. [Logging In](#logging-in)
2. [Adding a New Concert](#adding-a-new-concert)
3. [Editing Concert Details](#editing-concert-details)
4. [Uploading Photos](#uploading-photos)
5. [Deleting Photos](#deleting-photos)
6. [Managing Setlist Submissions](#managing-setlist-submissions)
7. [Deleting a Concert](#deleting-a-concert)
8. [Adding Personal Notes](#adding-personal-notes)
9. [Managing Comments](#managing-comments)
10. [Managing User Accounts](#managing-user-accounts)
11. [Email Notifications](#email-notifications)
12. [Troubleshooting Common Issues](#troubleshooting-common-issues)

---

## Logging In

### Step 1: Go to the Website
Open your web browser and go to: **https://earplugsandmemories.com**

### Step 2: Click "Sign In"
Look in the top-right corner of the page. You'll see a "Sign In with Google" button.

**What you'll see:**
- An orange "Sign In with Google" button in the header

### Step 3: Sign In with Google
Click the button and sign in with your Google account (the one that's been set up as the owner).

**After signing in:**
- The "Sign In" button will change to show your name and photo
- You'll see new buttons appear throughout the site (like "Add Concert", "Edit", "Delete")
- These buttons are only visible to you as the owner

---

## Adding a New Concert

### Step 1: Navigate to Add Concert Page
From any page on the site, look for the **"Add Concert"** link in the navigation menu at the top.

Or go directly to: **https://earplugsandmemories.com/add-concert.html**

### Step 2: Fill Out the Form

You'll see a form with several fields. Here's what each one means:

**Concert Date** *(Required)*
- Click the calendar icon and select the date of the concert
- Format: Month/Day/Year

**Venue Name** *(Required)*
- Type the name of the venue (e.g., "Madison Square Garden")
- As you type, matching venues from your database will appear
- If the venue already exists, click on it to auto-fill the city/state
- If it's a new venue, just type the name and fill in city/state below

**City** *(Required)*
- Type the city where the concert took place

**State** *(Required)*
- Type the 2-letter state code (e.g., "NY", "CA")

**Artist Name** *(Required)*
- Type the name of the main artist/band
- As you type, matching artists from your database will appear
- Click on an existing artist, or type a new name

**Supporting Act** *(Optional)*
- If there was an opening band, type their name here
- Leave blank if there was no opener

**Festival Name** *(Optional)*
- If this was part of a festival or multi-artist show, type the name here
- Examples: "Lollapalooza", "Multi-Artist Show"
- Leave blank for regular concerts

**Notes** *(Optional)*
- Add any personal notes about the concert
- These notes are private - only you can see them

### Step 3: Submit the Form
Click the **"Add Concert"** button at the bottom.

**What happens next:**
- You'll see a success message
- The concert is added to the database
- The website automatically updates (takes 2-3 minutes)
- You'll be redirected to view all concerts

---

## Editing Concert Details

Sometimes you need to fix a date, change an artist name, or update venue information.

### Step 1: Find the Concert
Navigate to the specific concert you want to edit. You can:
- Go to the **Concerts** page and click on the concert
- Search for the concert using the search box

### Step 2: Click "Edit Concert"
On the concert detail page, look for the **"Edit Concert"** button near the top (below the concert title).

**Note:** You'll only see this button if you're logged in as the owner.

### Step 3: Edit the Information
A popup window will appear with a form. You can edit:

**Date**
- Click the calendar to change the date

**Venue Name**
- Type a new venue name
- If you change to an existing venue, the city/state will auto-update

**City/State**
- Update the location if needed

**Artist Name**
- Type a new artist name
- **Important:** Changing the artist name will update which artist page shows this concert
- If the artist already exists in your database, it will link to that artist
- If it's a new artist, you'll be asked if you want to create a new artist record

**Supporting Act**
- Add, change, or remove the opening act

**Festival Name**
- Add, change, or remove the festival name

### Step 4: Save Changes
Click **"Save Changes"** at the bottom of the popup.

**What happens next:**
- You'll see a success message
- The concert information is updated immediately
- The website automatically rebuilds with the new information (2-3 minutes)

**Important Note about Artist Names:**
If you change the artist name and that artist doesn't exist yet, you'll get a popup asking:
- **"OK"** - Create a new artist (use this for artists you haven't added before)
- **"Cancel"** - Keep the old artist link (use this if you made a typo)

---

## Uploading Photos

You can upload photos to any concert. All signed-in users can upload photos, but as owner you can delete any photo.

### Step 1: Navigate to the Concert
Go to the concert detail page where you want to upload a photo.

### Step 2: Click "Upload Photo"
Scroll down to the **Photos** section. You'll see an **"Upload Photo"** button.

**Note:** You must be logged in to upload photos.

### Step 3: Select Your Photo
- Click **"Upload Photo"**
- A popup window will appear
- Click **"Choose File"** or drag and drop a photo
- Select a photo from your computer

**Photo requirements:**
- Must be a JPG, JPEG, or PNG file
- Maximum size: 10 MB
- The photo will automatically be resized before uploading (so it loads fast on the website)

### Step 4: Add a Caption (Optional)
Type a caption or description for the photo in the text box.

### Step 5: Upload
Click the **"Upload"** button.

**What happens next:**
- You'll see a progress bar
- After upload completes, the photo appears in the gallery
- The website automatically rebuilds with the new photo (2-3 minutes)

**Tips:**
- Photos are automatically compressed for faster loading
- Photos are stored securely in Firebase Storage
- Each photo shows who uploaded it and when

---

## Deleting Photos

You can delete any photo as the owner (or users can delete their own photos).

### Step 1: Find the Photo
Navigate to the concert and scroll to the **Photos** section.

### Step 2: Click the Delete Button
Hover over a photo - you'll see a **red trash icon** appear in the top-right corner of the photo.

Click the trash icon.

### Step 3: Confirm Deletion
A popup will ask: **"Are you sure you want to delete this photo?"**

- Click **"OK"** to delete the photo permanently
- Click **"Cancel"** to keep the photo

**What happens next:**
- The photo is immediately removed from the page
- The photo file is deleted from storage
- The website automatically rebuilds (2-3 minutes)

**Warning:** Deleting a photo cannot be undone!

---

## Managing Setlist Submissions

Users can submit setlist.fm URLs for concerts that don't have setlists yet. You review and approve these submissions.

### Step 1: Check for Pending Submissions
When you're logged in, you'll see a badge with a number next to **"Pending Setlists"** in the navigation menu. This shows how many submissions are waiting.

### Step 2: Go to Pending Setlists Page
Click **"Pending Setlists"** in the navigation menu.

Or go directly to: **https://earplugsandmemories.com/admin-setlists.html**

### Step 3: Review Each Submission
You'll see a list of pending submissions. Each one shows:
- Concert name and date
- Who submitted it and when
- The setlist.fm URL they provided

### Step 4: Approve or Reject

**To Approve:**
1. Click the green **"Approve"** button
2. The setlist will be imported from setlist.fm
3. The concert page will update with the full setlist
4. The submission is removed from the pending list
5. Website automatically rebuilds (2-3 minutes)

**To Reject:**
1. Click the red **"Reject"** button
2. Confirm you want to reject it
3. The submission is removed from the pending list
4. The concert remains without a setlist

**Why reject?**
- Wrong concert
- Invalid or broken setlist.fm URL
- Duplicate submission
- Setlist already exists

---

## Deleting a Concert

Sometimes you need to remove a concert entirely (duplicate entry, wrong information, etc.).

### Step 1: Navigate to the Concert
Go to the concert detail page you want to delete.

### Step 2: Click "Delete Concert"
Look for the red **"Delete Concert"** button near the top of the page (next to the Edit button).

**Note:** You'll only see this button if you're logged in as the owner.

### Step 3: Confirm Deletion
A popup will ask: **"Are you sure you want to delete this concert?"**

**Warning:** This will delete:
- The concert record
- The setlist (if any)
- All photos for this concert
- All comments/notes

Type **"DELETE"** (all caps) in the text box to confirm.

Click **"OK"** to permanently delete, or **"Cancel"** to keep the concert.

**What happens next:**
- The concert is immediately removed from the database
- All associated data is deleted
- The website automatically rebuilds (2-3 minutes)
- You're redirected to the concerts list page

**Warning:** This cannot be undone!

---

## Adding Personal Notes

You can add private notes to any concert. These notes are only visible to you (the owner).

### Step 1: Navigate to the Concert
Go to the concert detail page where you want to add notes.

### Step 2: Scroll to Personal Notes Section
Scroll down below the setlist and photos. You'll see a section called **"Personal Notes"**.

### Step 3: Add or Edit Notes
- If there are no notes yet, click **"Add Note"**
- If notes already exist, click **"Edit"**
- Type your notes in the text box
- Click **"Save"** when done

**What you can write:**
- Personal memories from the concert
- Who you went with
- Special moments or highlights
- Anything you want to remember

**Privacy:**
- These notes are completely private
- Only you (the owner) can see them
- They don't appear on the public site

---

## Managing Comments

Users can post comments on concerts. As the owner, you can delete any comment (for moderation purposes), and users can edit/delete their own comments.

### Viewing Comments

Navigate to any concert detail page and scroll down to the **"Comments"** section.

You'll see:
- User's name and profile photo
- When the comment was posted (e.g., "2 hours ago")
- The comment text

### What Users Can Do

**Regular users:**
- Post comments (must be signed in)
- Edit their own comments
- Delete their own comments

**Owner (you):**
- Delete ANY comment (for moderation/spam removal)

### Deleting a Comment

As the owner, you'll see a **red "Delete" button** on all comments.

**To delete a comment:**
1. Find the comment you want to remove
2. Click the red **"Delete"** button
3. Confirm deletion in the popup
4. The comment is immediately removed

**Use this for:**
- Spam comments
- Inappropriate content
- Off-topic or abusive posts

### Comment Persistence

**Important:** Comments remain visible even if a user deletes their account. This is intentional so you can:
- See comment history
- Identify spam patterns
- Keep legitimate comments from former users

You can always delete individual comments as needed.

---

## Managing User Accounts

You can view, disable, and delete user accounts through the Firebase Console.

### Accessing User Management

Go to: **https://console.firebase.google.com/project/earplugs-and-memories/authentication/users**

Or:
1. Go to https://console.firebase.google.com
2. Click on "earplugs-and-memories" project
3. Click "Authentication" in the left sidebar
4. Click the "Users" tab

### What You'll See

A list of all registered users with:
- Email address
- How they signed up (Google, Facebook, Email/Password)
- When they created their account
- Last sign-in time
- User ID (UID)

### Common Actions

**Search for a User:**
- Use the search bar to find users by email

**Disable a User:**
1. Click on the user
2. Click "Disable account"
3. User can no longer sign in (but their data remains)
4. You can re-enable them later

**Delete a User:**
1. Click on the user
2. Click the trash icon (Delete account)
3. Confirm deletion
4. **Note:** Their comments and photos remain in the database
5. To delete their content, you'll need to manually delete photos/comments

**Export User List:**
1. Click the "..." menu in top right
2. Select "Export users"
3. Download CSV or JSON

### When to Disable/Delete Users

**Disable for:**
- Temporary spam/abuse issues
- Testing
- Suspicious activity

**Delete for:**
- User requested account deletion
- Confirmed spam accounts
- Inactive accounts you want to clean up

For detailed instructions, see: **USER_ACCOUNT_MANAGEMENT.md**

---

## Email Notifications

The website automatically sends email notifications for various activities.

### What Emails Are Sent

**1. Welcome Emails** (Automatic)
- Sent to new users when they create an account
- From: noreply@earplugsandmemories.com
- Contains: Welcome message, feature overview, link to site

**2. Photo Upload Notifications** (To You)
- Sent to: akalbfell@gmail.com
- When: Someone uploads a photo
- Contains: Who uploaded, which concert, caption, link to view

**3. Comment Notifications** (To You)
- Sent to: akalbfell@gmail.com
- When: Someone posts a comment
- Contains: Who commented, which concert, comment text, link to view

### Email Settings

Emails are sent via **Resend** (free tier - 100 emails/day).

**To change notification email:**
```bash
firebase functions:config:set notify.email="new-email@example.com"
firebase deploy --only functions
```

**To disable notifications:**
You would need to disable the Cloud Functions or modify them to not send emails.

### Checking Email Logs

View email delivery logs:
```bash
firebase functions:log --only sendWelcomeEmail
firebase functions:log --only notifyPhotoUpload
firebase functions:log --only notifyComment
```

Or check in Resend dashboard: https://resend.com/emails

### Email Limits

- **Free tier**: 100 emails/day (3,000/month)
- **Sender**: noreply@earplugsandmemories.com
- **Domain verified**: Yes

This should be more than enough for your use case.

---

## Troubleshooting Common Issues

### "I don't see the Edit/Delete buttons"

**Solution:**
- Make sure you're logged in
- Click **"Sign In with Google"** in the top-right
- Use the Google account that's been set up as the owner
- Try refreshing the page (press Cmd+Shift+R on Mac, or Ctrl+Shift+R on Windows)

---

### "I get an error when trying to add/edit a concert"

**Solution:**
- Check that you filled in all required fields (marked with *)
- Make sure the date is valid
- Try refreshing the page and trying again
- If it still doesn't work, check that you're logged in

---

### "Photos aren't showing up after upload"

**Solution:**
- Wait 2-3 minutes for the website to automatically rebuild
- Refresh the page (press Cmd+Shift+R on Mac, or Ctrl+Shift+R on Windows)
- Check that the photo was under 10 MB
- Make sure it was a JPG, JPEG, or PNG file

---

### "Changes I made aren't appearing on the site"

**Solution:**
- Wait 2-3 minutes for automatic deployment
- Do a hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
- Clear your browser cache if the issue persists

---

### "I accidentally deleted something"

**Solution:**
- Photos and concerts cannot be recovered once deleted
- For important operations, always double-check before confirming
- Consider keeping backups of concert information externally

---

### "Setlist approval isn't importing the songs"

**Solution:**
- Make sure the setlist.fm URL is correct and complete
- The setlist.fm page must actually have song data
- Try copying the URL again from setlist.fm
- If it still doesn't work, you may need to add the setlist manually

---

### "I see 'Missing or insufficient permissions' error"

**Solution:**
- This usually means you're not logged in, or your account isn't set as the owner
- Sign out and sign back in
- Make sure you're using the correct Google account
- Contact the technical administrator if this persists

---

## Need More Help?

If you run into issues not covered in this guide:

1. **Try a hard refresh first:** Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
2. **Check that you're logged in** with the owner account
3. **Wait a few minutes** for automatic deployments to complete
4. **Contact technical support** if the issue persists

---

## Quick Reference: Common Tasks

| Task | Where to Go | Button to Click |
|------|-------------|-----------------|
| Add new concert | Add Concert page | "Add Concert" |
| Edit concert | Concert detail page | "Edit Concert" |
| Delete concert | Concert detail page | "Delete Concert" |
| Upload photo | Concert detail page | "Upload Photo" |
| Delete photo | Concert detail page | Trash icon on photo |
| Delete comment | Concert detail page | Red "Delete" button |
| Review setlists | Pending Setlists page | "Approve" or "Reject" |
| Add personal note | Concert detail page | "Add Note" or "Edit" |
| Manage users | Firebase Console | Authentication → Users |
| Check email logs | Terminal | `firebase functions:log` |

---

**Last Updated:** October 20, 2025
