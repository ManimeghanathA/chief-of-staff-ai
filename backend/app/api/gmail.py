from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.tools.gmail_tool import fetch_latest_emails

router = APIRouter(prefix="/gmail", tags=["gmail"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from app.auth.dependencies import get_current_user
from app.db.models import User

@router.get("/latest")
def get_latest_emails(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    emails = fetch_latest_emails(
        user_id=current_user.id,
        db=db
    )

    return {
        "count": len(emails),
        "emails": emails
    }
