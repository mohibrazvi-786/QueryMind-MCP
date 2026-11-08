"""Provider-independent embedding interface.

Supports a deterministic mock embedding provider for tests and an optional
local Sentence Transformers provider. No external LLM or embedding API key
is required in the default configuration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import math


class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension."""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts."""


class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic mock embedding provider.

    Produces stable, content-derived embeddings without any external model.
    Suitable for tests and offline development.
    """

    name = "mock"
    dimension = 16

    def embed_text(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            # Stable hash-derived vector so identical inputs => identical vectors.
            vector = [0.0] * self.dimension
            for i, ch in enumerate(text.lower()):
                vector[i % self.dimension] += float(ord(ch)) / 255.0
            # Normalize to unit length for cosine comparisons.
            norm = math.sqrt(sum(v * v for v in vector)) or 1.0
            vectors.append([v / norm for v in vector])
        return vectors
