"""Unit tests for embedding provider and hybrid retrieval service."""

from __future__ import annotations

from querymind.intelligence.embeddings.provider import MockEmbeddingProvider
from querymind.intelligence.retrieval.service import (
    RetrievedDocument,
    RetrievalService,
    cosine_similarity,
)


def test_mock_embedding_deterministic():
    provider = MockEmbeddingProvider()
    assert provider.dimension == 16
    v1 = provider.embed_text("hello world")
    v2 = provider.embed_text("hello world")
    assert v1 == v2
    assert len(v1) == 16

    batch = provider.embed_batch(["a", "b"])
    assert len(batch) == 2
    assert len(batch[0]) == 16


def test_mock_embedding_different_inputs_differ():
    provider = MockEmbeddingProvider()
    assert provider.embed_text("alpha") != provider.embed_text("beta")


def test_cosine_similarity():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine_similarity([], []) == 0.0


def test_retrieval_exact_table_match():
    provider = MockEmbeddingProvider()
    svc = RetrievalService(embedding_provider=provider)
    svc.index_documents(
        [
            RetrievedDocument(
                doc_id="table:public.customers",
                content="Table public.customers with columns: id, email.",
                relevance_score=0.0,
                source="schema.public.customers",
                doc_type="table",
                schema="public",
                table="customers",
            )
        ]
    )
    result = svc.search("customers", top_k=5)
    assert result.total_retrieved == 1
    assert result.documents[0].doc_type == "table"
    assert result.documents[0].relevance_score > 0


def test_retrieval_schema_filter():
    provider = MockEmbeddingProvider()
    svc = RetrievalService(embedding_provider=provider)
    svc.index_documents(
        [
            RetrievedDocument(
                doc_id="table:public.customers",
                content="Table public.customers.",
                relevance_score=0.0,
                source="schema.public.customers",
                doc_type="table",
                schema="public",
                table="customers",
            ),
            RetrievedDocument(
                doc_id="table:sales.report",
                content="Table sales.report.",
                relevance_score=0.0,
                source="schema.sales.report",
                doc_type="table",
                schema="sales",
                table="report",
            ),
        ]
    )
    result = svc.search("report", top_k=5, schema_filter="sales")
    assert all(d.schema == "sales" for d in result.documents)


def test_retrieval_without_embedding_provider():
    svc = RetrievalService()
    svc.index_documents(
        [
            RetrievedDocument(
                doc_id="table:public.customers",
                content="Table public.customers with email column.",
                relevance_score=0.0,
                source="schema.public.customers",
                doc_type="table",
                schema="public",
                table="customers",
            )
        ]
    )
    result = svc.search("customers email", top_k=5)
    assert result.total_retrieved == 1
