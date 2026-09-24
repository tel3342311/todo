"""ORM 模型與 Pydantic schema。"""
from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    finish_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False
    )


# ---------- Pydantic schemas ----------
class TodoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    finish_date: date | None = Field(default=None, description="Optional target date (YYYY-MM-DD).")


class TodoUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=200)
    done: bool | None = None
    finish_date: date | None = Field(
        default=None, description="Target date; null clears it, omission preserves it."
    )


class TodoOut(BaseModel):
    id: int
    title: str
    done: bool
    created_at: datetime
    finish_date: date | None

    model_config = {"from_attributes": True}
