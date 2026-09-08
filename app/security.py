from __future__ import annotations

from typing import Optional

import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth_server import verify_access_token

# Esquema de segurança declarado para o Swagger UI (/docs). Com ele, o botão
# "Authorize" injeta automaticamente `Authorization: Bearer <token>` em todos
# os endpoints que usam `Security(bearer_scheme)`. Quem chama via cliente
# (frontend, curl) continua podendo enviar o header manualmente — funciona igual.
bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Cole o access_token retornado em POST /auth/login. Formato: Bearer <token>",
)


def optional_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> Optional[str]:
    """Retorna a string do token (sem o prefixo 'Bearer') ou None se ausente."""
    return credentials.credentials if credentials else None


def require_valid_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Valida o JWT e retorna as claims. Levanta 401 se ausente/inválido/expirado."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ausente ou malformado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return verify_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"JWT inválido: {exc}.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
