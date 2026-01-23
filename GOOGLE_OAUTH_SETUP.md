# 🔐 Google OAuth Setup Guide

## Step-by-Step Google Cloud Console Configuration

### 1. Go to Google Cloud Console

Visit: https://console.cloud.google.com/

### 2. Create or Select a Project

- Click on the project dropdown at the top
- Click "New Project" or select an existing one
- Give it a name (e.g., "Chief of Staff AI")

### 3. Enable Required APIs

1. Go to **APIs & Services** > **Library**
2. Search and enable these APIs:
   - ✅ **Gmail API**
   - ✅ **Google Calendar API**
   - ✅ **Google+ API** (for user info)

### 4. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **"+ CREATE CREDENTIALS"** > **"OAuth client ID"**
3. If prompted, configure the OAuth consent screen first:
   - **User Type**: External (unless you have Google Workspace)
   - **App name**: Chief of Staff AI
   - **User support email**: Your email
   - **Developer contact**: Your email
   - **Scopes**: Add these:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/calendar`
     - `https://www.googleapis.com/auth/userinfo.email`
     - `openid`
   - **Test users**: ⚠️ **CRITICAL**: Add `harisankar@sentellent.com` as a test user
   - Click **"SAVE AND CONTINUE"** through all steps

4. Back to Credentials, click **"+ CREATE CREDENTIALS"** > **"OAuth client ID"**
5. **Application type**: Web application
6. **Name**: Chief of Staff AI Web Client
7. **Authorized redirect URIs**: ⚠️ **CRITICAL** - Add these EXACTLY:
   ```
   http://localhost:8000/auth/google/callback
   ```
   (If deploying, also add your production URL)

8. Click **"CREATE"**

### 5. Copy Your Credentials

You'll see:
- **Client ID**: Copy this
- **Client secret**: Copy this (click "Show" if hidden)

### 6. Update Your `.env` File

In `backend/.env`, add/update:

```env
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
FRONTEND_URL=http://localhost:3000
GOOGLE_API_KEY=your_google_api_key_for_gemini
```

### 7. Get Google API Key (for Gemini AI)

1. Go to **APIs & Services** > **Credentials**
2. Click **"+ CREATE CREDENTIALS"** > **"API Key"**
3. Copy the API key
4. (Optional) Restrict the API key to only the APIs you need

### 8. Important Notes

⚠️ **Test User Requirement**:
- You MUST add `harisankar@sentellent.com` as a test user
- This allows them to test your app without Google App verification
- Go to **OAuth consent screen** > **Test users** > **+ ADD USERS**

⚠️ **Redirect URI Must Match Exactly**:
- The URI in Google Console must match exactly what's in your `.env`
- No trailing slashes
- Must be `http://localhost:8000/auth/google/callback` (not `https`)

⚠️ **Backend Must Be Running**:
- The callback URL (`http://localhost:8000/auth/google/callback`) must be accessible
- Make sure your backend is running on port 8000
- Test it: `curl http://localhost:8000/health`

### 9. Testing the OAuth Flow

1. **Start your backend**:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. **Start your frontend**:
   ```bash
   cd frontend
   python -m http.server 3000
   ```

3. **Open**: http://localhost:3000

4. **Click**: "🔗 Connect Google"

5. **Expected flow**:
   - Redirects to Google login
   - You sign in (or use test user account)
   - Grant permissions
   - Redirects back to `http://localhost:8000/auth/google/callback`
   - Backend processes and redirects to frontend with token
   - Frontend stores token and shows main content

### 10. Troubleshooting

#### "ERR_CONNECTION_REFUSED" Error

**Problem**: Backend not running or wrong port

**Solution**:
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not running, start it:
cd backend
python -m uvicorn app.main:app --reload
```

#### "redirect_uri_mismatch" Error

**Problem**: Redirect URI in Google Console doesn't match your `.env`

**Solution**:
1. Check `GOOGLE_REDIRECT_URI` in `backend/.env`
2. Make sure it's exactly: `http://localhost:8000/auth/google/callback`
3. Update Google Console to match exactly
4. Wait a few minutes for changes to propagate

#### "access_denied" Error

**Problem**: User didn't grant permissions or test user not added

**Solution**:
1. Make sure `harisankar@sentellent.com` is added as test user
2. Try logging in with that account
3. Make sure you grant all requested permissions

#### "invalid_client" Error

**Problem**: Wrong Client ID or Secret

**Solution**:
1. Double-check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
2. Make sure there are no extra spaces
3. Restart backend after changing `.env`

#### Callback Returns JSON Instead of Redirecting

**Problem**: Old code (should be fixed now)

**Solution**: Make sure you have the latest `google_auth.py` with redirect logic

### 11. Production Deployment

When deploying to production:

1. **Update Google Console**:
   - Add production redirect URI: `https://yourdomain.com/auth/google/callback`
   - Keep localhost for development

2. **Update `.env`**:
   ```env
   GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/google/callback
   FRONTEND_URL=https://yourdomain.com
   ```

3. **Submit for Verification** (if going public):
   - Go to OAuth consent screen
   - Click "PUBLISH APP"
   - Fill out verification form

---

## Quick Checklist

- [ ] Project created in Google Cloud Console
- [ ] Gmail API enabled
- [ ] Calendar API enabled
- [ ] OAuth consent screen configured
- [ ] `harisankar@sentellent.com` added as test user
- [ ] OAuth 2.0 credentials created
- [ ] Redirect URI added: `http://localhost:8000/auth/google/callback`
- [ ] Client ID and Secret copied to `.env`
- [ ] Google API Key created and added to `.env`
- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Tested OAuth flow end-to-end

---

**Need Help?** Check the backend logs for detailed error messages!
