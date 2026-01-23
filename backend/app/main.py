from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import APP_NAME
from app.db.database import engine
from app.db import models
from app.auth.routes import router as auth_router
from app.api.chat import router as chat_router
from app.auth.google_auth import router as google_auth_router
from app.api.gmail import router as gmail_router
from app.api.calendar import router as calendar_router

# Create tables on startup
models.Base.metadata.create_all(bind=engine)



app = FastAPI(title=APP_NAME)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

app.include_router(chat_router)

app.include_router(google_auth_router)

app.include_router(gmail_router)

app.include_router(calendar_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": APP_NAME}
