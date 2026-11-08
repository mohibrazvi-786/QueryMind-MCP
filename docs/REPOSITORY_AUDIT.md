# Repository Audit — QueryMind MCP

**Stage 0 deliverable.** Generated before any implementation began.

## 1. Summary

QueryMind MCP is a **greenfield project**. The working directory was empty and not a git repository. There is no existing code, infrastructure, dependency set, documentation, or CI/CD to integrate with or conflict against. QueryMind MCP will be created as a new, independent repository named `querymind-mcp`.

## 2. Current Repository Architecture

| Item | Finding |
|------|---------|
| Repository path | `C:\Users\91842\Desktop\AI_Bootcamp\projects\04_MCP` |
| Git initialized | No (`fatal: not a git repository`) |
| Branches | None |
| Remotes | None |
| Total entries in working dir | 0 |
| Existing projects | None |

There is no existing repository architecture to preserve. No existing GitHub workflows, naming conventions, or test infrastructure were found.

## 3. Existing Project Inventory

None. No projects, modules, packages, applications, or scripts exist in the working directory.

## 4. Available Development Environment

| Component | Version / Status | Meets baseline? |
|-----------|------------------|-----------------|
| OS | Windows (win32), PowerShell 5.1 | N/A |
| Python | 3.13.14 (`python.exe`, `pip.exe`) | Yes (baseline: 3.12+) |
| pip | 26.2.1 | Yes |
| Git | 2.56.0.windows.4 | Yes |
| Docker | Not installed | No |
| Docker Compose | Not installed | No |
| PostgreSQL server | Not installed (`psql` not found) | No |
| psql client | Not installed | No |
| pg_config | Not found | No |
| Virtual environment | None exists | N/A |
| venv module | Available (stdlib) | Yes |

**Python location:** `C:\Users\91842\AppData\Local\Programs\Python\Python313\python.exe`

**Notes:**
- Python 3.13 exceeds the 3.12+ baseline. FastMCP, SQLAlchemy 2.x, and Pydantic v2 must be verified for 3.13 compatibility at dependency-pinning time.
- The Microsoft Store `python.exe` shim (`C:\Users\91842\AppData\Local\Microsoft\WindowsApps\python3.exe`) is a redirector; use the real install at `...\Python313\python.exe` and `python -m pip`.
- Docker and PostgreSQL are not present locally. Local end-to-end testing against a real PostgreSQL instance will require installing Docker Desktop or PostgreSQL, or using a remote/managed PostgreSQL target for the discovery engine.

## 5. Existing Dependencies

None. No `pyproject.toml`, `requirements*.txt`, `Pipfile`, `poetry.lock`, or installed project packages were found beyond the global Python 3.13 site-packages.

**Dependency conflicts:** None (greenfield).

## 6. Existing Infrastructure

| Layer | Finding |
|-------|---------|
| Target (inspected) PostgreSQL database | None |
| QueryMind internal PostgreSQL database | None |
| Docker / container runtime | None (not installed) |
| Reverse proxy / TLS termination | None |
| Secret manager | None |
| CI/CD (GitHub Actions) | None |
| Observability stack (OTel, Prometheus) | None |

## Environment constraints (honest)

- **No Docker / container runtime.** Docker Desktop is not installed and `docker` is not on PATH. Testcontainers and Docker Compose local demos cannot run until Docker is installed.
- **No PostgreSQL server.** `psql`/`pg_config` are not installed, no service listens on port 5432, and no PostgreSQL binaries exist on disk.
- **PostgreSQL download blocked.** The official Windows installer is served from `get.enterprisedb.com`, which returns HTTP 403 Forbidden for both `winget` and direct downloads from this network/region. Chocolatey is present but non-functional (`choco` not on PATH, install incomplete).
- **Consequence:** The discovery engine cannot be exercised against a live PostgreSQL in this session. It can (and is) validated offline by parsing its SQL with SQLGlot and unit-testing its result-assembly logic against synthetic rows. A real PostgreSQL instance is required to complete the Stage 3 live demonstration.


## 7. Existing Documentation, AI/ML, FastAPI, MCP, Test Infrastructure

None found. No `README.md`, `docs/`, FastAPI application, MCP server implementation, embeddings/vector store, anomaly detection code, or Pytest suite exists.

## 8. Recommended Project Structure

