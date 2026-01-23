from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import SessionLocal
from app.agent.graph import build_graph
from app.agent.schemas import AgentState
from app.auth.dependencies import get_current_user
from app.db.models import User

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str  # ← ONLY MESSAGE


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        print(f"✅ Chat request from user: {current_user.email} (ID: {current_user.id})")
        graph = build_graph()

        state = AgentState(
            user_id=str(current_user.id),
            message=payload.message,
        )

        result = graph.invoke(
            state,
            config={"configurable": {"db": db}}
        )

        # ✅ SAFE handling for LangGraph return type
        if isinstance(result, dict):
            response_text = result.get("response", "")
        else:
            response_text = result.response

        return {"response": response_text}
    except Exception as e:
        print(f"❌ Chat error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise


@router.get("/test-auth")
def test_auth(current_user: User = Depends(get_current_user)):
    """Test endpoint to verify authentication is working"""
    return {
        "status": "authenticated",
        "user_id": str(current_user.id),
        "email": current_user.email
    }

