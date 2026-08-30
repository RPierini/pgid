# pgid

Aplicação web didática para demonstrar Gestão de Identidades (GId), OAuth 2.0 / OpenID Connect, JWT, RBAC/ABAC e a arquitetura PEP/PDP/PIP/PAP com FastAPI no backend e Alpine.js no frontend.

## Estrutura

```text
app/
├── main.py               # Ponto de entrada FastAPI + lifespan (init DBs)
├── auth_server.py        # IdP/PDP: emissão e verificação de JWT
├── gateway.py            # PEP: autorização RBAC/ABAC
├── backend_api.py        # Fachada async para o app_repo
├── admin.py              # Rotas de administração (CRUD identidades + dados)
├── seed.py               # Semente dos usuários de demonstração
├── storage_mock.py       # Object storage mock com pre-signed URL
├── models.py             # Modelos Pydantic
├── db/
│   ├── identity.py       # Engine SQLite (identidades/credenciais)
│   ├── appdb.py          # Engine PostgreSQL (dados da aplicação)
│   └── models.py         # Modelos ORM SQLAlchemy
├── repositories/
│   ├── identity_repo.py  # CRUD assíncrono de usuários (SQLite)
│   └── app_repo.py       # CRUD assíncrono de notas/trancamentos (PostgreSQL)
├── static/
│   └── app.js
└── templates/
    └── index.html
frontend/
├── Dockerfile            # Nginx servindo a SPA e fazendo proxy para o backend
└── nginx.conf
Dockerfile                # Backend FastAPI
docker-compose.yml
```

## Bancos de Dados

| Banco | Tecnologia | Responsabilidade |
|-------|-----------|-----------------|
| Identity DB | SQLite (`/data/identity.db`) | Credenciais e identidades dos usuários |
| App DB | PostgreSQL (`pgid`) | Dados da aplicação (notas, trancamentos) |

## Subindo com Docker Compose (recomendado)

```bash
docker compose up --build
```

Acesse `http://localhost` no navegador.

Serviços iniciados:
- **frontend** – porta 80 (Nginx, SPA Alpine.js)
- **backend** – porta 8000 (FastAPI, exposta internamente)
- **db** – PostgreSQL 16 (volume `pg_data`)

## Execução local (sem Docker)

Instale as dependências:

```bash
pip install -r requirements.txt
```

Configure as variáveis de ambiente (ou crie um `.env`):

```bash
export IDENTITY_DB_URL=sqlite+aiosqlite:///./identity.db
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=pgid
export POSTGRES_USER=pgid
export POSTGRES_PASSWORD=pgid
```

Suba a aplicação:

```bash
uvicorn app.main:app --reload
```

Acesse `http://127.0.0.1:8000`.

## Rotas

### Auth (IdP/PDP)
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/auth/login` | Login OAuth2/OIDC – emite JWT |
| GET | `/auth/jwks.json` | Chave pública RSA em formato JWKS |

### API (Gateway/PEP)
| Método | Rota | Política |
|--------|------|---------|
| GET | `/api/aluno/notas` | `view_grades` |
| POST | `/api/professor/lancar-notas` | `submit_grades` |
| DELETE | `/api/coordenador/trancar-curso` | `freeze_course` |
| GET | `/api/storage/presigned-url` | `presigned_url` |

### Storage Mock
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/storage/download?token=...` | Download via URL pré-assinada |

### Admin (CRUD)
| Método | Rota | Banco | Descrição |
|--------|------|-------|-----------|
| GET | `/admin/users` | SQLite | Listar identidades |
| POST | `/admin/users` | SQLite | Criar identidade |
| PUT | `/admin/users/{username}` | SQLite | Atualizar identidade |
| DELETE | `/admin/users/{username}` | SQLite | Remover identidade |
| GET | `/admin/grades` | PostgreSQL | Listar notas |
| DELETE | `/admin/grades/{id}` | PostgreSQL | Remover nota |
| GET | `/admin/course-locks` | PostgreSQL | Listar trancamentos |
| DELETE | `/admin/course-locks/{id}` | PostgreSQL | Remover trancamento |

## Fluxos demonstrados

- Login OAuth2/OIDC com emissão de JWT assinado por RSA
- JWKS em `/auth/jwks.json`
- Gateway/PEP validando assinatura, expiração, roles e scopes
- Regras RBAC e ABAC para leitura/escrita de notas e trancamento de curso
- Mock de Object Storage com pre-signed URL
- Laboratório de ataque para forjar claims do JWT
- Painel de administração para CRUD de identidades (SQLite) e dados da aplicação (PostgreSQL)
