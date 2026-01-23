# 🔧 Fix: CloudFront Redirect Issue

## The Problem

You're seeing `d3hxk28k5oxq99.cloudfront.net` in the Google OAuth flow, which means:
- Google Console redirect URI is set to CloudFront (production)
- But you're testing locally on `localhost:8000`
- Google redirects to CloudFront → 404 error

## Solution: Add Localhost Redirect URI

### Step 1: Update Google Cloud Console

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click on your **OAuth 2.0 Client ID**
3. Under **"Authorized redirect URIs"**, you should have:
   ```
   https://d3hxk28k5oxq99.cloudfront.net/auth/google/callback
   ```
4. **ADD** this localhost URI (keep the CloudFront one too):
   ```
   http://localhost:8000/auth/google/callback
   ```
5. Click **"SAVE"**

**Important**: You can have MULTIPLE redirect URIs - one for local dev, one for production!

### Step 2: Verify Your `.env` File

Make sure `backend/.env` has:

```env
# For LOCAL development (what you're using now)
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# For production (when deployed)
# GOOGLE_REDIRECT_URI=https://d3hxk28k5oxq99.cloudfront.net/auth/google/callback
```

### Step 3: Restart Backend

After updating `.env`, restart your backend:

```bash
# Stop the current backend (Ctrl+C)
# Then restart:
cd backend
python -m uvicorn app.main:app --reload
```

### Step 4: Test Again

1. Open: http://localhost:3000
2. Click: "🔗 Connect Google"
3. Should now redirect to `localhost:8000/auth/google/callback` instead of CloudFront

## Why This Happened

- Your Google OAuth was configured for production (CloudFront)
- But you're testing locally
- Google uses the redirect URI from the OAuth client config, not from your `.env`
- Solution: Add BOTH URIs in Google Console

## Quick Checklist

- [ ] Added `http://localhost:8000/auth/google/callback` to Google Console
- [ ] Kept CloudFront URI for production
- [ ] Updated `.env` with localhost redirect URI
- [ ] Restarted backend
- [ ] Tested OAuth flow

---

**After fixing, the OAuth flow should work locally!** 🎉
