# Welcome Email Setup Guide

This guide explains how to configure and deploy the welcome email feature for new user signups using **SendGrid's free tier** (100 emails/day, completely free forever).

## What Was Added

A new Cloud Function `sendWelcomeEmail` that automatically triggers when a user creates an account with email/password authentication. It sends a beautifully formatted HTML welcome email from **noreply@earplugsandmemories.com**.

## Why SendGrid?

- ✅ **100% FREE** - 100 emails/day forever, no credit card required
- ✅ **Professional sender address** - Use noreply@earplugsandmemories.com
- ✅ **No actual email account needed** - Just verify domain ownership
- ✅ **Reliable delivery** - High inbox placement rate
- ✅ **Simple API** - Easy to integrate

## Setup Steps

### 1. Create SendGrid Account (Free)

1. Go to https://signup.sendgrid.com/
2. Sign up with your email (no credit card required)
3. Verify your email address
4. Complete the onboarding questions (select "Integrate using our Web API or SMTP Relay")

### 2. Verify Your Domain

To send from `noreply@earplugsandmemories.com`, you need to verify domain ownership:

1. In SendGrid dashboard, go to **Settings** → **Sender Authentication**
2. Click **Authenticate Your Domain**
3. Choose your DNS host (likely the same place you manage earplugsandmemories.com DNS)
4. Follow the instructions to add DNS records:
   - They'll give you 3 CNAME records to add
   - Add these to your domain's DNS settings
5. Click **Verify** (may take a few minutes for DNS to propagate)

**DNS Records will look like this:**
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

### 3. Create API Key

