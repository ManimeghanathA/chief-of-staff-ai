from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import User
from app.auth.auth_utils import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("user_id")

        if user_id is None:
            print(f"❌ Token missing user_id in payload: {payload}")
            raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError as e:
        error_msg = str(e).lower()
        if "expired" in error_msg or "exp" in error_msg:
            print(f"❌ Token expired: {e}")
            raise HTTPException(
                status_code=401, 
                detail="Token expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        print(f"❌ JWT decode error: {e}")
        print(f"❌ Token (first 20 chars): {token[:20] if token else 'None'}...")
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        print(f"❌ User not found for user_id: {user_id}")
        raise HTTPException(status_code=401, detail="User not found")

    return user
