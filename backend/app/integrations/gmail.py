from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.integrations.google_credentials import get_valid_google_credentials


def get_gmail_service(*, user_id, db: Session):
    creds = get_valid_google_credentials(
        user_id=user_id,
        db=db,
        required_scopes=[
            "https://www.googleapis.com/auth/gmail.readonly"
        ]
    )

    return build("gmail", "v1", credentials=creds)

from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.integrations.google_credentials import get_valid_google_credentials


def fetch_latest_emails(*, user_id, db: Session, max_results: int = 5):
    """
    Fetch latest Gmail messages for a user.
    Automatically refreshes Google access token if expired.
    """

    # 1. Get valid (auto-refreshed) Google credentials
    creds = get_valid_google_credentials(
        user_id=user_id,
        db=db,
        required_scopes=[
            "https://www.googleapis.com/auth/gmail.readonly"
        ]
    )

    # 2. Build Gmail service
    service = build("gmail", "v1", credentials=creds)

    # 3. Fetch message IDs
    results = service.users().messages().list(
        userId="me",
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    emails = []

    # 4. Fetch metadata for each message
    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From", "Subject"]
        ).execute()

        headers = {
            h["name"]: h["value"]
            for h in msg_data.get("payload", {}).get("headers", [])
        }

        emails.append({
            "from": headers.get("From"),
            "subject": headers.get("Subject"),
        })

    # 5. Return emails
    return emails
