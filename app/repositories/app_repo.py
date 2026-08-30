from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select

from app.db.appdb import app_session
from app.db.models import CourseLockRecord, GradeRecord
from app.models import CourseLockRequest, DemoUser, GradeSubmission

_DEFAULT_GRADES = [
    {"id": None, "disciplina": "Arquitetura de Software", "nota": 9.4, "status": "aprovada", "viewer_username": "seed"},
    {"id": None, "disciplina": "Segurança de Aplicações", "nota": 8.9, "status": "aprovada", "viewer_username": "seed"},
    {"id": None, "disciplina": "Identidade Digital", "nota": 9.8, "status": "aprovada", "viewer_username": "seed"},
]


async def fetch_grades(user: DemoUser) -> dict[str, Any]:
    async with app_session() as session:
        result = await session.execute(select(GradeRecord).order_by(GradeRecord.id))
        rows = result.scalars().all()
        grades = (
            [{"id": r.id, "disciplina": r.disciplina, "nota": r.nota, "status": r.status, "viewer_username": r.viewer_username} for r in rows]
            if rows
            else _DEFAULT_GRADES
        )
        return {
            "viewer": user.label,
            "grades": grades,
            "summary": "RBAC permitiu leitura de notas; ABAC preservou o contexto acadêmico do usuário.",
        }


async def submit_grade(user: DemoUser, submission: GradeSubmission) -> dict[str, Any]:
    async with app_session() as session:
        row = GradeRecord(
            viewer_username=user.username,
            disciplina=submission.disciplina,
            nota=submission.nota,
            status="lançada",
            created_at=datetime.now(UTC),
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return {
            "id": row.id,
            "submitted_by": user.label,
            "record": submission.model_dump(),
            "summary": "RBAC autorizou escrita e ABAC confirmou o atributo can_grade.",
        }


async def delete_grade(grade_id: int) -> bool:
    async with app_session() as session:
        result = await session.execute(
            delete(GradeRecord).where(GradeRecord.id == grade_id)
        )
        await session.commit()
        return result.rowcount > 0


async def list_grades() -> list[dict[str, Any]]:
    async with app_session() as session:
        result = await session.execute(select(GradeRecord).order_by(GradeRecord.id))
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "viewer_username": r.viewer_username,
                "disciplina": r.disciplina,
                "nota": r.nota,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]


async def freeze_course(user: DemoUser, payload: CourseLockRequest) -> dict[str, Any]:
    async with app_session() as session:
        row = CourseLockRecord(
            approved_by=user.username,
            course=payload.curso,
            reason=payload.motivo,
            created_at=datetime.now(UTC),
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return {
            "id": row.id,
            "approved_by": user.label,
            "course": payload.curso,
            "reason": payload.motivo,
            "summary": "A ação administrativa foi autorizada por RBAC e pelo atributo de departamento.",
        }


async def list_course_locks() -> list[dict[str, Any]]:
    async with app_session() as session:
        result = await session.execute(select(CourseLockRecord).order_by(CourseLockRecord.id))
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "approved_by": r.approved_by,
                "course": r.course,
                "reason": r.reason,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]


async def delete_course_lock(lock_id: int) -> bool:
    async with app_session() as session:
        result = await session.execute(
            delete(CourseLockRecord).where(CourseLockRecord.id == lock_id)
        )
        await session.commit()
        return result.rowcount > 0
