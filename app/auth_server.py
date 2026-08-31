from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import APIRouter, HTTPException, status

from app.models import DemoUser, FlowStep, LoginRequest, TokenResponse
from app.repositories import identity_repo

ISSUER = "pgid-demo"
ACCESS_TOKEN_LIFETIME_SECONDS = 3600
JWT_ALGORITHM = "RS256"
JWT_KEY_ID = "pgid-demo-rsa-1"

router = APIRouter(tags=["auth"])

_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PRIVATE_KEY_PEM = _private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)
PUBLIC_KEY_PEM = _private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)


def _b64url_uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, byteorder="big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _public_profile(user: DemoUser) -> dict[str, Any]:
    return {
        "username": user.username,
        "sub": user.subject,
        "name": user.name,
        "label": user.label,
        "roles": user.roles,
        "scopes": user.scopes,
        "attributes": {
            "department": user.department,
            "academic_unit": user.academic_unit,
            "clearance": user.clearance,
            "can_grade": user.can_grade,
            "storage_tier": user.storage_tier,
        },
    }


async def get_demo_user(username: str) -> DemoUser | None:
    return await identity_repo.get_user_by_username(username)


async def get_demo_user_by_subject(subject: str) -> DemoUser | None:
    return await identity_repo.get_user_by_subject(subject)


def issue_access_token(user: DemoUser) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user.subject,
        "name": user.name,
        "roles": user.roles,
        "scope": " ".join(user.scopes),
        "iss": ISSUER,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ACCESS_TOKEN_LIFETIME_SECONDS)).timestamp()),
    }
    return jwt.encode(
        payload,
        PRIVATE_KEY_PEM,
        algorithm=JWT_ALGORITHM,
        headers={"kid": JWT_KEY_ID},
    )


def verify_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        PUBLIC_KEY_PEM,
        algorithms=[JWT_ALGORITHM],
        issuer=ISSUER,
        options={"require": ["sub", "name", "roles", "scope", "iss", "iat", "exp"]},
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    user = await get_demo_user(payload.username)
    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário de demonstração inválido.",
        )

    token = issue_access_token(user)
    flow = [
        FlowStep(node="Cliente / App", status=200, detail="Login OAuth2/OIDC iniciado na SPA."),
        FlowStep(node="API Gateway (PEP)", status=200, detail="Requisição de login passou pelo gateway (pass-through, sem token ainda)."),
        FlowStep(node="IdP / PDP", status=200, detail="Usuário autenticado e token emitido."),
        FlowStep(node="Identity DB / PIP", status=200, detail="Identidade demonstrativa consultada."),
        FlowStep(node="Cliente / App", status=200, detail="JWT entregue ao frontend."),
    ]
    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_LIFETIME_SECONDS,
        user=_public_profile(user),
        flow=flow,
    )


@router.get("/auth/jwks.json")
async def jwks() -> dict[str, list[dict[str, str]]]:
    public_numbers = _private_key.public_key().public_numbers()
    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "kid": JWT_KEY_ID,
                "alg": JWT_ALGORITHM,
                "n": _b64url_uint(public_numbers.n),
                "e": _b64url_uint(public_numbers.e),
            }
        ]
    }
