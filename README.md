# Stratum

Stratum is a multi-tenant AI Operations Platform built for enterprise workloads: document ingestion with OCR and intelligent chunking, hybrid semantic search with automatic grounding validation, LangGraph-powered workflow orchestration, and continuous RAG quality measurement via RAGAS — all behind a hardened API gateway with per-tenant isolation enforced at every layer.

---

## Architecture

```
                          ┌─────────────────────────────────────────┐
                          │              React Frontend               │
                          │         (Vite · React 18 · Zustand)      │
                          └────────────────────┬────────────────────┘
                                               │ HTTPS
                          ┌────────────────────▼────────────────────┐
                          │               Gateway :8000              │
                          │     JWT validation · tenant resolution   │
                          │       rate limiting · header injection   │
                          └──┬──────┬──────┬──────┬──────┬──────┬──┘
                             │      │      │      │      │      │
              ┌──────────────▼─┐ ┌──▼───┐ │ ┌───▼──┐ ┌─▼───┐ │
              │ Identity :8001 │ │Ingest│ │ │Workfl│ │Conn.│ │
              │  users/tenants │ │:8002 │ │ │:8004 │ │:8005│ │
              └────────────────┘ └──┬───┘ │ └──┬───┘ └──┬──┘ │
                                    │     │    │        │    │
                          ┌─────────▼─┐ ┌─▼───▼──┐    │    │
                          │ Retrieval │ │Observer │    │    │
                          │   :8003   │ │  :8006  │    │    │
                          └─────┬─────┘ └────┬────┘    │    │
                                │            │         │    │
                          ┌─────▼────────────▼─────────▼────▼──────┐
                          │              Redis Streams               │
                          │     (event bus — all services publish)   │
                          └──────────────────┬──────────────────────┘
                                             │
                          ┌──────────────────▼──────────────────────┐
                          │           Evaluation :8007               │
                          │    RAGAS scoring · quality gates         │
                          └──────────────────┬──────────────────────┘
                                             │
        ┌────────────────┬──────────────────┬┴─────────────────┐
        │                │                  │                   │
  ┌─────▼──────┐  ┌──────▼──────┐  ┌───────▼──────┐  ┌────────▼────────┐
  │ PostgreSQL │  │    Qdrant   │  │    MinIO     │  │ Prometheus +    │
  │   :5432    │  │    :6333    │  │  :9000/9001  │  │ Grafana :9090/  │
  │ source of  │  │  vector DB  │  │  doc storage │  │ :3000           │
  │   truth    │  │             │  │              │  └─────────────────┘
  └────────────┘  └─────────────┘  └──────────────┘
```

**Communication rules:** Gateway is the only internet-facing service. Internal services communicate via HTTP (synchronous) or Redis Streams (async events). No service imports another's code.

---

## Tech Stack

### Backend
| Category | Technology |
|---|---|
| Runtime | Python 3.11+, FastAPI, ARQ |
| Workflow orchestration | LangGraph (inside workflow service) |
| LLM — generation | gpt-4o |
| LLM — grounding validation | gpt-4o-mini |
| Embeddings | `BAAI/bge-small-en-v1.5` (local) |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` (local) |
| RAG evaluation | RAGAS |
| Async tasks | ARQ workers (ingestion, workflow, connectors) |
| Logging | structlog + OpenTelemetry |

### Data
| Category | Technology |
|---|---|
| Primary store | PostgreSQL 15 |
| Vector store | Qdrant |
| Cache / event bus | Redis 7 (Streams) |
| Object storage | MinIO |

### Frontend
| Category | Technology |
|---|---|
| Framework | React 18, Vite |
| State | Zustand, TanStack Query |
| Charts | Recharts |
| Build tooling | uv, Ruff, mypy, pre-commit |

### Infrastructure
| Category | Technology |
|---|---|
| Containers | Docker Compose (dev), k3s (prod) |
| Ingress | Traefik |
| Metrics | Prometheus + Grafana |
| Tracing | OpenTelemetry + Jaeger |

---

## RAG Pipeline

Every search request runs this pipeline in order:

```
Query
  │
  ├─ embed (bge-small-en-v1.5, local)          dense vector
  ├─ expand abbreviations → BM25 encode         sparse vector
  │
  ▼
