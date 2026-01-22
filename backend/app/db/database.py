import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use environment variable or default to psycopg (v3) driver
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:password@localhost:5432/chief_of_staff")

# Convert Railway/standard PostgreSQL URLs to psycopg v3 format
if DATABASE_URL:
    # Convert postgresql:// to postgresql+psycopg://
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")
    # Also handle psycopg2 if present
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+psycopg://")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
