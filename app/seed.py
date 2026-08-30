from __future__ import annotations

import json

from sqlalchemy import select

from app.db.identity import identity_session
from app.db.models import UserModel

_SEED_USERS = [
    {
        "username": "alice",
        "subject": "aluna-alice",
        "name": "Alice",
        "label": "Alice - Aluna",
        "roles": ["aluno"],
        "scopes": ["notas:read", "storage:download"],
        "department": "alunos",
        "academic_unit": "sistemas",
        "clearance": 1,
        "can_grade": False,
        "storage_tier": "basic",
        "active": True,
    },
    {
        "username": "bob",
        "subject": "professor-bob",
        "name": "Bob",
        "label": "Bob - Professor",
        "roles": ["professor"],
        "scopes": ["notas:read", "notas:write", "storage:download"],
        "department": "docencia",
        "academic_unit": "sistemas",
        "clearance": 3,
        "can_grade": True,
        "storage_tier": "staff",
        "active": True,
    },
    {
        "username": "carlos",
        "subject": "coordenador-carlos",
        "name": "Carlos",
        "label": "Carlos - Coordenador",
        "roles": ["coordenador"],
        "scopes": ["notas:read", "notas:write", "matriculas:manage", "storage:download"],
        "department": "academico",
        "academic_unit": "sistemas",
        "clearance": 5,
        "can_grade": True,
        "storage_tier": "admin",
        "active": True,
    },
]


async def seed_identity_db() -> None:
    """Insere os usuários de demonstração se ainda não existirem."""
    async with identity_session() as session:
        for data in _SEED_USERS:
            result = await session.execute(
                select(UserModel).where(UserModel.username == data["username"])
            )
            if result.scalar_one_or_none() is None:
                session.add(
                    UserModel(
                        username=data["username"],
                        subject=data["subject"],
                        name=data["name"],
                        label=data["label"],
                        roles=json.dumps(data["roles"]),
                        scopes=json.dumps(data["scopes"]),
                        department=data["department"],
                        academic_unit=data["academic_unit"],
                        clearance=data["clearance"],
                        can_grade=data["can_grade"],
                        storage_tier=data["storage_tier"],
                        active=data["active"],
                    )
                )
        await session.commit()
