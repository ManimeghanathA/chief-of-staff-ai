from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from datetime import datetime

from app.integrations.google_credentials import get_valid_google_credentials


def create_calendar_event(
    *,
    user_id,
    db: Session,
    title: str,
    start_time: datetime,
    end_time: datetime,
):
    """
    Create a Google Calendar event for the user.
    """

    creds = get_valid_google_credentials(
        user_id=user_id,
        db=db,
        required_scopes=[
            "https://www.googleapis.com/auth/calendar"
        ]
    )

    service = build("calendar", "v3", credentials=creds)

    event = {
        "summary": title,
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "UTC",
        },
    }

    created_event = service.events().insert(
        calendarId="primary",
        body=event
    ).execute()

    return {
        "id": created_event.get("id"),
        "summary": created_event.get("summary"),
        "htmlLink": created_event.get("htmlLink"),
    }
