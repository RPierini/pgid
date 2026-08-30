from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import jwt
from fastapi import APIRouter, HTTPException, Query, Request, status

from app.models import DemoUser, FlowStep

router = APIRouter(tags=["storage"])

STORAGE_TOKEN_LIFETIME_SECONDS = 180
STORAGE_ALGORITHM = "HS256"
STORAGE_SECRET = "pgid-demo-storage-secret"

OBJECTS: dict[str, dict[str, Any]] = {
    "guias/gid-intro.txt": {
        "file_name": "gid-intro.txt",
        "content_type": "text/plain",
        "content": "Guia introdutório de Gestão de Identidades, OAuth2/OIDC, JWT e políticas PEP/PDP/PIP/PAP.",
    }
}


def build_presigned_download_url(request: Request, user: DemoUser, object_key: str) -> dict[str, Any]:
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=STORAGE_TOKEN_LIFETIME_SECONDS)
    token = jwt.encode(
        {
            "sub": user.subject,
            "scope": "storage:download",
            "object_key": object_key,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        },
        STORAGE_SECRET,
        algorithm=STORAGE_ALGORITHM,
    )
    base_url = str(request.base_url).rstrip("/")
    query = urlencode({"token": token})
    return {
        "download_url": f"{base_url}/storage/download?{query}",
        "object_key": object_key,
        "expires_at": expires_at.isoformat(),
        "scope": "storage:download",
    }


def verify_presigned_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        STORAGE_SECRET,
        algorithms=[STORAGE_ALGORITHM],
        options={"require": ["sub", "scope", "object_key", "iat", "exp"]},
    )


@router.get("/storage/download")
async def download(token: str = Query(...)) -> dict[str, Any]:
    try:
        claims = verify_presigned_token(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "ok": False,
                "message": "Pre-signed URL inválida ou expirada.",
                "flow": [
                    FlowStep(node="Cliente / App", status=401, detail="Download disparado pelo navegador.").model_dump(),
                    FlowStep(node="Object Storage", status=401, detail=f"Token HMAC rejeitado: {exc}.").model_dump(),
                ],
            },
        ) from exc

    object_key = claims["object_key"]
    record = OBJECTS.get(object_key)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objeto não encontrado.")

    return {
        "ok": True,
        "message": "Arquivo recuperado do storage mock com URL temporária.",
        "data": {"object_key": object_key, **record},
        "flow": [
            FlowStep(node="Cliente / App", status=200, detail="URL temporária utilizada pelo frontend.").model_dump(),
            FlowStep(node="Object Storage", status=200, detail="Assinatura HMAC e escopo de download validados.").model_dump(),
            FlowStep(node="Cliente / App", status=200, detail="Conteúdo entregue ao cliente.").model_dump(),
        ],
    }
