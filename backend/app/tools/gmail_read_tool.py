from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.integrations.google_credentials import get_valid_google_credentials


def fetch_gmail_messages_for_date(
    *,
    user_id: str,
    db: Session,
    days_ago: int = 0,
    max_results: int = 10
):
    """
    Fetch Gmail messages for a specific day.
    days_ago = 0 → today
    days_ago = 1 → yesterday
    """

    creds = get_valid_google_credentials(
        user_id=user_id,
        db=db,
        required_scopes=[
            "https://www.googleapis.com/auth/gmail.readonly"
        ]
    )

    service = build("gmail", "v1", credentials=creds)

    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days_ago)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end = start + timedelta(days=1)

    query = (
        f"after:{int(start.timestamp())} "
        f"before:{int(end.timestamp())}"
    )

    results = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        data = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From", "Subject"]
        ).execute()

        headers = {
            h["name"]: h["value"]
            for h in data["payload"]["headers"]
        }

        emails.append({
            "from": headers.get("From"),
            "subject": headers.get("Subject"),
        })

    return emails
