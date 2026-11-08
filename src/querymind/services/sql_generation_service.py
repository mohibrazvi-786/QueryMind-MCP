"""Natural-language-to-SQL generation pipeline.

Separates SQL generation from execution. Generated SQL is never executed
directly here — it must pass through SQLValidationService before any
read-only execution tool may run it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from querymind.core.exceptions import ValidationError
from querymind.intelligence.llm.provider import LLMClient, LLMProvider
from querymind.services.discovery_service import DiscoveryService
from querymind.services.sql_validation_service import SQLValidationResult


@dataclass
class SQLGenerationResult:
    """Result of generating SQL from a natural-language question."""

    question: str
    sql: str
    explanation: str
    referenced_tables: list[str] = field(default_factory=list)
    referenced_columns: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    validation: Optional[SQLValidationResult] = None
    confidence: str = "low"  # low | medium | high — only when meaningful


class SQLGenerationService:
    """Generates PostgreSQL SQL from natural-language questions using schema context."""

    def __init__(
        self,
        *,
        llm_provider: LLMProvider,
        discovery_service: DiscoveryService,
        validation_service,
    ) -> None:
        self.llm = LLMClient(llm_provider)
        self.discovery = discovery_service
        self.validation = validation_service

    def generate(
        self,
        question: str,
        *,
        allowed_schemas: Optional[set[str]] = None,
        allowed_tables: Optional[set[str]] = None,
        validate: bool = True,
    ) -> SQLGenerationResult:
        """Generate SQL for a question, optionally validating it."""
        # Retrieve relevant schema context to ground the generation.
        catalogue = self.discovery.discover_all()
        schema_hint = self._build_schema_hint(catalogue)

        prompt = self._build_prompt(question, schema_hint)
        sql = self.llm.generate_sql(prompt)

        result = SQLGenerationResult(
            question=question,
            sql=sql,
            explanation=self._explain_sql(sql),
            assumptions=self._detect_assumptions(question, sql, catalogue),
        )

        # Extract referenced tables/columns from the raw SQL for the response.
        try:
            parsed = self.validation.validate(sql)
            result.referenced_tables = parsed.tables
            result.referenced_columns = parsed.columns
            if validate:
                result.validation = parsed
        except Exception:  # noqa: BLE001 - validation failure is reported, not fatal here
            result.validation = None
            result.assumptions.append("Generated SQL could not be validated; review before execution.")

        # Confidence reflects whether validation passed and schema objects exist.
        if result.validation and result.referenced_tables:
            result.confidence = "medium"
        else:
            result.confidence = "low"

        return result

    def _build_schema_hint(self, catalogue: dict) -> str:
        lines = []
        for table in catalogue.get("tables", [])[:20]:
            cols = ", ".join(c.get("column_name", "") for c in table.get("columns", []))
            lines.append(f"{table['schema']}.{table['name']}({cols})")
        return "\n".join(lines)

    def _build_prompt(self, question: str, schema_hint: str) -> str:
        return (
            "You are a PostgreSQL SQL generator. Generate a single read-only SELECT statement.\n"
            "Use ONLY the tables and columns listed below. Do not invent names.\n"
            f"Schema:\n{schema_hint}\n\n"
            f"Question: {question}\n\n"
            "Return only the SQL statement, no markdown fences, no explanation."
        )

    @staticmethod
    def _explain_sql(sql: str) -> str:
        if not sql:
            return "No SQL generated."
        first = sql.strip().splitlines()[0][:80]
        return f"Generated query begins: {first}"

    @staticmethod
    def _detect_assumptions(
        question: str, sql: str, catalogue: dict
    ) -> list[str]:
        assumptions: list[str] = []
        known_tables = {
            (t["schema"], t["name"]) for t in catalogue.get("tables", [])
        }
        known_columns: set[tuple[str, str, str]] = set()
        for t in catalogue.get("tables", []):
            for c in t.get("columns", []):
                known_columns.add((t["schema"], t["name"], c["column_name"]))

        # Heuristic: detect references to tables/columns not in catalogue.
        import re

        for token in re.findall(r"\b[a-z_][a-z0-9_]*\b", sql.lower()):
            if token in {"select", "from", "where", "and", "or", "join", "on", "group", "by", "order", "limit", "as", "sum", "count", "avg", "min", "max", "having", "left", "right", "inner", "outer", "union", "all", "case", "when", "then", "else", "end", "null", "is", "in", "like", "between", "asc", "desc"}:
                continue
            # crude: skip numeric-looking tokens
            if token.isdigit():
                continue
            found = any(
                token == name for _, name, col in known_columns if col == token
            ) or any(token == name for _, name in known_tables)
            if not found:
                assumptions.append(f"Unverified schema reference: '{token}'")
                break  # keep concise
        if not assumptions:
            assumptions.append("All referenced schema objects appear present in the discovered catalogue.")
        return assumptions
