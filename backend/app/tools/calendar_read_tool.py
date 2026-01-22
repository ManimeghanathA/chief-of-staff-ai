from datetime import datetime, timedelta
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.integrations.google_credentials import get_valid_google_credentials


def fetch_upcoming_events(
    *,
    user_id,
    db: Session,
    max_results: int = 10
):
    """
    Fetch upcoming Google Calendar events for a user.
    """

    creds = get_valid_google_credentials(
        user_id=user_id,
        db=db,
        required_scopes=[
            "https://www.googleapis.com/auth/calendar.readonly"
        ]
    )

    service = build("calendar", "v3", credentials=creds)

    now = datetime.utcnow().isoformat() + "Z"
    one_week = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"

    events_result = service.events().list(
        calendarId="primary",
        timeMin=now,
        timeMax=one_week,
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])

    parsed_events = []
    for event in events:
        parsed_events.append({
            "summary": event.get("summary"),
            "start": event.get("start"),
            "end": event.get("end")
        })

    return parsed_events
