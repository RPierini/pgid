from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DemoUser(BaseModel):
    username: str
    subject: str
    name: str
    label: str
    roles: list[str]
    scopes: list[str]
    department: str
    academic_unit: str
    clearance: int
    can_grade: bool = False
    storage_tier: str = "basic"
    active: bool = True


class LoginRequest(BaseModel):
    username: str = Field(..., description="Usuário demonstrativo selecionado na UI")


class GradeSubmission(BaseModel):
    disciplina: str = "Arquitetura de Software"
    aluno: str = "alice"
    nota: float = 9.4


class CourseLockRequest(BaseModel):
    curso: str = "Engenharia de Software"
    motivo: str = "Ajuste de matriz curricular"


class FlowStep(BaseModel):
    node: str
    status: int
    detail: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict[str, Any]
    flow: list[FlowStep]


class ApiEnvelope(BaseModel):
    ok: bool
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    flow: list[FlowStep]
    actor: dict[str, Any] | None = None
    policy: dict[str, Any] | None = None

