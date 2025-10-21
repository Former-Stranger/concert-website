# User Account Management Guide

This guide explains how to manage user accounts for your concert archive website.

## Overview

User accounts are managed through **Firebase Authentication**. You can view, disable, delete, and manage users directly from the Firebase Console.

---

## Accessing User Management

### Method 1: Direct Link (Fastest)

Go directly to: https://console.firebase.google.com/project/earplugs-and-memories/authentication/users

### Method 2: Through Firebase Console

1. Go to https://console.firebase.google.com
2. Click on your project: **"earplugs-and-memories"**
3. In the left sidebar, click **"Authentication"**
4. Click the **"Users"** tab at the top

---

## What You Can Do

### View All Users

In the Users tab, you'll see a list of all registered users with:
- **Identifier**: Email address or phone number
- **Providers**: How they signed up (Google, Email/Password)
- **Created**: When the account was created
- **Signed In**: Last sign-in time
- **User UID**: Unique identifier for each user

### Search for a User

Use the search bar at the top to find users by:
- Email address
- Display name
- UID

---

## Common Actions

### 1. Disable a User Account

**When to use:** Temporarily prevent a user from signing in (e.g., spam, abuse)

**Steps:**
1. Find the user in the list
2. Click on the user row to open their details
3. Click the **"Disable account"** button in the top right
4. Confirm the action

**What happens:**
- User cannot sign in
- Their data (photos, comments) remains intact
- You can re-enable the account later

**To re-enable:**
1. Go to the disabled user
2. Click **"Enable account"**

---

### 2. Delete a User Account

**When to use:** Permanently remove a user (e.g., user request, spam account)

**⚠️ Warning:** This action cannot be undone!

**Steps:**
1. Find the user in the list
2. Click on the user row
3. Click the **"Delete account"** button (trash icon in top right)
4. Confirm the action

**What happens:**
- User account is permanently deleted
- User can no longer sign in
- **Their data (photos, comments) remains** in Firestore
  - You'll need to manually delete their content if desired

**To also delete user's content:**
1. Note the user's UID before deleting
2. Go to Firestore Database
3. Search for their content using UID:
   - Search `concert_photos` where `user_id == [UID]`
   - Search `concert_comments` where `user_id == [UID]`
4. Delete documents manually

---

### 3. View User Details

**To see detailed information about a user:**

1. Click on any user in the list
2. You'll see:
   - **User UID**: Unique identifier
   - **Email**: User's email address
   - **Display name**: How they appear on the site
   - **Phone number**: If provided
   - **Creation time**: When account was created
   - **Last sign-in**: Most recent login
   - **Providers**: Sign-in methods linked (Google, Email/Password)

---

### 4. Reset User Password (Email/Password Users)

**For users who signed up with email/password:**

Firebase doesn't allow admins to directly reset passwords, but you can:

**Option A: User Self-Service (Recommended)**
- Direct the user to your password reset flow on the website
- They'll receive a password reset email

**Option B: Send Password Reset Email Manually**
1. Go to user's details in Firebase Console
2. Click **"Send password reset email"** (if available)
3. User will receive email with reset link

---

### 5. Change User's Email

1. Click on the user
2. Click on their email address
3. Enter new email address
4. Save changes

**Note:** User will need to verify the new email

---

### 6. Link Multiple Sign-In Methods

Users can link multiple authentication methods (e.g., Google + Email/Password):

This happens automatically when:
- User signs in with Google using same email
- Then creates password login with same email
- Firebase merges them into one account

**To unlink a method:**
1. Go to user details
2. Find the provider you want to unlink
3. Click the X or trash icon next to it

---

## Bulk Operations

### Export User List

**To get a list of all users:**

1. In Authentication → Users
2. Click the **"..."** menu (three dots) in top right
3. Select **"Export users"**
4. Choose format (CSV or JSON)
5. Download the file

**Useful for:**
- Backing up user data
- Analyzing signup patterns
- Migrating to another system

---

### Delete Multiple Users

**Using Firebase Console:**
Unfortunately, the console doesn't support bulk delete. You need to:
- Delete users one by one, OR
- Use Firebase CLI (see below)

