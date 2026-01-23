"""
Quick test script to verify memory functionality.
Run this after starting the backend to test the memory system.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test if backend is running"""
    print("🔍 Testing backend health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Backend is running!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Is it running on http://localhost:8000?")
        return False

def test_register(email, password):
    """Register a new user"""
    print(f"\n📝 Registering user: {email}...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            print("✅ Registration successful!")
            return data.get("access_token")
        else:
            print(f"❌ Registration failed: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_login(email, password):
    """Login user"""
    print(f"\n🔐 Logging in: {email}...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            return data.get("access_token")
        else:
            print(f"❌ Login failed: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_chat(token, message):
    """Send a chat message"""
    print(f"\n💬 Sending message: '{message}'...")
    try:
        response = requests.post(
            f"{BASE_URL}/chat/",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": message}
        )
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat successful!")
            print(f"   Response: {data.get('response', 'No response')[:200]}...")
            return data.get("response")
        else:
            print(f"❌ Chat failed: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("=" * 60)
    print("🧪 Chief of Staff AI - Memory System Test")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Backend is not running. Please start it first!")
        return
    
    # Test 2: Register/Login
    email = "test@example.com"
    password = "test123"
    
    token = test_register(email, password)
    if not token:
        # Try login instead
        token = test_login(email, password)
        if not token:
            print("\n❌ Cannot authenticate. Please check your credentials.")
            return
    
    # Test 3: Test memory storage
    print("\n" + "=" * 60)
    print("🧠 Testing Memory System")
    print("=" * 60)
    
    # Store a preference
    print("\n📌 Test 1: Storing a preference...")
    test_chat(token, "I hate 9 AM meetings")
    
    # Store another preference
    print("\n📌 Test 2: Storing another preference...")
    test_chat(token, "I prefer afternoon meetings")
    
    # Test memory retrieval
    print("\n📌 Test 3: Testing if agent remembers preferences...")
    test_chat(token, "What are my meeting preferences?")
    
    # Test with a question that should use memory
    print("\n📌 Test 4: Testing memory in context...")
    test_chat(token, "Do I have any 9 AM meetings today?")
    
    print("\n" + "=" * 60)
    print("✅ Memory test complete!")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("   1. Check the database to verify memories were stored")
    print("   2. Test the frontend at http://localhost:3000")
    print("   3. Try connecting Google OAuth for email/calendar features")

if __name__ == "__main__":
    main()
