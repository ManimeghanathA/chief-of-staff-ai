from fastapi import FastAPI
from app.core.config import APP_NAME

app = FastAPI(title=APP_NAME)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": APP_NAME}
