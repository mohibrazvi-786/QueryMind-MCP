# Dashboard — QueryMind MCP

## Overview

The web dashboard is a user interface for the existing QueryMind services.
It is secondary to the MCP server and does not reimplement business logic —
all logic is called through the backend API.

## Stack

Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS.

## Sections

| Section | Path | Description |
|---------|------|-------------|
| Overview | `/` | Connected databases, health, schema objects, slow queries, recommendations, anomalies |
| Connections | `/connections` | Add/test/edit/disable/delete connections; configure permitted schemas |
| AI Assistant | `/assistant` | Natural-language questions, generated SQL, validation |
| SQL Workspace | `/sql` | SQL editor, validation, EXPLAIN, read-only execution, history |
| Schema Explorer | `/schema` | Tables, columns, keys, indexes, relationships with search |
| Performance | `/performance` | Slow-query ranking, plan analysis, inefficiency findings, index recommendations |
| Anomaly Monitor | `/anomalies` | Metric history, baselines, detected anomalies, severity |
| Audit Logs | `/audit` | Actor, action, timestamp, resource, outcome, org (authorized roles only) |
| Organization | `/org` | Roles and organization management |

## Engineering requirements

- Typed API client (`src/lib/api.ts`).
- Reusable UI components (`src/components/ui/*`).
- Loading, error, and empty states.
- Form validation.
- Accessible keyboard navigation.
- Responsive mobile layouts.
- Secure session handling; no credentials in browser storage.
- No authorization logic exclusively in the frontend.
- No fake API responses in production.

## Status

Dashboard source is authored under `frontend/`. Frontend build and lint are
defined in CI but could not be executed in this environment because npm
tarball downloads are blocked (network restriction). The dashboard is
therefore unverified against a live backend.