Qdrant hybrid search (asyncio.gather)
  ├─ vector top-20  (pre-filtered by tenant_id)
  └─ BM25 top-20    (pre-filtered by tenant_id)
  │
  ▼
RRF fusion → top-20 candidates
  │
  ▼
Rerank (ms-marco-MiniLM, local) → top-5
  │
  ▼
Generate answer (gpt-4o)
  │
  ▼
Grounding validation (gpt-4o-mini)
  ├─ pass  → return answer
  └─ fail  → regenerate with strict prompt → re-validate → return
  │
  ▼
Log to PostgreSQL + publish to Redis Streams
  │
  ▼
Async: trigger RAGAS evaluation (fire-and-forget)
```

### Benchmark scores

| Metric | Score |
|---|---|
| Faithfulness | 1.00 |
| Answer relevancy | — |
| Context precision | — |
| Overall (RAGAS) | 0.88 |

---

## Quick Start

**Prerequisites:** Docker, Docker Compose, an OpenAI API key.

```bash
# 1. Clone and enter the repo
git clone <repo-url> stratum
cd stratum/infrastructure

# 2. Copy and fill in environment files
cp .env.example .env
# Set OPENAI_API_KEY and Postgres/Redis/MinIO credentials in .env
# Copy per-service .env.docker.example files in each services/<name>/ directory

# 3. Start all services
docker compose up --build -d

# 4. Verify everything is healthy
docker compose ps

# 5. Open the frontend
open http://localhost:5173   # or start the dev server: cd frontend && npm install && npm run dev
```

Default Grafana credentials: `admin` / `stratum_admin` at `http://localhost:3000`.

---

## Services

| Service | Port | Description |
|---|---|---|
| gateway | 8000 | API gateway — JWT auth, tenant resolution, rate limiting |
| identity | 8001 | Users, tenants, roles, API keys, refresh tokens |
| ingestion | 8002 | Document parsing, chunking, embedding, Qdrant indexing |
| retrieval | 8003 | Hybrid search, reranking, grounding, answer generation |
| workflow | 8004 | LangGraph agent orchestration and tool dispatch |
| connectors | 8005 | Slack, Jira, GitHub integrations and webhook ingestion |
| observer | 8006 | Audit log, LLM call tracking, SSE stream (Redis subscriber) |
| evaluation | 8007 | RAGAS scoring and quality gates on every search result |
| PostgreSQL | 5432 | Primary datastore |
| Qdrant | 6333 | Vector database |
| Redis | 6379 | Task queue and event bus |
| MinIO | 9000 | Object storage for raw documents |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Dashboards |
| pgAdmin | 5050 | Postgres UI |

---

## Observability

Metrics are scraped by Prometheus and visualized in Grafana. Two pre-built dashboards ship with the repo:

| Dashboard | What it shows |
|---|---|
| **Stratum Platform Overview** | Documents ingested, total searches, workflow runs, average RAGAS score, faithfulness / answer relevancy / context precision gauges, RAG score over time, latency distribution, grounding pass rate |
| **Infrastructure Monitoring** | Per-service resource usage, Redis memory, Qdrant health, Postgres connections |

All services emit structured logs via `structlog`. Every Redis Streams event carries `tenant_id` for per-tenant filtering. The observer service aggregates all events into a unified audit log.

---

## Key Engineering Decisions

- **Retrieval never writes to Qdrant.** Qdrant writes are strictly owned by the ingestion service. This makes it safe to scale retrieval horizontally without any coordination concern around index consistency.

- **Grounding validation blocks the response path.** If gpt-4o-mini detects that more than 15% of the generated answer is unsupported by retrieved chunks, the pipeline regenerates with a stricter prompt before returning — rather than flagging it post-hoc.

- **All evaluation is fire-and-forget.** The retrieval endpoint triggers RAGAS scoring in a background `asyncio.Task` after committing the log entry. This keeps p99 search latency unaffected by evaluation throughput.

- **Tenant isolation is enforced at every layer.** Tenant ID comes from the JWT claim at the gateway; it is injected as a header and trusted by internal services. Every Postgres query and every Qdrant search is pre-filtered by `tenant_id` — there is no path that can leak cross-tenant data.

- **Abbreviation expansion is sparse-only.** The BM25 (sparse) path expands abbreviations like "PR → pull requests" to improve term overlap with document vocabulary. The dense vector path receives the raw query — expanding abbreviations there degrades semantic similarity.
