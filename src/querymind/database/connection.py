"""PostgreSQL connection management for target databases."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from querymind.core.exceptions import ConnectionError, DatabaseError


class TargetConnection:
    """A managed, read-only connection to a target PostgreSQL database.

    Enforces statement timeouts, result limits, and a read-only transaction
    mode so callers cannot accidentally issue destructive statements through
    this service layer.
    """

    def __init__(
        self,
        database_url: str,
        *,
        statement_timeout_ms: int = 10000,
        max_result_rows: int = 1000,
        organization_id: Optional[str] = None,
    ) -> None:
        self.database_url = database_url
        self.statement_timeout_ms = statement_timeout_ms
        self.max_result_rows = max_result_rows
        self.organization_id = organization_id
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    def connect(self) -> "TargetConnection":
        try:
            self._engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=5,
                connect_args={
                    "options": (
                        f"-c statement_timeout={self.statement_timeout_ms} "
                        f"-c default_transaction_read_only=on"
                    )
                },
            )
            self._session_factory = sessionmaker(bind=self._engine, autoflush=False)
            # Verify connectivity.
            with self.session() as session:
                session.execute(text("SELECT 1"))
        except Exception as exc:  # noqa: BLE001 - wrap any DB connectivity failure
            raise ConnectionError(f"Cannot connect to target database: {exc}") from exc
        return self

    @contextmanager
    def session(self) -> Iterator[Session]:
        if self._session_factory is None:
            raise ConnectionError("TargetConnection not connected; call .connect() first")
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def execute(self, sql: str, params: Optional[dict] = None):
        """Execute a single read-only statement and return rows as dicts."""
        if self._session_factory is None:
            raise ConnectionError("TargetConnection not connected; call .connect() first")
        with self.session() as session:
            result = session.execute(text(sql), params or {})
            rows = [dict(row._mapping) for row in result.mappings()]
            if len(rows) > self.max_result_rows:
                rows = rows[: self.max_result_rows]
            return rows

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
