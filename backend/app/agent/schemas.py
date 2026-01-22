from typing import List, Dict, Optional, Literal
from pydantic import BaseModel
from datetime import datetime

class AgentState(BaseModel):
    user_id: str
    message: str

    # memory
    memory: List[Dict[str, str]] = []

    # intent
    intent: Optional[
        Literal[
            "gmail_today",
            "gmail_yesterday",
            "gmail_today_summary",
            "calendar_today",
            "calendar_tomorrow",
            "calendar_create",
            "need_more_info",
            "unsupported",
        ]
    ] = None

    # calendar fields
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # final response
    response: Optional[str] = None
