from __future__ import annotations

from typing import Any

from app.models import CourseLockRequest, DemoUser, GradeSubmission


def fetch_grades(user: DemoUser) -> dict[str, Any]:
    return {
        "viewer": user.label,
        "grades": [
            {"disciplina": "Arquitetura de Software", "nota": 9.4, "status": "aprovada"},
            {"disciplina": "Segurança de Aplicações", "nota": 8.9, "status": "aprovada"},
            {"disciplina": "Identidade Digital", "nota": 9.8, "status": "aprovada"},
        ],
        "summary": "RBAC permitiu leitura de notas; ABAC preservou o contexto acadêmico do usuário.",
    }


def submit_grade(user: DemoUser, submission: GradeSubmission) -> dict[str, Any]:
    return {
        "submitted_by": user.label,
        "record": submission.model_dump(),
        "summary": "RBAC autorizou escrita e ABAC confirmou o atributo can_grade.",
    }


def freeze_course(user: DemoUser, payload: CourseLockRequest) -> dict[str, Any]:
    return {
        "approved_by": user.label,
        "course": payload.curso,
        "reason": payload.motivo,
        "summary": "A ação administrativa foi autorizada por RBAC e pelo atributo de departamento.",
    }
