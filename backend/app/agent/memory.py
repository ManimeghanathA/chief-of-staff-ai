from sqlalchemy.orm import Session
from app.db.models import Memory
import uuid


def load_user_memory(db: Session, user_id: str):
    """Load user memories from database. user_id can be UUID string or UUID object."""
    user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    memories = db.query(Memory).filter(Memory.user_id == user_uuid).all()
    return [{"key": m.key, "value": m.value} for m in memories]


def save_user_memory(db: Session, user_id: str, facts: list, source: str = "chat"):
    """Save user memories to database. user_id can be UUID string or UUID object."""
    if not facts:
        return
    
    user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    
    for fact in facts:
        if not fact.get("key") or not fact.get("value"):
            continue
            
        memory = Memory(
            user_id=user_uuid,
            key=fact["key"],
            value=fact["value"],
            source=source
        )
        db.add(memory)
    db.commit()
