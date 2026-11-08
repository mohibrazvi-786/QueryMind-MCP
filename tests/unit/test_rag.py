"""Unit tests for RAG service (schema ingestion pipeline)."""

from __future__ import annotations

from types import SimpleNamespace

from querymind.intelligence.embeddings.provider import MockEmbeddingProvider
from querymind.intelligence.retrieval.service import RetrievalService
from querymind.services.discovery_service import DiscoveryService
from querymind.services.rag_service import RAGService


class FakeConnection:
    def __init__(self, tables: dict) -> None:
        self._tables = tables

    def execute(self, sql: str, params: dict | None = None):
        return []


def test_rag_ingest_schema_structure():
    catalogue = {
        "database_version": "PostgreSQL 17.11",
        "schemas": ["public"],
        "tables": [
            {
                "schema": "public",
                "name": "customers",
                "type": "BASE TABLE",
                "columns": [
                    {"column_name": "id", "data_type": "integer", "is_nullable": "NO"},
                    {"column_name": "email", "data_type": "varchar", "is_nullable": "YES"},
                ],
                "primary_keys": ["id"],
                "foreign_keys": [],
                "indexes": [],
                "stats": {"row_estimate": 100000},
            }
        ],
        "relationships": [],
        "indexes": [],
        "table_stats": [],
    }

    conn = FakeConnection({})
    svc = DiscoveryService(conn)
    # Monkeypatch discover_all to return our catalogue.
    svc.discover_all = lambda: catalogue  # type: ignore[method-assign]

    retrieval = RetrievalService(embedding_provider=MockEmbeddingProvider())
    rag = RAGService(discovery_service=svc, retrieval_service=retrieval)

    summary = rag.ingest_schema()
    assert summary["documents_indexed"] > 0
    assert summary["tables"] == 1
    assert summary["snapshot_version"] == "PostgreSQL 17.11"

    # Search should find the customers table.
    result = rag.search_schema("customers email", top_k=5)
    assert result.total_retrieved >= 1
    assert any(d.doc_type == "table" and d.table == "customers" for d in result.documents)
