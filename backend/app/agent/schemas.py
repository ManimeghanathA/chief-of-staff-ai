from typing import List, Dict, Optional
from pydantic import BaseModel


class AgentState(BaseModel):
    user_id: int
    message: str
    memory: List[Dict[str, str]] = []
    response: Optional[str] = None
