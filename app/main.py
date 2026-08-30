from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.admin import router as admin_router
from app.auth_server import router as auth_router
from app.db.appdb import AppBase, app_engine
from app.db.identity import IdentityBase, identity_engine
from app.db.models import CourseLockRecord, GradeRecord, UserModel  # noqa: F401 – trigger metadata
from app.gateway import router as gateway_router
from app.seed import seed_identity_db
from app.storage_mock import router as storage_router

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with identity_engine.begin() as conn:
        await conn.run_sync(IdentityBase.metadata.create_all)
    async with app_engine.begin() as conn:
        await conn.run_sync(AppBase.metadata.create_all)
    await seed_identity_db()
    yield


app = FastAPI(
    title="PGId Demo",
    description="Demonstração didática de GId, OAuth2/OIDC, JWT, RBAC/ABAC e PEP/PDP/PIP/PAP.",
    version="2.0.0",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(auth_router)
app.include_router(gateway_router)
app.include_router(storage_router)
app.include_router(admin_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")
