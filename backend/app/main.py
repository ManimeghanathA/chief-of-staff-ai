from fastapi import FastAPI
from app.core.config import APP_NAME
from app.db.database import engine
from app.db import models
from app.auth.routes import router as auth_router
from app.api.chat import router as chat_router



models.Base.metadata.create_all(bind=engine)

app = FastAPI(title=APP_NAME)

app.include_router(auth_router)

app.include_router(chat_router)
@app.get("/health")
def health_check():
    return {"status": "ok", "app": APP_NAME}
