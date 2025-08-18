from typing import List
import os

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker

from core.models import Base, StockSpotDB, StockHistoryDB


def get_project_root():
    """Get the project root directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))


DB_DIR = os.path.join(get_project_root(), "data")
os.makedirs(DB_DIR, exist_ok=True)  # 确保主数据库目录存在
SQLITE_MAIN_DB = os.path.join(DB_DIR, "stock_data.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{SQLITE_MAIN_DB}"

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


def get_hist_db_session(symbol: str):
    """
    Get a database session for historical data for a specific symbol/aust.
    Automatically creates the database file and tables if not exist.
    """
    hist_db_dir = os.path.join(get_project_root(), "data", "hist_db")
    os.makedirs(hist_db_dir, exist_ok=True)  # 确保历史数据库目录存在
    db_path = os.path.join(hist_db_dir, f"stock_hist_{symbol}.db")
    hist_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    HistSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=hist_engine)
    Base.metadata.create_all(bind=hist_engine)
    db = HistSessionLocal()
    return db
