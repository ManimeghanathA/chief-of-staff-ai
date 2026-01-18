from fastapi import FastAPI
from app.core.config import APP_NAME
from app.db.database import engine
from app.db import models

# CREATE TABLES
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title=APP_NAME)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": APP_NAME}
