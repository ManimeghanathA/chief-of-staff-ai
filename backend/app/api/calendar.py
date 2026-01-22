from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.tools.calendar_read_tool import fetch_upcoming_events

router = APIRouter(prefix="/calendar", tags=["calendar"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from app.auth.dependencies import get_current_user
from app.db.models import User
@router.get("/events")
def get_calendar_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        events = fetch_upcoming_events(
            user_id=current_user.id,
            db=db
        )
    except Exception as e:
        # This typically means calendar scope not granted
        raise HTTPException(
            status_code=403,
            detail="Calendar not connected. Please connect your calendar."
        )

    return {
        "count": len(events),
        "events": events
    }

from pydantic import BaseModel
from datetime import datetime
from app.auth.dependencies import get_current_user
from app.db.models import User
from app.tools.calendar_write_tool import create_calendar_event


class CreateEventRequest(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime


@router.post("/create-event")
def create_event(
    payload: CreateEventRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = create_calendar_event(
        user_id=current_user.id,
        db=db,
        title=payload.title,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )

    return {
        "message": "Event created successfully",
        "event": event
    }

