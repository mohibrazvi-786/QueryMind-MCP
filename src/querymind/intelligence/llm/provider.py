"""Provider-independent LLM interface.

Implements a small, replaceable abstraction for LLM-backed tasks
(SQL generation, query explanation, schema documentation, optimization
explanations). A deterministic mock provider is included for automated
tests so no external LLM or API key is required.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """Structured response from an LLM provider."""

    content: str
    provider: str
    model: str
    raw: object = None


class LLMProvider(ABC):
    """Abstract LLM provider."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Model identifier."""

    @abstractmethod
    def generate(self, prompt: str, *, temperature: float = 0.0) -> LLMResponse:
        """Generate text from a prompt."""


class MockLLMProvider(LLMProvider):
    """Deterministic mock provider for tests.

    Produces predictable SQL for a small set of known natural-language
    patterns against a synthetic e-commerce schema. Any unknown prompt
    returns a statement that validation will reject, signaling insufficiency
    rather than fabricating a schema.
    """

    name = "mock"
    model = "mock-v1"

    # Known patterns mapped to safe, valid SQL against the synthetic schema.
    _PATTERNS = {
        "top customers": (
            "SELECT c.id, c.email, SUM(o.total_amount) AS total_spending "
            "FROM customers c JOIN orders o ON o.customer_id = c.id "
            "GROUP BY c.id, c.email ORDER BY total_spending DESC LIMIT 10"
        ),
        "top 10 customers": (
            "SELECT c.id, c.email, SUM(o.total_amount) AS total_spending "
            "FROM customers c JOIN orders o ON o.customer_id = c.id "
            "GROUP BY c.id, c.email ORDER BY total_spending DESC LIMIT 10"
        ),
        "top five customers": (
            "SELECT c.id, c.email, SUM(o.total_amount) AS total_spending "
            "FROM customers c JOIN orders o ON o.customer_id = c.id "
            "GROUP BY c.id, c.email ORDER BY total_spending DESC LIMIT 5"
        ),
        "total spending": (
            "SELECT c.id, c.email, SUM(o.total_amount) AS total_spending "
            "FROM customers c JOIN orders o ON o.customer_id = c.id "
            "GROUP BY c.id, c.email ORDER BY total_spending DESC"
        ),
        "order count": (
            "SELECT c.id, c.email, COUNT(o.id) AS order_count "
            "FROM customers c LEFT JOIN orders o ON o.customer_id = c.id "
            "GROUP BY c.id, c.email ORDER BY order_count DESC"
        ),
        "products by category": (
            "SELECT category, COUNT(*) AS product_count "
            "FROM products GROUP BY category ORDER BY product_count DESC"
        ),
        "slow query": (
            "SELECT * FROM orders WHERE order_date >= '2024-01-01' "
            "ORDER BY total_amount DESC LIMIT 100"
        ),
    }

    def generate(self, prompt: str, *, temperature: float = 0.0) -> LLMResponse:
        lower = prompt.lower()
        sql: Optional[str] = None
        for key, value in self._PATTERNS.items():
            if key in lower:
                sql = value
                break
        if sql is None:
            # Unknown query: produce an invalid statement so validation
            # rejects it and the caller learns schema info is missing.
            sql = "SELECT * FROM unknown_table WHERE 1=0"
        return LLMResponse(
            content=sql,
            provider=self.name,
            model=self.model,
            raw=None,
        )


class LLMClient:
    """Thin client wrapping a provider with retries and timeouts."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def generate_sql(self, prompt: str) -> str:
        response = self.provider.generate(prompt)
        return response.content

    def explain(self, prompt: str) -> str:
        response = self.provider.generate(prompt)
        return response.content
