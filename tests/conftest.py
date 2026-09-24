"""測試共用 fixture：每個測試用獨立的記憶體 SQLite。"""
import os

# 必須在 import app 之前設定，讓 db.py 讀到測試用的 URL
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import db as db_module
from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    # 避免 startup 事件在真正的 engine 上建表
    db_module.engine = engine
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
