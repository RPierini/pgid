from __future__ import annotations

from typing import Any

import jwt
from fastapi import APIRouter, Header, Request, status
from fastapi.responses import JSONResponse

from app import backend_api, storage_mock
from app.auth_server import get_demo_user_by_subject, verify_access_token
from app.models import ApiEnvelope, CourseLockRequest, DemoUser, FlowStep, GradeSubmission

router = APIRouter(prefix="/api", tags=["gateway"])


def _allow_read_grades(user: DemoUser, claims: dict[str, Any]) -> tuple[bool, str]:
    same_unit = user.academic_unit == "sistemas"
    return same_unit, "ABAC confirmou vínculo com a unidade acadêmica sistemas."


def _allow_submit_grades(user: DemoUser, claims: dict[str, Any]) -> tuple[bool, str]:
    return user.can_grade, "ABAC verificou o atributo can_grade do docente."


def _allow_freeze_course(user: DemoUser, claims: dict[str, Any]) -> tuple[bool, str]:
    allowed = user.department == "academico" and user.clearance >= 5
    return allowed, "ABAC confirmou departamento acadêmico e clearance administrativo."


def _allow_storage(user: DemoUser, claims: dict[str, Any]) -> tuple[bool, str]:
    allowed = user.storage_tier in {"basic", "staff", "admin"}
    return allowed, "ABAC confirmou o tier de storage habilitado para download temporário."


POLICIES: dict[str, dict[str, Any]] = {
    "view_grades": {
        "required_roles": ["aluno", "professor", "coordenador"],
        "required_scopes": ["notas:read"],
        "abac_rule": _allow_read_grades,
        "description": "Leitura de notas para perfis acadêmicos autorizados.",
    },
    "submit_grades": {
        "required_roles": ["professor", "coordenador"],
        "required_scopes": ["notas:write"],
        "abac_rule": _allow_submit_grades,
        "description": "Lançamento de notas por perfis docentes ou coordenação.",
    },
    "freeze_course": {
        "required_roles": ["coordenador"],
        "required_scopes": ["matriculas:manage"],
        "abac_rule": _allow_freeze_course,
        "description": "Trancamento administrativo de curso pela coordenação.",
    },
    "presigned_url": {
        "required_roles": ["aluno", "professor", "coordenador"],
        "required_scopes": ["storage:download"],
        "abac_rule": _allow_storage,
        "description": "Emissão de URL temporária para storage mock.",
    },
}


def _flow_start() -> list[FlowStep]:
    return [
        FlowStep(node="Cliente / App", status=102, detail="Operação iniciada na SPA."),
        FlowStep(node="API Gateway (PEP)", status=102, detail="JWT recebido para inspeção."),
        FlowStep(node="IdP / PDP", status=102, detail="Assinatura e expiração em validação."),
        FlowStep(node="Identity DB / PIP", status=102, detail="Atributos do sujeito em consulta."),
        FlowStep(node="Policy Admin / PAP", status=102, detail="Política de acesso carregada."),
    ]


def _deny(message: str, flow: list[FlowStep], code: int, policy: dict[str, Any] | None = None) -> JSONResponse:
    flow[-1].status = code
    flow[-1].detail = message
    flow[1].status = code
    flow[1].detail = "PEP bloqueou a requisição."
    return JSONResponse(
        status_code=code,
        content=ApiEnvelope(
            ok=False,
            message=message,
            data={},
            flow=flow,
            actor=None,
            policy=_serialize_policy(policy),
        ).model_dump(),
    )


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1].strip()


def _serialize_policy(policy: dict[str, Any] | None) -> dict[str, Any] | None:
    if policy is None:
        return None
    return {
        "description": policy["description"],
        "required_roles": policy["required_roles"],
        "required_scopes": policy["required_scopes"],
    }


