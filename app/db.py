"""資料庫連線設定：預設使用 SQLite，可用環境變數 DATABASE_URL 覆寫。"""
import os

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./todo.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def initialize_database() -> None:
    """Create tables and add the optional finish date to existing SQLite databases."""
    with engine.begin() as connection:
        if connection.dialect.name == "sqlite":
            # Serialize startup upgrades before inspecting or changing the schema.
            connection.exec_driver_sql("BEGIN IMMEDIATE")
        Base.metadata.create_all(bind=connection)
        columns = {column["name"] for column in inspect(connection).get_columns("todos")}
        if "finish_date" not in columns:
            if connection.dialect.name != "sqlite":
                raise RuntimeError("Migrate todos.finish_date to a nullable DATE before startup.")
            connection.exec_driver_sql("ALTER TABLE todos ADD COLUMN finish_date DATE")


def get_db():
    """FastAPI 依賴注入：每個請求一個 Session。"""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
