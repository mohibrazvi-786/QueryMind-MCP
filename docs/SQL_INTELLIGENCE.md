# SQL Intelligence — QueryMind MCP

Natural-language-to-SQL and SQL validation pipeline.

## NL-to-SQL pipeline

```text
User Question
      |
      v
Intent Classification        (mock LLM provider, provider-independent)
      |
      v
Schema Retrieval             (hybrid RAG over discovered metadata)
      |
      v
Relationship Expansion       (foreign-key context)
      |
      v
SQL Generation               (PostgreSQL SELECT, grounded in schema hint)
      |
      v
SQLGlot Validation           (AST parse, read-only, single-statement, allowlists)
      |
      v
Schema Reference Validation  (tables/columns checked against discovered catalogue)
      |
      v
Safe SQL Response            (never executed by the generation step)
```

## Components

### LLM provider abstraction (`intelligence/llm/provider.py`)
`LLMProvider` interface with `generate(prompt)`. Defaults to
`MockLLMProvider` — deterministic, no external LLM or API key. Commercial
providers can be added by implementing the interface and configuring
`LLM_PROVIDER`.

### SQL generation service (`services/sql_generation_service.py`)
`SQLGenerationService.generate(question)` builds a schema hint from the
discovery catalogue, prompts the LLM, and returns a `SQLGenerationResult`
containing the SQL, explanation, referenced tables/columns, assumptions, and
confidence. Generated SQL is **not** executed here.

### SQL validation service (`services/sql_validation_service.py`)
`SQLValidationService.validate(sql)` uses SQLGlot AST parsing to enforce:
- Single statement only.
- SELECT-only (INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE/CREATE/GRANT/REVOKE
  and unknown statement types rejected).
- Disallowed functions rejected (e.g. `pg_sleep`).
- Schema/table allowlists.
- No keyword-only matching — AST-based.

`execute_readonly_query` re-validates at execution time and enforces
statement timeout, result row limit, and read-only transaction.

## Security

- LLM output is never trusted or executed directly.
- All executable SQL passes `validate_readonly_sql` before execution.
- Database content (comments, descriptions) treated as untrusted (prompt injection).
- Credentials never logged; connection strings redacted.

## Status

Implemented and unit-tested. Live SQL execution requires a real PostgreSQL
target database (see `docs/POSTGRESQL_INTEGRATION_CHECKLIST.md`).
