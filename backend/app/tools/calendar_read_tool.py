from datetime import datetime, timedelta
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.integrations.google_credentials import get_valid_google_credentials
import socket


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

    # Reduce "hang forever" behavior on slow networks.
    # This affects underlying httplib2 socket connections used by googleapiclient.
    # Set a reasonable timeout (15 seconds should be enough for most cases)
    original_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(15)

    try:
        # cache_discovery=False avoids writing discovery cache files in some environments.
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)

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
    finally:
        # Restore original timeout setting
        socket.setdefaulttimeout(original_timeout)

    events = events_result.get("items", [])

    parsed_events = []
    for event in events:
        parsed_events.append({
            "summary": event.get("summary"),
            "start": event.get("start"),
            "end": event.get("end")
        })

    return parsed_events
