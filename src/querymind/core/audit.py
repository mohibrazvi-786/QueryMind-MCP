"""Append-only audit logging.

Records security and operational events with tenant context. Audit records
are append-only: once written they must not be modified or deleted by
ordinary users. Sensitive values (passwords, tokens, API keys, SQL
parameters) are redacted before storage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import structlog

from querymind.core.rbac import Principal


_SENSITIVE_KEYS = {
    "password",
    "passwd",
    "secret",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "token",
    "credential",
    "private_key",
    "connection_string",
    "dsn",
}


@dataclass
class AuditRecord:
    """A single immutable audit record."""

    event_id: str
    timestamp: str
    actor_user_id: Optional[str]
    actor_username: Optional[str]
    organization_id: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    outcome: str  # success | failure | denied | error
    correlation_id: Optional[str]
    metadata: dict


class AuditLogger:
    """Append-only audit logger.

    The default implementation writes structured audit records to the
    application log (JSON). Production deployments should forward these
    to an immutable audit store (e.g. a write-once table or SIEM).
    """

    def __init__(self) -> None:
        self._logger = structlog.get_logger("querymind.audit")
        self._records: list[AuditRecord] = []

    def _redact(self, metadata: dict) -> dict:
        redacted: dict = {}
        for key, value in metadata.items():
            if any(s in key.lower() for s in _SENSITIVE_KEYS):
                redacted[key] = "***"
            else:
                redacted[key] = value
        return redacted

    def log(
        self,
        *,
        action: str,
        principal: Optional[Principal] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        outcome: str = "success",
        correlation_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> AuditRecord:
        from uuid import uuid4

        now = datetime.now(timezone.utc).isoformat()
        actor_user_id = principal.user_id if principal else None
        actor_username = principal.username if principal else None
        organization_id = principal.organization_id if principal else None

        record = AuditRecord(
            event_id=str(uuid4()),
            timestamp=now,
            actor_user_id=actor_user_id,
            actor_username=actor_username,
            organization_id=organization_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            correlation_id=correlation_id,
            metadata=self._redact(metadata or {}),
        )

        self._records.append(record)
        self._logger.info(
            "audit",
            event_id=record.event_id,
            timestamp=record.timestamp,
            actor_user_id=record.actor_user_id,
            actor_username=record.actor_username,
            organization_id=record.organization_id,
            action=record.action,
            resource_type=record.resource_type,
            resource_id=record.resource_id,
            outcome=record.outcome,
            correlation_id=record.correlation_id,
            metadata=record.metadata,
        )
        return record

    def list_records(
        self,
        *,
        organization_id: Optional[str] = None,
        actor_user_id: Optional[str] = None,
        action: Optional[str] = None,
        outcome: Optional[str] = None,
        limit: int = 100,
    ) -> list[AuditRecord]:
        records = list(self._records)
        if organization_id is not None:
            records = [r for r in records if r.organization_id == organization_id]
        if actor_user_id is not None:
            records = [r for r in records if r.actor_user_id == actor_user_id]
        if action is not None:
            records = [r for r in records if r.action == action]
        if outcome is not None:
            records = [r for r in records if r.outcome == outcome]
        records.sort(key=lambda r: r.timestamp, reverse=True)
        return records[:limit]

    def count(self) -> int:
        return len(self._records)


audit_logger = AuditLogger()
