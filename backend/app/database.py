"""
数据库连接与会话管理。

使用 SQLAlchemy 2.x 同步 API，SQLite 作为默认数据库。
提供 engine、SessionLocal 和 Base，以及 get_db 依赖函数。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# SQLite 连接需要 check_same_thread=False
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI 依赖：获取数据库会话，自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