1. In SendGrid dashboard, go to **Settings** → **API Keys**
2. Click **Create API Key**
3. Name it "Firebase Functions" or "Welcome Emails"
4. Choose **Restricted Access**
5. Under **Mail Send**, enable **Full Access**
6. Click **Create & View**
7. **COPY THE API KEY** (you won't be able to see it again!)
   - It will look like: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 4. Configure Firebase Functions

Set the SendGrid API key in Firebase Functions config:

```bash
firebase functions:config:set sendgrid.key="YOUR_SENDGRID_API_KEY"
```

Example:
```bash
firebase functions:config:set sendgrid.key="SG.abc123xyz456..."
```

Verify it was set:
```bash
firebase functions:config:get
```

You should see:
```json
{
  "sendgrid": {
    "key": "SG.abc123..."
  },
  "github": {
    "token": "..."
  }
}
```

### 5. Deploy the Function

```bash
cd /Users/akalbfell/Documents/Jay/concert-website
firebase deploy --only functions
```

This will:
- Upload the `sendWelcomeEmail` function
- Install SendGrid dependency
- Make the function active

## Testing

### Test with a New User Signup

1. Go to https://earplugsandmemories.com
2. Sign up with a new email/password account
3. Check your inbox for the welcome email from `noreply@earplugsandmemories.com`

### Check Function Logs

View logs to see if the email was sent:

```bash
firebase functions:log --only sendWelcomeEmail
```

Or in Firebase Console:
https://console.firebase.google.com/project/earplugs-and-memories/functions/logs

## Email Content

The welcome email includes:

- **From**: noreply@earplugsandmemories.com
- **Subject**: "Welcome to Earplugs & Memories! 🎵"
- **Personalized greeting** with user's display name
- **Feature highlights**: Upload photos, submit setlists, add comments, explore stats
- **Call-to-action button** linking to the site
- **Styled HTML** with your brand colors (#d4773e orange, #2d1b1b brown)
- **Plain text fallback** for email clients that don't support HTML

### Preview

The email will look like this:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Welcome to Earplugs & Memories!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hi [Name],

Thanks for joining our concert archive community!
We're excited to have you here.

What You Can Do:
📸 Upload Photos
🎼 Submit Setlists
💬 Add Comments
📊 Explore Stats

[Visit Earplugs & Memories] ← Orange button
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Customizing the Email

To customize the email content, edit the `msg` object in `functions/index.js` (lines 503-564).

## Troubleshooting

### Email not sending

**Check the logs**:
```bash
firebase functions:log --only sendWelcomeEmail
```

**Common issues**:

1. **"SendGrid not configured" error**
   - Make sure you ran: `firebase functions:config:set sendgrid.key="..."`
   - Verify with: `firebase functions:config:get`

2. **"The from address does not match a verified Sender Identity"**
   - You need to complete domain verification in SendGrid
   - Go to SendGrid → Settings → Sender Authentication
   - Follow the domain verification steps above

3. **"Invalid API Key" error**
   - Double-check you copied the full API key
   - Create a new API key if needed
   - Make sure it has "Mail Send" permissions

4. **Emails going to spam**
   - Domain verification should prevent this
   - Check SendGrid's spam reports in their dashboard
   - Make sure DNS records are properly configured

### Domain Verification Issues

If domain verification fails:

1. **Check DNS propagation**: Use https://dnschecker.org to verify CNAME records are live
2. **Wait 24-48 hours**: DNS can take time to propagate
3. **Try again**: Click "Verify" button in SendGrid again
4. **Use "Single Sender Verification" temporarily**:
   - In SendGrid → Settings → Sender Authentication → Verify a Single Sender
   - Verify your personal email (e.g., your Gmail)
   - Change `from.email` in the code to use this verified email
   - You can still set `from.name` to "Earplugs & Memories"

### Testing Locally

Test the function locally using Firebase Emulators:

```bash
firebase emulators:start --only functions,auth
```

Then create a test user through the Auth emulator UI.

**Note**: Emails sent from emulator will actually send to real email addresses!

## SendGrid Free Tier Details

### What's Included (FREE Forever):
- ✅ 100 emails per day
- ✅ Email API
- ✅ Domain authentication
- ✅ Email activity dashboard
- ✅ Email validation
- ✅ Spam reports

### Limits:
- 100 emails/day (3,000/month)
- 1 sender identity (or unlimited with domain verification)
- Basic support (community forum)

### Upgrading (if needed in the future):
- **Essentials**: $19.95/month - 50,000 emails/month
- **Pro**: $89.95/month - 100,000 emails/month

**For your use case**: 100 emails/day should be more than enough for new user signups!

## Alternative: Single Sender Verification (Quick Start)

If you want to test immediately without domain verification:

1. In SendGrid, go to **Settings** → **Sender Authentication**
2. Click **Verify a Single Sender**
3. Enter your personal email address
4. Check your email and verify
5. Update the function code to use your verified email:

```javascript
from: {
  email: 'your-verified-email@gmail.com',  // Your verified email
  name: 'Earplugs & Memories'
},
replyTo: 'noreply@earplugsandmemories.com'  // Can be anything
```

This lets you send emails immediately while you work on domain verification.

## Cost Summary

- **SendGrid**: FREE (100 emails/day)
- **Firebase Functions**: FREE (well within free tier)
- **DNS Records**: FREE (you already own the domain)

**Total cost: $0.00/month** 🎉

## Security Notes

- API key stored securely in Firebase Functions config (not in code)
- Config is not committed to git
- Only deployed to production environment
- User creation succeeds even if email fails (graceful degradation)
- SendGrid provides spam protection and rate limiting

## Future Enhancements

Possible improvements:

1. **Email templates**: Use SendGrid's dynamic templates
2. **Email tracking**: Track open rates and clicks
3. **Different email types**: Password reset, concert updates, setlist approved, etc.
4. **Unsubscribe link**: Let users opt out of future emails
5. **Scheduled emails**: "On this day" concert reminders

## Support Resources

- **SendGrid Documentation**: https://docs.sendgrid.com/
- **SendGrid API Reference**: https://docs.sendgrid.com/api-reference/mail-send/mail-send
- **Firebase Functions Logs**: `firebase functions:log`
- **SendGrid Dashboard**: https://app.sendgrid.com/

## Quick Reference Commands

```bash
# Set SendGrid API key
firebase functions:config:set sendgrid.key="YOUR_API_KEY"

# View current config
firebase functions:config:get

# Deploy function
firebase deploy --only functions

# View logs
firebase functions:log --only sendWelcomeEmail

# Test locally
firebase emulators:start --only functions,auth
```

## Next Steps

1. ✅ Create SendGrid account
2. ✅ Verify domain (or use single sender temporarily)
3. ✅ Create API key
4. ✅ Configure Firebase: `firebase functions:config:set sendgrid.key="..."`
5. ✅ Deploy: `firebase deploy --only functions`
6. ✅ Test by creating a new account
7. ✅ Check logs to confirm emails are sending

---

**Need help?** Check the Firebase Functions logs first, then SendGrid's activity dashboard for delivery details.
