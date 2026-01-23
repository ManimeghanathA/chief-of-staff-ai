from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
import os
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.database import SessionLocal
from app.db.models import User, GoogleCredential
from datetime import datetime
import requests
from app.auth.auth_utils import create_access_token



router = APIRouter(prefix="/auth/google", tags=["google-auth"])

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar", 
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]



@router.get("/login")
def google_login():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    return RedirectResponse(auth_url)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/callback")
def google_callback(request: Request, db: Session = Depends(get_db)):
    code = request.query_params.get("code")
    error = request.query_params.get("error")
    
    # Handle OAuth errors
    if error:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(f"{frontend_url}?error={error}")

    if not code:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(f"{frontend_url}?error=no_code")

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    try:
        # 1. Exchange code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials
        userinfo_response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"}
        )

        userinfo = userinfo_response.json()
        email = userinfo.get("email")
        user = db.query(User).filter(User.email == email).first()

        if not user:
            user = User(email=email)
            db.add(user)
            db.commit()
            db.refresh(user)
        expires_at = credentials.expiry

        google_creds = db.query(GoogleCredential).filter(
            GoogleCredential.user_id == user.id
        ).first()

        if not google_creds:
            google_creds = GoogleCredential(
                user_id=user.id,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                expires_at=expires_at,
                scopes=" ".join(credentials.scopes)
            )
            db.add(google_creds)
        else:
            google_creds.access_token = credentials.token
            google_creds.expires_at = expires_at

        db.commit()
        
        app_token = create_access_token({"user_id": str(user.id)})
        
        # Redirect to frontend with token
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(f"{frontend_url}?token={app_token}&success=true")
        
    except Exception as e:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(f"{frontend_url}?error=oauth_failed")


@router.get("/calendar-consent")
def google_calendar_consent():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,  # SAME callback
    )

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )

    return RedirectResponse(auth_url)
