# 🧪 Testing Guide - Chief of Staff AI

## Prerequisites

1. **Python 3.11+** installed
2. **PostgreSQL database** (local or Railway.com)
3. **Google Cloud Console** credentials (for OAuth)
4. **Google API Key** (for Gemini AI)

## Step 1: Environment Setup

### Backend Environment Variables

Create/update `backend/.env` with:

```env
# Database (use your Railway PostgreSQL URL or local)
DATABASE_URL=postgresql://user:password@host:port/dbname

# Google OAuth (from Google Cloud Console)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Google API Key (for Gemini AI)
GOOGLE_API_KEY=your_google_api_key

# App Name
APP_NAME=ChiefOfStaffBackend
```

### Important: Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Add `harisankar@sentellent.com` as a **Test User** (as per requirements)
4. Set authorized redirect URI: `http://localhost:8000/auth/google/callback`

## Step 2: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Step 3: Start the Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Test the health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"ok","app":"ChiefOfStaffBackend"}
```

## Step 4: Start the Frontend

Open a **new terminal**:

```bash
cd frontend
python -m http.server 3000
```

Or use any static file server:
- VS Code Live Server extension
- `npx serve .`
- Any other HTTP server

Then open: **http://localhost:3000**

## Step 5: Test the Application

### 5.1 Register/Login

1. Open http://localhost:3000
2. Click **"Register"**
3. Enter email and password
4. Click **"Login"** after registration

### 5.2 Connect Google (Optional but Recommended)

1. Click **"🔗 Connect Google"**
2. You'll be redirected to Google OAuth
3. Sign in with your Google account
4. Grant permissions for Gmail and Calendar
5. You'll be redirected back with a token

### 5.3 Test Basic Chat

Try these messages:
- "Hello, how are you?"
- "What can you help me with?"

### 5.4 Test Memory System ⭐

**Test 1: Store a Preference**
```
You: "I hate 9 AM meetings"
Agent: [Should acknowledge and remember]
```

**Test 2: Verify Memory**
```
You: "What meetings do I have today?"
Agent: [Should mention your preference about 9 AM meetings if relevant]
```

**Test 3: Store Another Preference**
```
You: "I prefer afternoon meetings"
Agent: [Should acknowledge]
```

**Test 4: Test Memory Persistence**
- Log out and log back in
- Ask: "What are my meeting preferences?"
- Agent should remember both preferences

### 5.5 Test Email Integration (Requires Google Connected)

```
You: "What emails did I receive today?"
Agent: [Fetches and lists emails]

You: "What important emails do I have today?"
Agent: [Summarizes important emails and extracts facts]
```

### 5.6 Test Calendar Integration (Requires Google Connected)

```
You: "What meetings do I have today?"
Agent: [Lists today's meetings]

You: "What meetings do I have tomorrow?"
Agent: [Lists tomorrow's meetings]

You: "Create a meeting from 2pm to 3pm"
Agent: [Creates meeting]
```

## Step 6: Verify Memory in Database

You can check if memories are being stored:

```python
# Connect to your PostgreSQL database
# Query the memory table:
SELECT * FROM memory WHERE user_id = 'your-user-id';
```

You should see entries like:
- `key: "meeting_preference"`, `value: "hates 9 AM meetings"`, `source: "chat"`
- `key: "meeting_time_preference"`, `value: "prefers afternoon meetings"`, `source: "chat"`

## Step 7: Test Email Memory Extraction

1. Make sure you have some emails in your Gmail
2. Ask: "What important emails do I have today?"
3. The agent should:
   - Read your emails
   - Extract facts (e.g., "Project X is delayed")
   - Store them in memory with `source: "email"`

## Troubleshooting

### Backend won't start
- Check if port 8000 is available
- Verify DATABASE_URL is correct
- Check all environment variables are set

### Frontend can't connect to backend
- Verify backend is running on port 8000
- Check `API_BASE_URL` in `frontend/app.js`
- Check browser console for CORS errors

### Memory not working
- Check database connection
- Verify memory table exists (should be created automatically)
- Check backend logs for errors

### Google OAuth not working
- Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
- Check redirect URI matches exactly
- Ensure test user is added in Google Cloud Console

### Chat returns errors
- Check if GOOGLE_API_KEY is set (for Gemini AI)
- Verify database connection
- Check backend logs for detailed errors

## Quick Test Commands

```bash
# Test health
curl http://localhost:8000/health

# Test registration
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Test login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Test chat (replace TOKEN with actual token)
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"message":"I hate 9 AM meetings"}'
```

## Expected Behavior

✅ **Memory System Working:**
- Agent remembers preferences from chat
- Agent extracts facts from emails
- Agent uses memories in responses
- Memories persist across sessions

✅ **Integration Working:**
- Gmail API fetches emails
- Calendar API reads events
- OAuth flow completes successfully

✅ **Frontend Working:**
- Login/Register works
- Chat interface functional
- Google OAuth redirects properly
- Messages display correctly

## Next Steps After Testing

1. ✅ Verify memory is stored in database
2. ✅ Test with multiple users
3. ✅ Test email fact extraction
4. ✅ Deploy to production
5. ✅ Update frontend API_BASE_URL for production

---

**Happy Testing! 🚀**
