from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.repositories import app_repo, identity_repo

router = APIRouter(prefix="/admin", tags=["admin"])


# ─── Identidades / Usuários (Identity DB – SQLite) ──────────────────────────


@router.get("/users")
async def list_users() -> list[dict[str, Any]]:
    users = await identity_repo.list_users()
    return [u.model_dump() for u in users]


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(body: dict[str, Any]) -> dict[str, Any]:
    existing = await identity_repo.get_user_by_username(body.get("username", ""))
    if existing:
        raise HTTPException(status_code=409, detail="Usuário já existe.")
    user = await identity_repo.create_user(body)
    return user.model_dump()


@router.put("/users/{username}")
async def update_user(username: str, body: dict[str, Any]) -> dict[str, Any]:
    user = await identity_repo.update_user(username, body)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user.model_dump()


@router.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(username: str) -> None:
    deleted = await identity_repo.delete_user(username)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")


# ─── Dados de Aplicação (App DB – PostgreSQL) ────────────────────────────────


@router.get("/grades")
async def list_grades() -> list[dict[str, Any]]:
    return await app_repo.list_grades()


@router.delete("/grades/{grade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grade(grade_id: int) -> None:
    deleted = await app_repo.delete_grade(grade_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Nota não encontrada.")


@router.get("/course-locks")
async def list_course_locks() -> list[dict[str, Any]]:
    return await app_repo.list_course_locks()


@router.delete("/course-locks/{lock_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course_lock(lock_id: int) -> None:
    deleted = await app_repo.delete_course_lock(lock_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Registro não encontrado.")
