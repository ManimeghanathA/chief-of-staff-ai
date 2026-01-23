# ⚡ Quick Test Guide

## 🚀 Servers Started!

I've started both servers for you:

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000

## 📋 Testing Steps

### 1. Open the Frontend
Open your browser and go to: **http://localhost:3000**

### 2. Register a New User
- Click **"Register"**
- Enter an email (e.g., `test@example.com`)
- Enter a password (e.g., `test123`)
- Click **"Login"** button

### 3. Test Memory System ⭐

#### Test 1: Store a Preference
Type in chat: **"I hate 9 AM meetings"**

Expected: Agent should acknowledge and remember this.

#### Test 2: Store Another Preference
Type: **"I prefer afternoon meetings"**

Expected: Agent should acknowledge.

#### Test 3: Verify Memory
Type: **"What are my meeting preferences?"**

Expected: Agent should mention both preferences.

#### Test 4: Test Memory in Context
Type: **"Do I have any 9 AM meetings today?"**

Expected: Agent should remember you don't like 9 AM meetings.

### 4. Test Email Integration (Optional - Requires Google OAuth)

1. Click **"🔗 Connect Google"**
2. Sign in with Google
3. Grant permissions
4. Try: **"What emails did I receive today?"**

### 5. Test Calendar Integration (Optional - Requires Google OAuth)

Try:
- **"What meetings do I have today?"**
- **"What meetings do I have tomorrow?"**

## 🧪 Alternative: Use Test Script

You can also run the automated test:

```bash
python test_memory.py
```

This will:
- Test backend health
- Register/login
- Test memory storage
- Test memory retrieval

## 🔍 Verify Memory in Database

To check if memories are stored:

```sql
-- Connect to your PostgreSQL database
SELECT * FROM memory;
```

You should see entries with:
- `key`: The preference/fact name
- `value`: The description
- `source`: "chat" or "email"

## 🐛 Troubleshooting

### Backend not running?
```bash
cd backend
python -m uvicorn app.main:app --reload
```

### Frontend not running?
```bash
cd frontend
python -m http.server 3000
```

### Database connection error?
- Check your `DATABASE_URL` in `backend/.env`
- Make sure PostgreSQL is running (if local)
- Or verify Railway.com database is accessible

### Chat not working?
- Check browser console (F12) for errors
- Verify backend is running on port 8000
- Check `API_BASE_URL` in `frontend/app.js`

## ✅ Success Indicators

You'll know it's working when:
- ✅ You can register/login
- ✅ Chat messages get responses
- ✅ Agent remembers your preferences
- ✅ Preferences persist after logout/login
- ✅ Agent uses memories in responses

## 🎯 Next Steps

1. Test all features
2. Connect Google OAuth
3. Test email/calendar integration
4. Verify memory extraction from emails
5. Deploy to production!

---

**Happy Testing! 🚀**
