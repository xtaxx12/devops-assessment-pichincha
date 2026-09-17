# DevOps Assessment — Microservicio `/DevOps`

[![CI/CD](https://github.com/OWNER/devops-assessment/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/OWNER/devops-assessment/actions/workflows/ci-cd.yml)

Microservicio REST construido con **Python 3.12 + FastAPI**, desarrollado con **TDD** y
**Clean Code**, contenerizado con Docker, desplegado en Kubernetes con 2+ réplicas detrás de un
balanceador de carga y con pipeline CI/CD completo en GitHub Actions.


## Tabla de contenidos

1. [Contrato del endpoint](#contrato-del-endpoint)
2. [Arquitectura y decisiones de diseño](#arquitectura-y-decisiones-de-diseño)
3. [Estructura del repositorio](#estructura-del-repositorio)
4. [Ejecución local](#ejecución-local)
5. [Tests y cobertura](#tests-y-cobertura)
6. [Docker](#docker)
7. [Kubernetes](#kubernetes)
8. [Pipeline CI/CD](#pipeline-cicd)
9. [Probar el endpoint con curl](#probar-el-endpoint-con-curl)
10. [Variables de entorno](#variables-de-entorno)

---

## Contrato del endpoint

| Método | Ruta | Auth | Respuesta |
|---|---|---|---|
| `POST` | `/DevOps` | `X-Parse-REST-API-Key` + `X-JWT-KWY` | `200` `{"message": "Hello Juan Perez your message will be send"}` |
| `GET/PUT/PATCH/DELETE/OPTIONS/HEAD` | `/DevOps` | — | `405` texto plano `ERROR` |
| `POST` | `/api-manager/token` | `X-Parse-REST-API-Key` | `201` `{"token": "<jwt>", "transaction_id": "<uuid>", "expires_in": 300}` |
| `GET` | `/health` | — | `200` `{"status": "ok", "version": "1.0.0"}` |

Payload de entrada de `POST /DevOps`:

```json
{ "message": "This is a test", "to": "Juan Perez", "from": "Rita Asturia", "timeToLifeSec": 45 }
```

Códigos de error: `401` API key inválida/ausente, `401` JWT inválido/ausente/expirado,
`401` JWT ya utilizado (replay), `422` payload inválido.

## Arquitectura y decisiones de diseño

**Python + FastAPI.** Permite alcanzar cobertura total con muy poco código: validación de
payload declarativa (Pydantic), inyección de dependencias nativa para la seguridad y `TestClient`
para pruebas de integración sin levantar un servidor.

**Separación de responsabilidades** (cada módulo una sola razón para cambiar):

```
src/devops_service/
├── main.py          # fábrica de la app (create_app) y wiring de dependencias
├── config.py        # Settings desde variables de entorno (pydantic-settings)
├── schemas.py       # contratos de entrada/salida
├── services.py      # lógica de negocio (build_greeting)
├── api_manager.py   # API Manager: ApiKeyValidator + JwtManager + registro de transacciones
├── security.py      # dependencias FastAPI que traducen errores del API Manager a HTTP 401
└── routes/          # routers: devops.py, tokens.py, health.py
```

**API Manager y JWT único por transacción.** El módulo `api_manager.py` emite JWT HS256 con
`jti` (UUID v4), `iat`, `exp` e `iss`. Al consumir un token, el `jti` se registra en un
`TransactionRegistry`; un segundo uso del mismo JWT se rechaza con `401 Transaction JWT already used`.
El registro es un `Protocol`, con implementación en memoria por defecto; en un despliegue con
varias réplicas donde se exija replay-protection global bastaría con inyectar una implementación
sobre Redis (`SET jti EX ttl NX`) sin tocar el resto del código. El evaluador obtiene el JWT
llamando a `POST /api-manager/token` con la API key (ver sección curl).

**Secretos.** La API key y el secreto JWT solo existen como variables de entorno
(`.env` local ignorado por git, `Secret` de Kubernetes creado por el pipeline desde GitHub Secrets).
La comparación de la API key usa `hmac.compare_digest` (tiempo constante).

**Contenedor.** Dockerfile multi-stage (venv construido en `builder`, copiado a un `python:3.12-slim`
limpio), usuario no root, sistema de archivos de solo lectura, `HEALTHCHECK`.

**Kubernetes.** kustomize con `base` + overlays `dev`/`prod`: Deployment con 2 réplicas
(`RollingUpdate` sin downtime, anti-afinidad entre nodos, probes, hardening), Service
`LoadBalancer`, HPA 2→6 réplicas por CPU (crecimiento dinámico) y PodDisruptionBudget.

## Estructura del repositorio

```
.
├── .github/
│   ├── workflows/ci-cd.yml        # pipeline
│   └── actions/deploy/action.yml  # acción compuesta reutilizada por dev y prod
├── src/devops_service/            # código fuente
├── tests/
│   ├── unit/                      # api_manager, services, config
│   └── integration/               # endpoint /DevOps y /api-manager/token vía TestClient
├── infra/k8s/                     # IaC: base + overlays (ver infra/README.md)
├── Dockerfile · .dockerignore · docker-compose.yml
├── pyproject.toml                 # pytest, coverage (fail_under=90), ruff
├── requirements.txt · requirements-dev.txt   # dependencias fijadas (lockfile)
├── sonar-project.properties
└── Makefile
```

## Ejecución local

Requisitos: Python 3.12+.

```bash
git clone https://github.com/OWNER/devops-assessment.git && cd devops-assessment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # edita API_KEY y JWT_SECRET
make run                        # http://localhost:8000  (docs en /docs)
```

## Tests y cobertura

Los tests se escribieron antes que el código (TDD): primero fallaron por `ModuleNotFoundError`,
luego se implementó el mínimo para ponerlos en verde y se refactorizó.

```bash
make test          # pytest + cobertura (umbral mínimo 90 %, actual 100 %)
make lint          # ruff check + ruff format --check
pytest -m unit     # solo unitarios
pytest -m integration
```

## Docker

```bash
make docker-build                      # docker build -t devops-service:local .
make docker-run                        # usa .env
# o con compose:
docker compose up --build
```

## Kubernetes

Ver [`infra/README.md`](infra/README.md) para el detalle. Resumen:

```bash
kubectl create namespace devops-service
kubectl -n devops-service create secret generic devops-service-secrets \
  --from-literal=API_KEY="$API_KEY" --from-literal=JWT_SECRET="$JWT_SECRET"
kubectl apply -k infra/k8s/overlays/prod
kubectl -n devops-service get svc devops-service   # EXTERNAL-IP → HOST
```

Para probar en local con minikube: `minikube addons enable metrics-server` y
`minikube tunnel` para obtener IP del `LoadBalancer`.

## Pipeline CI/CD

Archivo: [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml)

```
push (cualquier rama) / PR / tag v* / manual
        │
        ├── lint   ─ ruff check, ruff format, hadolint (Dockerfile)
        ├── test   ─ pytest + cobertura (XML + JUnit publicados), SonarCloud si hay SONAR_TOKEN
        │
        └── build  ─ docker buildx → ghcr.io/OWNER/devops-service:{sha-xxxxxxx, <rama>, vX.Y.Z, latest}
                     smoke test real del contenedor (token → POST /DevOps → GET = ERROR)
                        │
                        ├── deploy-dev   ─ rama develop  (environment "development")
                        └── deploy-prod  ─ rama main/master (environment "production")
```

* **Se ejecuta en cualquier rama**; solo `main`/`master` despliega a producción.
* **Gestión de dependencias:** versiones fijadas en `requirements*.txt` + caché de pip en Actions
  + caché de capas Docker (`type=gha`).
* **Despliegue de cualquier versión bajo demanda:** `Actions → CI/CD → Run workflow` con
  `version=sha-abc1234` (o `v1.0.0`) y `environment=prod|dev`. Si `version` va vacío se construye
  desde el commit actual.
* **Sin credenciales de clúster** (`KUBE_CONFIG` ausente) los jobs de deploy hacen un render
  `kustomize build` (dry-run) y avisan; no fallan. Con credenciales, crean el Secret desde los
  GitHub Secrets, aplican el overlay y esperan el `rollout status`.

### Secrets requeridos en el repositorio

| Secret | Uso |
|---|---|
| `API_KEY` | Valor de `X-Parse-REST-API-Key` inyectado en el Secret de Kubernetes |
| `JWT_SECRET` | Secreto HS256 (≥32 caracteres aleatorios) |
| `KUBE_CONFIG` | `base64 -w0 ~/.kube/config` del clúster destino (opcional; sin él, dry-run) |
| `SONAR_TOKEN` | Opcional, activa el análisis en SonarCloud |

`GITHUB_TOKEN` se usa automáticamente para publicar en GHCR.

## Probar el endpoint con curl

```bash
HOST=localhost:8000        # o la EXTERNAL-IP del LoadBalancer (puerto 80)
API_KEY=2f5ae96c-b558-4c7b-a590-a501ae1c3f6c

# 1) Obtener un JWT único para la transacción (API Manager)
JWT=$(curl -s -X POST -H "X-Parse-REST-API-Key: $API_KEY" \
  http://$HOST/api-manager/token | python3 -c 'import sys,json; print(json.load(sys.stdin)["token"])')

# 2) Invocar el endpoint (mismo comando que usará el evaluador)
curl -X POST \
  -H "X-Parse-REST-API-Key: $API_KEY" \
  -H "X-JWT-KWY: ${JWT}" \
  -H "Content-Type: application/json" \
  -d '{ "message" : "This is a test", "to": "Juan Perez", "from": "Rita Asturia", "timeToLifeSec" : 45 }' \
  http://$HOST/DevOps
# → {"message":"Hello Juan Perez your message will be send"}

# 3) Reutilizar el mismo JWT → 401 {"detail":"Transaction JWT already used"}
# 4) Otro método → "ERROR"
curl -X GET http://$HOST/DevOps
```

Si el evaluador ejecuta el comando contra `https://${HOST}/DevOps`, el JWT se le entrega
generándolo con el paso 1 (o proporcionándole el valor por cualquier medio, como indica el reto).

## Variables de entorno

| Variable | Obligatoria | Default | Descripción |
|---|---|---|---|
| `API_KEY` | sí | — | Valor esperado de `X-Parse-REST-API-Key` |
| `JWT_SECRET` | sí | — | Secreto HS256 para firmar/verificar JWT |
| `JWT_TTL_SECONDS` | no | `300` | Vigencia de cada JWT de transacción |
| `PORT` | no | `8000` | Puerto del contenedor |
