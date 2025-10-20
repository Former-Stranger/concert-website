# Email Setup Walkthrough - Follow Along!

I've set up three email features for you:

1. ✉️ **Welcome emails** - Sent to new users when they sign up
2. 📸 **Photo notifications** - Sent to your friend when someone uploads a photo
3. 💬 **Comment notifications** - Sent to your friend when someone comments

All emails come from **noreply@earplugsandmemories.com** and use SendGrid's **free tier** (100 emails/day).

---

## Step 1: Create SendGrid Account (5 minutes)

1. Open https://signup.sendgrid.com/ in a new tab
2. Sign up with your email (no credit card needed!)
3. Check your email and verify your account
4. Answer the onboarding questions:
   - "What's your role?" → Choose whatever fits
   - "How will you send?" → Select **"Integrate using our Web API or SMTP Relay"**
   - Click through to dashboard

**✅ Check:** You should now see the SendGrid dashboard

---

## Step 2: Create API Key (2 minutes)

1. In SendGrid dashboard, click **Settings** (left sidebar) → **API Keys**
2. Click the blue **"Create API Key"** button (top right)
3. Name it: `Firebase Functions`
4. Select **"Restricted Access"**
5. Scroll down to **"Mail Send"** and toggle it to **"Full Access"**
6. Click **"Create & View"**
7. **COPY THE API KEY** - it starts with `SG.` and is very long
   - ⚠️ You won't be able to see it again!
   - Keep this window open or paste it somewhere safe

**✅ Check:** You have copied a key that looks like: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

## Step 3: Verify Your Domain (10 minutes)

This lets you send emails from `noreply@earplugsandmemories.com`.

1. In SendGrid dashboard, go to **Settings** → **Sender Authentication**
2. Click **"Authenticate Your Domain"**
3. Select your DNS host (where you manage earplugsandmemories.com)
   - Common options: GoDaddy, Namecheap, Cloudflare, etc.
4. Follow the instructions - you'll need to add **3 CNAME records** to your DNS

**The DNS records will look like this:**

```
Type: CNAME
Host: em1234.earplugsandmemories.com
Value: u12345.wl.sendgrid.net

Type: CNAME
Host: s1._domainkey.earplugsandmemories.com
Value: s1.domainkey.u12345.wl.sendgrid.net

Type: CNAME
Host: s2._domainkey.earplugsandmemories.com
Value: s2.domainkey.u12345.wl.sendgrid.net
```

5. Add these 3 records to your DNS provider
6. Come back to SendGrid and click **"Verify"**
   - May take a few minutes for DNS to propagate
   - If it doesn't work immediately, wait 10-15 minutes and try again

**✅ Check:** SendGrid shows your domain as "Verified" with a green checkmark

### Alternative: Quick Start Without Domain Verification

If you want to test NOW before doing DNS setup:

1. Go to **Settings** → **Sender Authentication** → **Verify a Single Sender**
2. Enter your personal email (Gmail, etc.)
3. Verify it
4. You can send emails from your verified email temporarily
   - Display name will still show "Earplugs & Memories"
   - But email address will be your personal one until you verify the domain

---

## Step 4: Configure Firebase (2 minutes)

Now let's add the SendGrid API key and your friend's email to Firebase.

Open Terminal and run these commands:

```bash
# Navigate to your project
cd /Users/akalbfell/Documents/Jay/concert-website

# Set SendGrid API key (paste the key you copied earlier)
firebase functions:config:set sendgrid.key="PASTE_YOUR_SENDGRID_API_KEY_HERE"

# Set notification email (your friend's email where notifications go)
firebase functions:config:set notify.email="your-friend@email.com"
```

**Example:**
```bash
firebase functions:config:set sendgrid.key="SG.abc123xyz456..."
firebase functions:config:set notify.email="jay@example.com"
```

**Verify it worked:**
```bash
firebase functions:config:get
```

You should see:
```json
{
  "sendgrid": {
    "key": "SG.abc123..."
  },
  "notify": {
    "email": "your-friend@email.com"
  },
  "github": {
    "token": "..."
  }
}
```

**✅ Check:** Both `sendgrid.key` and `notify.email` appear in the output

---

## Step 5: Deploy to Firebase (3 minutes)

Deploy the new functions:

```bash
firebase deploy --only functions
```

This will:
- Upload 3 new functions: `sendWelcomeEmail`, `notifyPhotoUpload`, `notifyComment`
- Take 2-3 minutes to deploy
- Show success message when done

**✅ Check:** You see "✔  Deploy complete!" message

---

## Step 6: Test It! (5 minutes)

### Test Welcome Email

1. Go to https://earplugsandmemories.com
2. Sign up with a new email/password account
3. Check the email inbox - you should receive a welcome email from `noreply@earplugsandmemories.com`

### Test Photo Notification

1. Sign in to your site
2. Go to any concert page
3. Upload a photo
4. Check your friend's email - they should receive a notification about the photo upload

### Test Comment Notification

1. On a concert page, add a comment (if comments are enabled)
2. Check your friend's email - they should receive a notification about the comment

---

## Troubleshooting

### "The from address does not match a verified Sender Identity"

**Problem:** Domain not verified yet
**Solution:** Complete Step 3 (domain verification) or use single sender verification temporarily

### Emails not arriving

**Check these:**
1. Look in spam/junk folder
2. Check Firebase Functions logs: `firebase functions:log`
3. Check SendGrid dashboard → Activity Feed to see if email was sent
4. Verify config is set: `firebase functions:config:get`

### DNS verification taking forever

**Solution:**
- Wait 24 hours for DNS to fully propagate
- Use https://dnschecker.org to check if CNAME records are live
- Try the "Single Sender Verification" option as a temporary workaround

---

## What Emails Look Like

### Welcome Email
**To:** New user
**From:** noreply@earplugsandmemories.com
**Subject:** Welcome to Earplugs & Memories! 🎵
**Content:** Personalized greeting with features overview and CTA button

### Photo Notification
**To:** Your friend's email
**From:** noreply@earplugsandmemories.com
**Subject:** 📸 New Photo: [Concert Name]
**Content:** Who uploaded, which concert, caption (if any), link to view

### Comment Notification
**To:** Your friend's email
**From:** noreply@earplugsandmemories.com
**Subject:** 💬 New Comment: [Concert Name]
**Content:** Who commented, which concert, comment text, link to view

---

## Costs

- **SendGrid Free Tier:** 100 emails/day forever (3,000/month)
- **Firebase Functions:** Well within free tier
- **DNS Records:** Already included with your domain

**Total: $0/month** 🎉

---

## Command Reference

```bash
# View current config
firebase functions:config:get

# View function logs
firebase functions:log

# View specific function logs
firebase functions:log --only sendWelcomeEmail

# Deploy functions
firebase deploy --only functions

# Test locally (optional)
firebase emulators:start --only functions,auth
```

---

## Next Steps After Setup

Once everything works:

1. Test by creating a test account
2. Upload a test photo
3. Make sure notifications arrive at your friend's email
4. Delete the setup file if you want: `EMAIL_SETUP_WALKTHROUGH.md`
5. Keep `docs/WELCOME_EMAIL_SETUP_REFERENCE.md` for future reference

---

**Questions? Let me know and I'll help troubleshoot!**
