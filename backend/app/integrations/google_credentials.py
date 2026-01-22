from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from sqlalchemy.orm import Session
from google.auth.exceptions import RefreshError
from fastapi import HTTPException


from app.db.models import GoogleCredential
from app.core.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET
)


def get_valid_google_credentials(
    user_id,
    db: Session,
    required_scopes: list[str]
) -> Credentials:
    """
    Returns a valid Google Credentials object.
    Automatically refreshes the access token if expired.
    """

    # 1. Load stored credentials from DB
    creds_row = (
        db.query(GoogleCredential)
        .filter(GoogleCredential.user_id == user_id)
        .first()
    )

    if not creds_row:
        raise Exception("Google credentials not found for user")

    # 2. Build Credentials object
    credentials = Credentials(
        token=creds_row.access_token,
        refresh_token=creds_row.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=required_scopes
    )

    # 3. Check expiry and refresh if needed
    if credentials.expired:
        try:
            credentials.refresh(Request())
        except RefreshError:
            raise HTTPException(
                status_code=401,
                detail="Google access expired. Please reconnect your Google account."
            )

        creds_row.access_token = credentials.token
        creds_row.expires_at = credentials.expiry
        creds_row.updated_at = datetime.utcnow()
        db.commit()


    return credentials
