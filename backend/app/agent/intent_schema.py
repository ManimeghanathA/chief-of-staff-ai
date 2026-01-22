from pydantic import BaseModel
from typing import Optional, Literal


class AgentIntent(BaseModel):
    intent: Literal[
        "gmail_today",
        "gmail_yesterday",
        "gmail_today_summary",
        "calendar_today",
        "calendar_tomorrow",
        "calendar_create",
        "unsupported",
        "need_more_info"
    ]

    # For calendar_create
    date: Optional[Literal["today", "tomorrow"]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    reason: Optional[str] = None
