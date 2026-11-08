# RAG Pipeline — QueryMind MCP

Schema-aware Retrieval-Augmented Generation for database intelligence.

## Objective

The LLM must not receive the entire database schema on every request. Instead,
only the relevant schema information is retrieved and provided as context.

## Pipeline

```text
PostgreSQL Database
        |
        v
Discovery Service  (information_schema + pg_catalog)
        |
        v
Schema Normalization
        |
        v
Metadata Document Creation  (database / schema / table / column / PK / FK / index / relationship)
        |
        v
Chunking
        |
        v
Embedding Generation        (MockEmbeddingProvider default; pluggable provider interface)
        |
        v
Vector / Keyword Index      (in-memory RetrievalService; pgvector optional)
        |
        v
Hybrid Retrieval            (keyword + exact table/column match + semantic + relationship expansion)
        |
        v
Relevant Schema Context
        |
        v
LLM (provider-independent)
```

## Components

### Discovery service
Queries PostgreSQL system catalogues (`information_schema`, `pg_catalog`,
`pg_class`, `pg_attribute`, `pg_constraint`, `pg_indexes`, `pg_stat_user_tables`)
to produce a schema catalogue without hardcoding table names.

### RAG service (`services/rag_service.py`)
Ingests the discovery catalogue into traceable metadata documents and syncs
them to the retrieval index. Supports full (re)indexing.

### Retrieval service (`intelligence/retrieval/service.py`)
Hybrid retrieval combining:
- Exact table/column name match.
- Keyword overlap.
- Semantic similarity (when an embedding provider is configured).
- Relationship-aware context expansion (foreign keys).

Returns `RetrievedDocument` objects with `doc_id`, `source`, `doc_type`,
`schema`, `table`, `column`, `relevance_score`, and `retrieval_method` so
every result is traceable to actual discovered metadata.

### Embedding provider (`intelligence/embeddings/provider.py`)
Provider-independent interface (`EmbeddingProvider`). Defaults to
`MockEmbeddingProvider` (deterministic, no external model or API key).
A Sentence Transformers provider can be plugged in via configuration.

## Schema synchronization

- Initial schema indexing via `ingest_schema()`.
- Changed/removed table and column detection (future incremental sync).
- Versioned schema snapshots tracked via `database_version`.
- Stale documents replaced by `doc_id` on re-index.

## Security

- Retrieved schema comments, descriptions, and metadata are treated as **untrusted**
  data — never as system instructions (prompt-injection defence).
- Authorization is enforced before retrieval and again before exposing results.
- Cross-tenant retrieval is blocked.
- No actual customer records are ingested — only schema metadata.

## Status

Implemented and unit-tested with deterministic mock embeddings. Semantic
retrieval with a real embedding model is optional and can be enabled by
configuring an `EmbeddingProvider`; pgvector is not required.