async def _authorize(
    authorization: str | None, policy_name: str
) -> tuple[DemoUser, dict[str, Any], dict[str, Any], list[FlowStep]] | JSONResponse:
    policy = POLICIES[policy_name]
    flow = _flow_start()
    token = _extract_bearer_token(authorization)
    if not token:
        return _deny("Token ausente ou malformado.", flow, status.HTTP_401_UNAUTHORIZED, policy)

    try:
        claims = verify_access_token(token)
    except jwt.ExpiredSignatureError:
        return _deny("JWT expirado.", flow, status.HTTP_401_UNAUTHORIZED, policy)
    except jwt.PyJWTError as exc:
        return _deny(f"JWT inválido: {exc}.", flow, status.HTTP_401_UNAUTHORIZED, policy)

    flow[2].status = 200
    flow[2].detail = "Assinatura RSA e claims padrão validadas pelo PDP."

    user = await get_demo_user_by_subject(claims["sub"])
    if user is None:
        return _deny("Sujeito do token não encontrado no PIP.", flow, status.HTTP_401_UNAUTHORIZED, policy)

    flow[3].status = 200
    flow[3].detail = "Atributos do sujeito carregados do Identity DB (SQLite)."

    token_roles = set(claims.get("roles", []))
    required_roles = set(policy["required_roles"])
    if not token_roles.intersection(required_roles):
        return _deny("RBAC negou acesso para as roles apresentadas no JWT.", flow, status.HTTP_403_FORBIDDEN, policy)

    token_scopes = set(str(claims.get("scope", "")).split())
    required_scopes = set(policy["required_scopes"])
    if not required_scopes.issubset(token_scopes):
        return _deny("Escopos insuficientes para a operação.", flow, status.HTTP_403_FORBIDDEN, policy)

    allowed, reason = policy["abac_rule"](user, claims)
    if not allowed:
        return _deny("ABAC negou acesso com base nos atributos do sujeito.", flow, status.HTTP_403_FORBIDDEN, policy)

    flow[4].status = 200
    flow[4].detail = reason
    return user, claims, policy, flow


def _success(
    message: str,
    user: DemoUser,
    policy: dict[str, Any],
    flow: list[FlowStep],
    data: dict[str, Any],
    backend_detail: str,
    include_storage: bool = False,
) -> ApiEnvelope:
    if include_storage:
        flow.append(FlowStep(node="Object Storage", status=200, detail="Objeto e metadata do storage mock preparados."))
    flow.extend(
        [
            FlowStep(node="Backend API", status=200, detail=backend_detail),
            FlowStep(node="Business DB", status=200, detail="Persistência consultada no PostgreSQL com sucesso."),
            FlowStep(node="Cliente / App", status=200, detail="Resposta consolidada devolvida à SPA."),
        ]
    )
    actor = {
        "username": user.username,
        "name": user.name,
        "label": user.label,
        "roles": user.roles,
    }
    return ApiEnvelope(
        ok=True,
        message=message,
        data=data,
        flow=flow,
        actor=actor,
        policy=_serialize_policy(policy),
    )


@router.get("/aluno/notas", response_model=ApiEnvelope)
async def aluno_notas(authorization: str | None = Header(default=None)) -> ApiEnvelope | JSONResponse:
    decision = await _authorize(authorization, "view_grades")
    if isinstance(decision, JSONResponse):
        return decision
    user, claims, policy, flow = decision
    data = await backend_api.fetch_grades(user)
    return _success(
        "Notas recuperadas com sucesso.",
        user,
        policy,
        flow,
        data,
        backend_detail="Backend aplicou a regra de leitura de notas.",
    )


@router.post("/professor/lancar-notas", response_model=ApiEnvelope)
async def lancar_notas(
    payload: GradeSubmission,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope | JSONResponse:
    decision = await _authorize(authorization, "submit_grades")
    if isinstance(decision, JSONResponse):
        return decision
    user, claims, policy, flow = decision
    data = await backend_api.submit_grade(user, payload)
    return _success(
        "Nota lançada com sucesso.",
        user,
        policy,
        flow,
        data,
        backend_detail="Backend registrou o lançamento de nota no PostgreSQL.",
    )


@router.delete("/coordenador/trancar-curso", response_model=ApiEnvelope)
async def trancar_curso(
    payload: CourseLockRequest,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope | JSONResponse:
    decision = await _authorize(authorization, "freeze_course")
    if isinstance(decision, JSONResponse):
        return decision
    user, claims, policy, flow = decision
    data = await backend_api.freeze_course(user, payload)
    return _success(
        "Curso trancado com sucesso.",
        user,
        policy,
        flow,
        data,
        backend_detail="Backend executou a operação administrativa de trancamento no PostgreSQL.",
    )


@router.get("/storage/presigned-url", response_model=ApiEnvelope)
async def presigned_url(
    request: Request,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope | JSONResponse:
    decision = await _authorize(authorization, "presigned_url")
    if isinstance(decision, JSONResponse):
        return decision
    user, claims, policy, flow = decision
    data = storage_mock.build_presigned_download_url(request, user, "guias/gid-intro.txt")
    return _success(
        "URL temporária emitida com sucesso.",
        user,
        policy,
        flow,
        data,
        backend_detail="Gateway obteve uma URL pré-assinada para o recurso solicitado.",
        include_storage=True,
    )
