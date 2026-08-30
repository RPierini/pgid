from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.appdb import AppBase
from app.db.identity import IdentityBase


class UserModel(IdentityBase):
    """Identidades e credenciais de usuários (SQLite)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    subject: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    roles: Mapped[str] = mapped_column(String, nullable=False)   # JSON array
    scopes: Mapped[str] = mapped_column(String, nullable=False)  # JSON array
    department: Mapped[str] = mapped_column(String, nullable=False)
    academic_unit: Mapped[str] = mapped_column(String, nullable=False)
    clearance: Mapped[int] = mapped_column(Integer, nullable=False)
    can_grade: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    storage_tier: Mapped[str] = mapped_column(String, nullable=False, default="basic")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class GradeRecord(AppBase):
    """Registros de notas lançadas (PostgreSQL)."""

    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    viewer_username: Mapped[str] = mapped_column(String, nullable=False)
    disciplina: Mapped[str] = mapped_column(String, nullable=False)
    nota: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CourseLockRecord(AppBase):
    """Registros de trancamento de cursos (PostgreSQL)."""

    __tablename__ = "course_locks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    approved_by: Mapped[str] = mapped_column(String, nullable=False)
    course: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
