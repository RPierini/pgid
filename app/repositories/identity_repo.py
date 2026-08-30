from __future__ import annotations

import json
from typing import Any

from sqlalchemy import delete, select

from app.db.identity import identity_session
from app.db.models import UserModel
from app.models import DemoUser


def _to_demo_user(row: UserModel) -> DemoUser:
    return DemoUser(
        username=row.username,
        subject=row.subject,
        name=row.name,
        label=row.label,
        roles=json.loads(row.roles),
        scopes=json.loads(row.scopes),
        department=row.department,
        academic_unit=row.academic_unit,
        clearance=row.clearance,
        can_grade=row.can_grade,
        storage_tier=row.storage_tier,
        active=row.active,
    )


async def list_users() -> list[DemoUser]:
    async with identity_session() as session:
        result = await session.execute(select(UserModel))
        return [_to_demo_user(row) for row in result.scalars()]


async def get_user_by_username(username: str) -> DemoUser | None:
    async with identity_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        row = result.scalar_one_or_none()
        return _to_demo_user(row) if row else None


async def get_user_by_subject(subject: str) -> DemoUser | None:
    async with identity_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.subject == subject)
        )
        row = result.scalar_one_or_none()
        return _to_demo_user(row) if row else None


async def create_user(data: dict[str, Any]) -> DemoUser:
    async with identity_session() as session:
        row = UserModel(
            username=data["username"],
            subject=data.get("subject", data["username"]),
            name=data["name"],
            label=data.get("label", data["name"]),
            roles=json.dumps(data.get("roles", [])),
            scopes=json.dumps(data.get("scopes", [])),
            department=data.get("department", ""),
            academic_unit=data.get("academic_unit", ""),
            clearance=int(data.get("clearance", 1)),
            can_grade=bool(data.get("can_grade", False)),
            storage_tier=data.get("storage_tier", "basic"),
            active=bool(data.get("active", True)),
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return _to_demo_user(row)


async def update_user(username: str, data: dict[str, Any]) -> DemoUser | None:
    async with identity_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        for field in ("name", "label", "department", "academic_unit", "storage_tier", "subject"):
            if field in data:
                setattr(row, field, data[field])
        if "roles" in data:
            row.roles = json.dumps(data["roles"])
        if "scopes" in data:
            row.scopes = json.dumps(data["scopes"])
        if "clearance" in data:
            row.clearance = int(data["clearance"])
        if "can_grade" in data:
            row.can_grade = bool(data["can_grade"])
        if "active" in data:
            row.active = bool(data["active"])
        await session.commit()
        await session.refresh(row)
        return _to_demo_user(row)


async def delete_user(username: str) -> bool:
    async with identity_session() as session:
        result = await session.execute(
            delete(UserModel).where(UserModel.username == username)
        )
        await session.commit()
        return result.rowcount > 0
