# pgid

Aplicação web didática para demonstrar Gestão de Identidades (GId), OAuth 2.0 / OpenID Connect, JWT, RBAC/ABAC e a arquitetura PEP/PDP/PIP/PAP com FastAPI no backend e Alpine.js no frontend.

## Estrutura

```text
app/
├── main.py
├── auth_server.py
├── gateway.py
├── backend_api.py
├── storage_mock.py
├── models.py
├── static/
│   └── app.js
└── templates/
    └── index.html
```

## Requisitos

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Execução

Suba a aplicação com:

```bash
uvicorn app.main:app --reload
```

Depois, abra `http://127.0.0.1:8000`.

## Fluxos demonstrados

- Login OAuth2/OIDC com emissão de JWT assinado por RSA
- JWKS em `/auth/jwks.json`
- Gateway/PEP validando assinatura, expiração, roles e scopes
- Regras RBAC e ABAC para:
  - `GET /api/aluno/notas`
  - `POST /api/professor/lancar-notas`
  - `DELETE /api/coordenador/trancar-curso`
  - `GET /api/storage/presigned-url`
- Mock de Object Storage com pre-signed URL em `/storage/download`
- Laboratório de ataque para forjar claims do JWT e observar a falha do PEP
