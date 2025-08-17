from typing import List

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker

from core.models import Base, StockSpotDB

SQLALCHEMY_DATABASE_URL = "sqlite:///./stock_data.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Get a database session for direct use (非依赖式)"""
    db = SessionLocal()
    return db


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
