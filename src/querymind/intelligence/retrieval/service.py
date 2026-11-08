"""Hybrid schema retrieval.

Combines keyword search, exact table/column matching, semantic retrieval
(when an embedding provider is available), and relationship-aware context
expansion. Returns traceable source identifiers so every retrieved item can
be mapped back to actual discovered schema metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import math

from querymind.intelligence.embeddings.provider import EmbeddingProvider


@dataclass
class RetrievedDocument:
    """A retrieved schema document with provenance."""

    doc_id: str
    content: str
    relevance_score: float
    source: str  # e.g. "schema.public.customers"
    doc_type: str  # table | column | relationship | index | constraint
    schema: Optional[str] = None
    table: Optional[str] = None
    column: Optional[str] = None
    retrieval_method: str = "hybrid"


@dataclass
class RetrievalResult:
    """Result of a schema knowledge search."""

    query: str
    documents: list[RetrievedDocument] = field(default_factory=list)
    total_retrieved: int = 0


class RetrievalService:
    """Hybrid retrieval over normalized schema documents."""

    def __init__(self, *, embedding_provider: Optional[EmbeddingProvider] = None) -> None:
        self.embedding_provider = embedding_provider
        self._documents: dict[str, RetrievedDocument] = {}
        self._vectors: dict[str, list[float]] = {}

    def index_documents(self, documents: list[RetrievedDocument]) -> None:
        """Index (or re-index) schema documents. Replaces documents with the same doc_id."""
        for doc in documents:
            self._documents[doc.doc_id] = doc
            if self.embedding_provider is not None:
                self._vectors[doc.doc_id] = self.embedding_provider.embed_text(doc.content)

    def remove_document(self, doc_id: str) -> bool:
        removed = self._documents.pop(doc_id, None) is not None
        self._vectors.pop(doc_id, None)
        return removed

    def _cosine(self, a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1.0
        nb = math.sqrt(sum(y * y for y in b)) or 1.0
        return dot / (na * nb)

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        schema_filter: Optional[str] = None,
    ) -> RetrievalResult:
        """Hybrid search over schema documents."""
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        scored: list[tuple[float, RetrievedDocument]] = []

        query_vector = None
        if self.embedding_provider is not None:
            query_vector = self.embedding_provider.embed_text(query)

        for doc in self._documents.values():
            if schema_filter and doc.schema != schema_filter:
                continue

            score = 0.0
            methods = []

            # Exact table/column match (strongest signal).
            if doc.table and doc.table.lower() in query_lower:
                score += 0.5
                methods.append("exact_table")
            if doc.column and doc.column.lower() in query_lower:
                score += 0.4
                methods.append("exact_column")

            # Keyword overlap.
            content_terms = set(doc.content.lower().split())
            overlap = len(query_terms & content_terms)
            if overlap:
                score += 0.3 * min(overlap / max(len(query_terms), 1), 1.0)
                methods.append("keyword")

            # Semantic similarity.
            if query_vector is not None and doc.doc_id in self._vectors:
                sim = self._cosine(query_vector, self._vectors[doc.doc_id])
                if sim > 0:
                    score += 0.4 * sim
                    methods.append("semantic")

            if score > 0:
                doc.retrieval_method = "+".join(methods) or "keyword"
                doc.relevance_score = round(score, 4)
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]

        return RetrievalResult(
            query=query,
            documents=[doc for _, doc in top],
            total_retrieved=len(scored),
        )

    def relationship_expansion(
        self, documents: list[RetrievedDocument]
    ) -> list[RetrievedDocument]:
        """Expand retrieved documents with related table/column documents."""
        expanded = list(documents)
        seen = {d.doc_id for d in expanded}
        for doc in documents:
            if doc.doc_type == "table" and doc.schema and doc.table:
                # Find foreign-key relationship documents referencing this table.
                for other in self._documents.values():
                    if other.doc_id in seen:
                        continue
                    if other.doc_type == "relationship" and (
                        other.table == doc.table
                        or (other.content and doc.table.lower() in other.content.lower())
                    ):
                        expanded.append(other)
                        seen.add(other.doc_id)
        return expanded


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Public cosine similarity helper."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)
