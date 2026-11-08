"""Schema RAG ingestion pipeline.

Normalizes discovery catalogue output into traceable metadata documents,
chunks them, generates embeddings, and syncs with the retrieval service.
Never ingests actual customer records — only schema metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from querymind.intelligence.embeddings.provider import EmbeddingProvider
from querymind.intelligence.retrieval.service import RetrievedDocument, RetrievalService
from querymind.services.discovery_service import DiscoveryService


@dataclass
class SchemaDocument:
    """A normalized schema metadata document."""

    doc_id: str
    content: str
    doc_type: str  # database | schema | table | column | relationship | index | constraint
    schema: Optional[str] = None
    table: Optional[str] = None
    column: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class RAGService:
    """Ingests and synchronizes schema metadata into the retrieval index."""

    def __init__(
        self,
        *,
        discovery_service: DiscoveryService,
        retrieval_service: RetrievalService,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ) -> None:
        self.discovery = discovery_service
        self.retrieval = retrieval_service
        self.embedding_provider = embedding_provider
        self._snapshot_version: Optional[str] = None

    def ingest_schema(self) -> dict:
        """Run a full discovery and index all schema metadata documents."""
        catalogue = self.discovery.discover_all()
        self._snapshot_version = catalogue.get("database_version", "unknown")

        documents: list[SchemaDocument] = []

        # Database-level document.
        documents.append(
            SchemaDocument(
                doc_id=f"database:{catalogue.get('database_version','unknown')}",
                content=(
                    f"Database version: {catalogue.get('database_version','unknown')}. "
                    f"Schemas: {', '.join(catalogue.get('schemas', []))}. "
                    f"Tables: {len(catalogue.get('tables', []))}."
                ),
                doc_type="database",
                metadata={"databases": catalogue.get("schemas", [])},
            )
        )

        # Per-table documents with columns, PKs, FKs, indexes, stats.
        for table in catalogue.get("tables", []):
            schema = table["schema"]
            name = table["name"]
            cols = table.get("columns", [])
            col_descriptions = ", ".join(
                f"{c['column_name']} ({c.get('data_type')})" for c in cols
            )
            documents.append(
                SchemaDocument(
                    doc_id=f"table:{schema}.{name}",
                    content=(
                        f"Table {schema}.{name} ({table.get('type')}) with columns: {col_descriptions}. "
                        f"Primary keys: {', '.join(table.get('primary_keys', [])) or 'none'}. "
                        f"Indexes: {', '.join(i.get('index_name','') for i in table.get('indexes', [])) or 'none'}."
                    ),
                    doc_type="table",
                    schema=schema,
                    table=name,
                    metadata={"row_estimate": table.get("stats", {}).get("row_estimate")},
                )
            )
            # Per-column documents.
            for c in cols:
                documents.append(
                    SchemaDocument(
                        doc_id=f"column:{schema}.{name}.{c['column_name']}",
                        content=(
                            f"Column {schema}.{name}.{c['column_name']} "
                            f"({c.get('data_type')}, nullable={c.get('is_nullable')})."
                        ),
                        doc_type="column",
                        schema=schema,
                        table=name,
                        column=c["column_name"],
                        metadata={"data_type": c.get("data_type")},
                    )
                )
            # Per-index documents.
            for idx in table.get("indexes", []):
                documents.append(
                    SchemaDocument(
                        doc_id=f"index:{schema}.{name}.{idx.get('index_name')}",
                        content=(
                            f"Index {idx.get('index_name')} on {schema}.{name}: {idx.get('index_definition','')}"
                        ),
                        doc_type="index",
                        schema=schema,
                        table=name,
                        metadata={"index_definition": idx.get("index_definition")},
                    )
                )

        # Relationship documents from foreign keys.
        for rel in catalogue.get("relationships", []):
            documents.append(
                SchemaDocument(
                    doc_id=f"relationship:{rel.get('constraint_name')}",
                    content=(
                        f"Foreign key {rel.get('constraint_name')} from "
                        f"{rel.get('source_schema')}.{rel.get('source_table')}.{rel.get('source_column')} "
                        f"to {rel.get('target_schema')}.{rel.get('target_table')}.{rel.get('target_column')}"
                    ),
                    doc_type="relationship",
                    schema=rel.get("source_schema"),
                    table=rel.get("source_table"),
                    column=rel.get("source_column"),
                    metadata={
                        "target_schema": rel.get("target_schema"),
                        "target_table": rel.get("target_table"),
                        "target_column": rel.get("target_column"),
                    },
                )
            )

        # Convert to RetrievedDocument and index.
        retrieved_docs = [
            RetrievedDocument(
                doc_id=d.doc_id,
                content=d.content,
                relevance_score=0.0,
                source=f"schema.{d.schema or 'db'}.{d.table or ''}",
                doc_type=d.doc_type,
                schema=d.schema,
                table=d.table,
                column=d.column,
            )
            for d in documents
        ]

        self.retrieval.index_documents(retrieved_docs)

        return {
            "snapshot_version": self._snapshot_version,
            "documents_indexed": len(retrieved_docs),
            "schemas": catalogue.get("schemas", []),
            "tables": len(catalogue.get("tables", [])),
            "relationships": len(catalogue.get("relationships", [])),
            "indexes": len(catalogue.get("indexes", [])),
        }

    def sync_schema(self) -> dict:
        """Alias for ingest_schema (full re-index). Incremental sync is a
        future optimization; full re-index keeps metadata consistent."""
        return self.ingest_schema()

    def search_schema(self, query: str, *, top_k: int = 5, schema_filter=None):
        """Search indexed schema knowledge."""
        return self.retrieval.search(query, top_k=top_k, schema_filter=schema_filter)