**Using Firebase CLI (Advanced):**

```bash
# List all users
firebase auth:export users.json --project earplugs-and-memories

# Delete multiple users (requires custom script)
# Create a script that reads UIDs and calls:
firebase auth:delete [UID] --project earplugs-and-memories
```

---

## Monitoring & Analytics

### View Authentication Activity

1. In Firebase Console → Authentication
2. Click **"Usage"** tab
3. See:
   - Daily active users
   - Sign-ups over time
   - Sign-in methods breakdown

### View Individual User Activity

Firebase doesn't track detailed user activity, but you can:

**Check their content:**
1. Go to Firestore Database
2. Query by user_id:
   - `concert_photos` where `user_id == [UID]`
   - `concert_comments` where `user_id == [UID]`
3. See all their photos and comments

---

## Security Best Practices

### 1. Monitor New Sign-Ups

- Check Authentication → Users regularly
- Look for suspicious patterns (many signups from same IP, spam-looking names)

### 2. Handle Reports

If users report inappropriate content:
1. Find the offending content (photo/comment)
2. Check the user_id field
3. Look up that user in Authentication
4. Decide: disable, warn, or delete

### 3. Your Owner Account

**Keep your owner account secure:**
- Your UID: `jBa71VgYp0Qz782bawa4SgjHu1l1`
- You have special permissions (edit/delete anything)
- Enable 2FA on your Google account
- Don't share your login credentials

---

## Common Scenarios

### Scenario 1: User Requests Account Deletion

1. Go to Authentication → Users
2. Search for their email
3. Delete their account
4. (Optional) Delete their content from Firestore
5. Confirm deletion via email to the user

### Scenario 2: Spam Account

1. Disable the account immediately
2. Check their photos/comments in Firestore
3. Delete any spam content
4. Then permanently delete the account

### Scenario 3: User Forgot Password

**They should use the website's "Forgot Password" feature, but if needed:**
1. Find user in Authentication
2. Send password reset email
3. User clicks link in email to reset

### Scenario 4: Merge Duplicate Accounts

Firebase automatically merges accounts with the same email if:
- They use the same email for different providers

If they used different emails:
1. User should sign in with primary account
2. Manually move their content (if needed)
3. Delete the duplicate account

---

## Limitations

What you **CANNOT** do in Firebase Console:
- ❌ View a user's password (encrypted, not viewable)
- ❌ Force-change a user's password (they must reset it)
- ❌ See detailed activity logs (use Cloud Functions logs for API calls)
- ❌ Bulk delete users easily (need custom script)
- ❌ Email users directly (need separate email service like Resend)

---

## Advanced: Firebase Admin SDK

For more control, you can use the Firebase Admin SDK in Cloud Functions or scripts:

```javascript
// Delete a user
await admin.auth().deleteUser(uid);

// Disable a user
await admin.auth().updateUser(uid, { disabled: true });

// Get user by email
const user = await admin.auth().getUserByEmail(email);

// List all users
const listUsers = await admin.auth().listUsers(1000);
```

See Firebase Admin Auth docs: https://firebase.google.com/docs/auth/admin

---

## Quick Reference

| Task | How To |
|------|--------|
| View all users | Authentication → Users |
| Disable user | Click user → "Disable account" |
| Delete user | Click user → Delete icon |
| Reset password | User must use "Forgot Password" flow |
| Export users | Users tab → "..." menu → "Export users" |
| Search user | Use search bar at top of Users tab |
| View user content | Firestore → Query by user_id |

---

## Support Links

- **Firebase Console**: https://console.firebase.google.com/project/earplugs-and-memories
- **Authentication Users**: https://console.firebase.google.com/project/earplugs-and-memories/authentication/users
- **Firestore Database**: https://console.firebase.google.com/project/earplugs-and-memories/firestore
- **Firebase Auth Docs**: https://firebase.google.com/docs/auth
- **Admin SDK Docs**: https://firebase.google.com/docs/auth/admin

---

**Questions?** Check the Firebase documentation or reach out if you need help with user management!
