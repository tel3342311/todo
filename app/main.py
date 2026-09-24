"""Todo API — 課程實作專案的主程式。

端點：
  GET    /                前端頁（app/static/index.html，示範用）
  GET    /health          健康檢查（K8s liveness/readiness 用）
  GET    /todos           列出所有待辦
  POST   /todos           新增待辦
  GET    /todos/{id}      取得單筆
  PATCH  /todos/{id}      更新（title / done）
  DELETE /todos/{id}      刪除
  GET    /stats           統計（總數、完成數、完成率）
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import db as db_module
from .db import Base, get_db
from .models import Todo, TodoCreate, TodoOut, TodoUpdate

APP_VERSION = os.getenv("APP_VERSION", "0.1.0")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """啟動時建表（教學用；正式環境請改用 Alembic migration）。"""
    Base.metadata.create_all(bind=db_module.engine)
    yield


app = FastAPI(title="Todo API", version=APP_VERSION, lifespan=lifespan)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """提供待辦管理介面。"""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": APP_VERSION}


@app.get("/todos", response_model=list[TodoOut])
def list_todos(db: Session = Depends(get_db), done: bool | None = None) -> list[Todo]:
    """依 ID 列出待辦，可選擇以完成狀態篩選。"""
    query = select(Todo).order_by(Todo.id)
    if done is not None:
        query = query.where(Todo.done == done)
    return list(db.scalars(query).all())


@app.post("/todos", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoCreate, db: Session = Depends(get_db)) -> Todo:
    """建立並儲存待辦。"""
    todo = Todo(title=payload.title)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


def _get_or_404(db: Session, todo_id: int) -> Todo:
    todo = db.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="todo not found")
    return todo


@app.get("/todos/{todo_id}", response_model=TodoOut)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, todo_id)


@app.patch("/todos/{todo_id}", response_model=TodoOut)
def update_todo(todo_id: int, payload: TodoUpdate, db: Session = Depends(get_db)) -> Todo:
    """更新待辦標題或完成狀態。"""
    todo = _get_or_404(db, todo_id)
    if payload.title is not None:
        todo.title = payload.title
    if payload.done is not None:
        todo.done = payload.done
    db.commit()
    db.refresh(todo)
    return todo


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = _get_or_404(db, todo_id)
    db.delete(todo)
    db.commit()
    return None


@app.get("/stats")
def stats(db: Session = Depends(get_db)) -> dict:
    todos = db.scalars(select(Todo)).all()
    total = len(todos)
    done = sum(1 for t in todos if t.done)
    # NOTE(課程用): 這裡有一個刻意留下的 bug —— total 為 0 時會 ZeroDivisionError。
    # 單元 3「Codex 除錯」練習：請學員用 Codex 找出並修正，並補上測試。
    rate = round(done / total * 100, 1)
    return {"total": total, "done": done, "completion_rate": rate}
