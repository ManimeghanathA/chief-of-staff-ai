from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import SessionLocal
from app.agent.graph import build_graph
from app.agent.schemas import AgentState

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    user_id: int
    message: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    graph = build_graph()

    state = AgentState(
        user_id=payload.user_id,
        message=payload.message
    )

    result = graph.invoke(
        state,
        config={"configurable": {"db": db}}
    )

    # ✅ SAFE handling
    if isinstance(result, dict):
        response_text = result.get("response", "")
    else:
        response_text = result.response

    return {"response": response_text}

