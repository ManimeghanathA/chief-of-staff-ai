from sqlalchemy.orm import Session
from app.db.models import Memory


def load_user_memory(db: Session, user_id: int):
    memories = db.query(Memory).filter(Memory.user_id == user_id).all()
    return [{"key": m.key, "value": m.value} for m in memories]


def save_user_memory(db: Session, user_id: int, facts: list):
    for fact in facts:
        memory = Memory(
            user_id=user_id,
            key=fact["key"],
            value=fact["value"],
            source="chat"
        )
        db.add(memory)
    db.commit()
