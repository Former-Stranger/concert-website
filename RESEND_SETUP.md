# Resend Email Setup - Simple Guide

I've switched to **Resend** which is easier to sign up for than SendGrid. Same features, same free tier (100 emails/day).

## Quick Setup (15 minutes total)

### Step 1: Create Resend Account (3 minutes)

1. Go to https://resend.com/signup
2. Sign up with your email
3. Verify your email address
4. You're in! No credit card needed.

**✅ Check:** You should see the Resend dashboard

---

### Step 2: Add Your Domain (5 minutes)

1. In Resend dashboard, click **"Domains"** in the left sidebar
2. Click **"Add Domain"**
3. Enter: `earplugsandmemories.com`
4. Click **"Add"**

Resend will show you DNS records to add. You'll need to add **3 records**:

```
Type: TXT
Name: @ (or leave blank)
Value: resend._domainkey.earplugsandmemories.com

Type: MX
Name: @ (or leave blank)
Priority: 10
Value: feedback-smtp.resend.com

Type: TXT
Name: _dmarc
Value: v=DMARC1; p=none; pct=100; rua=mailto:dmarc@earplugsandmemories.com
```

5. Go to your DNS provider (GoDaddy, Cloudflare, Namecheap, etc.)
6. Add these 3 DNS records
7. Come back to Resend and click **"Verify DNS Records"**
   - May take 5-10 minutes for DNS to propagate
   - If it doesn't verify immediately, wait a bit and try again

**✅ Check:** Domain shows as "Verified" in Resend

---

### Step 3: Get API Key (1 minute)

1. In Resend dashboard, click **"API Keys"** in the left sidebar
2. Click **"Create API Key"**
3. Name it: `Firebase Functions`
4. Permission: **"Sending access"**
5. Click **"Create"**
6. **COPY THE API KEY** - it starts with `re_`
   - ⚠️ You won't see it again!
   - Keep this window open or save it somewhere

**✅ Check:** You have an API key like: `re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### Step 4: Configure Firebase (2 minutes)

Open Terminal and run:

```bash
cd /Users/akalbfell/Documents/Jay/concert-website

# Set Resend API key
firebase functions:config:set resend.key="PASTE_YOUR_API_KEY_HERE"

# Set your friend's email for notifications
firebase functions:config:set notify.email="friend@email.com"
```

**Example:**
```bash
firebase functions:config:set resend.key="re_abc123xyz456..."
firebase functions:config:set notify.email="jay@gmail.com"
```

Verify it worked:
```bash
firebase functions:config:get
```

Should show:
```json
{
  "resend": {
    "key": "re_abc123..."
  },
  "notify": {
    "email": "friend@email.com"
  }
}
```

**✅ Check:** Both values appear correctly

---

### Step 5: Deploy (3 minutes)

```bash
firebase deploy --only functions
```

Wait for deployment to complete (2-3 minutes).

**✅ Check:** You see "✔  Deploy complete!"

---

## Test It!

### Test Welcome Email
1. Go to https://earplugsandmemories.com
2. Create a new account with email/password
3. Check that email inbox for welcome email from `noreply@earplugsandmemories.com`

### Test Photo Notification
1. Sign in to your site
2. Upload a photo to any concert
3. Check your friend's email for notification

### Test Comment Notification
1. Add a comment to any concert
2. Check your friend's email for notification

---

## What You Get

### 📧 Welcome Emails
- **To:** New users
- **From:** noreply@earplugsandmemories.com
- **When:** User signs up with email/password
- **Content:** Welcome message with features overview

### 📸 Photo Notifications
- **To:** Your friend (notify.email)
- **From:** noreply@earplugsandmemories.com
- **When:** Someone uploads a photo
- **Content:** Who uploaded, which concert, caption, link

### 💬 Comment Notifications
- **To:** Your friend (notify.email)
- **From:** noreply@earplugsandmemories.com
- **When:** Someone posts a comment
- **Content:** Who commented, which concert, comment text, link

---

## Troubleshooting

### Domain not verifying
- Wait 15-30 minutes for DNS to propagate worldwide
- Check DNS with: https://dnschecker.org
- Make sure you added ALL 3 records correctly
- Try the "Verify" button again

### Emails not sending
Check logs:
```bash
firebase functions:log
```

Check Resend dashboard → "Logs" to see if emails were sent

### "Domain not verified" error
You need to complete Step 2 (domain verification) first

### Want to test without domain verification?
Unfortunately Resend requires domain verification for all emails. But it's quick and easy - just add those 3 DNS records!

---

## Costs

- **Resend:** FREE forever (100 emails/day, 3,000/month)
- **Firebase Functions:** FREE (well within free tier)
- **Total:** $0/month 🎉

---

## Commands Reference

```bash
# View config
firebase functions:config:get

# View logs
firebase functions:log

# Deploy
firebase deploy --only functions

# Test specific function
firebase functions:log --only sendWelcomeEmail
```

---

## Need Help?

1. Check Resend dashboard → "Logs" to see email delivery status
2. Check Firebase logs: `firebase functions:log`
3. Verify domain is verified in Resend
4. Make sure DNS records are added correctly

**Common issue:** If emails aren't sending, it's usually because domain isn't verified yet. DNS can take up to 24 hours but usually works in 10-15 minutes.

---

That's it! Once you verify your domain and deploy, emails will start working automatically. Let me know if you hit any snags!
