# ⚡ Quick Fix for Google OAuth

## The Problem
"ERR_CONNECTION_REFUSED" means your backend isn't running when Google tries to redirect back.

## Solution

### Step 1: Make Sure Backend is Running

Open a terminal and run:

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!** The backend must stay running.

### Step 2: Verify Backend is Accessible

Open another terminal and test:

```bash
curl http://localhost:8000/health
```

Should return: `{"status":"ok","app":"ChiefOfStaffBackend"}`

### Step 3: Check Your `.env` File

Make sure `backend/.env` has:

```env
GOOGLE_CLIENT_ID=your_actual_client_id
GOOGLE_CLIENT_SECRET=your_actual_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
FRONTEND_URL=http://localhost:3000
```

### Step 4: Google Cloud Console Setup

**CRITICAL**: The redirect URI in Google Console must match EXACTLY:

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click on your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", make sure you have:
   ```
   http://localhost:8000/auth/google/callback
   ```
   - No `https`
   - No trailing slash
   - Exact match

4. **IMPORTANT**: Add test user:
   - Go to "OAuth consent screen"
   - Under "Test users", click "+ ADD USERS"
   - Add: `harisankar@sentellent.com`
   - Save

### Step 5: Test the Flow

1. **Backend running** ✅ (port 8000)
2. **Frontend running** ✅ (port 3000)
3. Open: http://localhost:3000
4. Click: "🔗 Connect Google"
5. Sign in with Google
6. Grant permissions
7. Should redirect back and log you in!

## Common Issues

### "redirect_uri_mismatch"
- Check Google Console redirect URI matches `.env` exactly
- Wait 2-3 minutes after changing (Google caches)

### "ERR_CONNECTION_REFUSED"
- Backend not running → Start it!
- Wrong port → Check it's on 8000
- Firewall blocking → Check Windows Firewall

### "invalid_client"
- Wrong Client ID/Secret in `.env`
- Restart backend after changing `.env`

### Callback shows JSON instead of redirecting
- Fixed! Make sure you have latest code
- Restart backend

## Still Not Working?

1. Check backend logs for errors
2. Check browser console (F12) for errors
3. Verify backend is accessible: `curl http://localhost:8000/health`
4. Test callback directly: `curl http://localhost:8000/auth/google/callback?code=test`

---

**Remember**: Backend MUST be running before clicking "Connect Google"!
