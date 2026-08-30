from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.auth_server import router as auth_router
from app.gateway import router as gateway_router
from app.storage_mock import router as storage_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="PGId Demo",
    description="Demonstração didática de GId, OAuth2/OIDC, JWT, RBAC/ABAC e PEP/PDP/PIP/PAP.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(auth_router)
app.include_router(gateway_router)
app.include_router(storage_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")