Create `querymind-mcp` as an independent repository following the mandated layout:

```text
querymind-mcp/
├── src/querymind/
│   ├── mcp_server/
│   │   ├── server.py
│   │   ├── tools/{discovery,query,optimization,monitoring,documentation}.py
│   │   ├── resources/
│   │   └── prompts/
│   ├── api/
│   ├── core/{config,security,logging,exceptions}.py
│   ├── database/{connection,models,repositories,migrations}
│   ├── intelligence/{text_to_sql,schema_retrieval,embeddings,query_optimizer,anomaly_detection}.py
│   ├── services/{discovery_service,query_service,monitoring_service,reporting_service}.py
│   └── schemas/
├── tests/{unit,integration,security,mcp,evaluation}
├── evals/{text_to_sql,retrieval,anomaly_detection}
├── scripts/{seed_demo_data,benchmark_queries}.py
├── docs/{REPOSITORY_AUDIT,ARCHITECTURE,DATABASE_DESIGN,MCP_TOOLS,RAG_PIPELINE,SQL_SECURITY,QUERY_OPTIMIZATION,ANOMALY_DETECTION,EVALUATION,DEPLOYMENT,API_DOCUMENTATION,TESTING}.md
├── alembic/
├── docker/
├── .github/workflows/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env.example
├── .gitignore
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE
```

No existing code to duplicate; build modules progressively per the roadmap (discovery engine first).

## 9. Potential Conflicts

| Conflict | Risk | Mitigation |
|----------|------|------------|
| Python 3.13 vs. dependency support | Some AI/ML/DB packages may lag on 3.13 wheels | Pin after verifying 3.13 wheels; prefer `>=3.12,<3.14` bounds |
| No Docker locally | Can't run Testcontainers / Compose locally | Develop against an externally provisioned PostgreSQL; add Docker when available |
| Windows PowerShell 5.1 | Some Unix-oriented scripts/tooling may not port directly | Use cross-platform Python; avoid shell-only assumptions in CI |
| No secret manager | Credentials must not be stored plaintext | `.env.example` only; runtime secrets via environment variables |

## 10. Integration Risks

| Risk | Description | Impact |
|------|-------------|--------|
| No local PostgreSQL | First milestone (discovery engine) needs a real PG instance | Provision a target PostgreSQL (local install, Docker, or cloud dev DB) before Stage 3 |
| No Docker | Compose-based local demo cannot run end-to-end locally | Document remote-Docker alternative; CI can build images |
| Greenfield security baseline | Auth/RBAC/audit must be built from scratch | Implement security in Stage 8 alongside, not after, the discovery engine |

## 11. Recommended Implementation Strategy

1. **Stage 0 (complete):** Repository audit → this document.
2. **Stage 1:** Architecture (`ARCHITECTURE.md`), database design (`DATABASE_DESIGN.md`), implementation plan (`IMPLEMENTATION_PLAN.md`), dependency decisions.
3. **Stage 2:** Python project scaffolding (`pyproject.toml`, package layout), virtual environment, Alembic, internal database models/migrations.
4. **Stage 3:** Database Discovery Engine (SQLAlchemy + PostgreSQL catalogues) — first working milestone: accurate JSON schema report without hardcoded table names.
5. **Stage 4:** MCP server (FastMCP), all 19 tools, 6 resources, 6 prompts, STDIO + Streamable HTTP.
6. **Stage 5:** Schema RAG + natural-language-to-SQL + SQLGlot validation + read-only execution.
7. **Stage 6:** Execution-plan analysis, index advisor, health monitoring, reporting.
8. **Stage 7:** Statistical anomaly detection + Isolation Forest experiment.
9. **Stage 8:** Authentication, RBAC, organization isolation, SQL execution policies, audit logging.
10. **Stage 9:** Optional web dashboard.
11. **Stage 10–12:** Testing, Docker/CI, documentation, release preparation.

**Guarding rules:** No empty placeholder modules; no hardcoded AI responses; no fabricated schema or evaluation results; no unrestricted SQL execution; no secrets committed.

## 12. Next Immediate Action

Create `docs/ARCHITECTURE.md`, `docs/DATABASE_DESIGN.md`, and `IMPLEMENTATION_PLAN.md`, then scaffold the Python project and implement the discovery service against a real PostgreSQL instance.
