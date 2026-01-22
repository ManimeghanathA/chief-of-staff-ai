from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.integrations.google_credentials import get_valid_google_credentials


def fetch_latest_emails(
    *,
    user_id,
    db: Session,
    max_results: int = 5
):
    """
    Fetch latest Gmail messages for a user.
    """

    creds = get_valid_google_credentials(
        user_id=user_id,
        db=db,
        required_scopes=[
            "https://www.googleapis.com/auth/gmail.readonly"
        ]
    )

    service = build("gmail", "v1", credentials=creds)

    results = service.users().messages().list(
        userId="me",
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From", "Subject"]
        ).execute()

        headers = msg_data["payload"]["headers"]
        email = {h["name"]: h["value"] for h in headers}
        emails.append(email)

    return emails
