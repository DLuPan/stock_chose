from typing import List
import os
from dotenv import load_dotenv

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker

from core.models import Base, StockSpotDB, StockHistoryDB


def get_project_root():
    """Get the project root directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))


# Load environment variables from .env file
load_dotenv(os.path.join(get_project_root(), ".env"))


# MySQL 数据库配置 - 请根据您的实际配置修改这些参数
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "stock_data")

SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600,
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
    Get a database session for historical data for a specific symbol.
    For MySQL, we'll use the same database but different table naming or schema.
    """
    # 对于MySQL，我们可以使用同一个数据库，但可能需要不同的表命名策略
    # 这里返回相同的会话，实际使用时可能需要调整表名或使用分区
    return get_db_session()
