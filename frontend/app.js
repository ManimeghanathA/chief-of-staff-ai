// Configuration - Update this with your backend URL
const API_BASE_URL = window.location.origin.includes('localhost') 
    ? 'http://localhost:8000' 
    : 'YOUR_BACKEND_URL_HERE'; // Replace with your deployed backend URL

// Handle Google OAuth callback FIRST (before DOMContentLoaded)
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get('token');
const error = urlParams.get('error');

let authToken = localStorage.getItem('authToken');
let currentUser = null;

// If token is in URL, use it (this happens after Google OAuth redirect)
if (token) {
    authToken = token;
    localStorage.setItem('authToken', token);
    // Clean URL immediately
    window.history.replaceState({}, document.title, window.location.pathname);
} else if (error) {
    // Handle OAuth errors
    console.error('OAuth error:', error);
    // Clean URL
    window.history.replaceState({}, document.title, window.location.pathname);
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    // Show success notification if we just logged in via Google
    if (token) {
        setTimeout(() => {
            showNotification('Google login successful!', 'success');
        }, 100);
    } else if (error) {
        setTimeout(() => {
            showNotification('Google login failed: ' + error, 'error');
        }, 100);
    }
    
    checkAuth();
    setupEventListeners();
});

function checkAuth() {
    // Refresh token from localStorage
    authToken = localStorage.getItem('authToken');
    
    if (authToken) {
        console.log('Token found, showing main content');
        showMainContent();
    } else {
        console.log('No token found, showing auth section');
        showAuthSection();
    }
}

function setupEventListeners() {
    // Auth buttons
    document.getElementById('loginBtn').addEventListener('click', () => showAuthModal('Login'));
    document.getElementById('registerBtn').addEventListener('click', () => showAuthModal('Register'));
    document.getElementById('googleAuthBtn').addEventListener('click', handleGoogleAuth);
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    
    // Modal
    document.querySelector('.close').addEventListener('click', closeAuthModal);
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('authModal');
        if (e.target === modal) {
            closeAuthModal();
        }
    });
    
    // Chat
    document.getElementById('sendBtn').addEventListener('click', sendMessage);
    document.getElementById('messageInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Auth form
    document.getElementById('authForm').addEventListener('submit', handleAuthSubmit);
}

function showAuthModal(type) {
    const modal = document.getElementById('authModal');
    const title = document.getElementById('modalTitle');
    const submitBtn = document.getElementById('submitBtn');
    
    title.textContent = type;
    submitBtn.textContent = type;
    modal.style.display = 'block';
}

function closeAuthModal() {
    document.getElementById('authModal').style.display = 'none';
    document.getElementById('authForm').reset();
}

function showAuthSection() {
    document.getElementById('authSection').style.display = 'flex';
    document.getElementById('userSection').style.display = 'none';
    document.getElementById('mainContent').style.display = 'none';
}

function showMainContent() {
    document.getElementById('authSection').style.display = 'none';
    document.getElementById('userSection').style.display = 'flex';
    document.getElementById('mainContent').style.display = 'block';
}

async function handleAuthSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('emailInput').value;
    const password = document.getElementById('passwordInput').value;
    const isLogin = document.getElementById('modalTitle').textContent === 'Login';
    
    const endpoint = isLogin ? '/auth/login' : '/auth/register';
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.access_token;
            localStorage.setItem('authToken', authToken);
            closeAuthModal();
            showMainContent();
            showNotification(isLogin ? 'Logged in successfully!' : 'Registered successfully!', 'success');
        } else {
            showNotification(data.detail || 'Authentication failed', 'error');
        }
    } catch (error) {
        showNotification('Network error. Please check your connection.', 'error');
        console.error('Auth error:', error);
    }
}

function handleGoogleAuth() {
    // Store current origin so we can redirect back correctly
    const currentOrigin = window.location.origin;
    console.log('Initiating Google OAuth from:', currentOrigin);
    
    // Redirect to Google OAuth endpoint
    // The backend will redirect back to FRONTEND_URL, so make sure it matches
    window.location.href = `${API_BASE_URL}/auth/google/login`;
}

async function handleLogout() {
    authToken = null;
    localStorage.removeItem('authToken');
    currentUser = null;
    showAuthSection();
    clearChat();
    showNotification('Logged out successfully', 'success');
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    // Refresh token from localStorage in case it was updated
    authToken = localStorage.getItem('authToken');
    
    if (!message) {
        return;
    }
    
    if (!authToken) {
        addMessageToChat('Please log in first to use the chat.', 'assistant');
        showAuthSection();
        return;
    }
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    input.value = '';
    
    // Show loading
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`,
            },
            body: JSON.stringify({ message }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addMessageToChat(data.response, 'assistant');
        } else if (response.status === 401) {
            // Token expired or invalid - clear it and show auth
            const errorData = await response.json().catch(() => ({}));
            const errorMsg = errorData.detail || 'Session expired';
            
            authToken = null;
            localStorage.removeItem('authToken');
            
            if (errorMsg.includes('expired')) {
                addMessageToChat('Your session has expired. Please log in again to continue.', 'assistant');
                showNotification('Session expired. Please log in again.', 'error');
            } else {
                addMessageToChat('Authentication failed. Please log in again.', 'assistant');
                showNotification('Please log in again.', 'error');
            }
            showAuthSection();
        } else {
            addMessageToChat('Sorry, I encountered an error. Please try again.', 'assistant');
            console.error('Chat error:', data);
        }
    } catch (error) {
        addMessageToChat('Network error. Please check your connection.', 'assistant');
        console.error('Chat error:', error);
    } finally {
        hideLoading();
    }
}

function sendQuickMessage(message) {
    document.getElementById('messageInput').value = message;
    sendMessage();
}

function addMessageToChat(message, role) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = message;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function clearChat() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = `
        <div class="message assistant">
            <div class="message-content">
                👋 Hello! I'm your Chief of Staff AI assistant. I can help you manage your calendar, emails, and remember your preferences. How can I help you today?
            </div>
        </div>
    `;
}

function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showNotification(message, type) {
    // Simple notification - you can enhance this
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#4CAF50' : '#f44336'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 3000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Token handling moved to top of file (before DOMContentLoaded)
