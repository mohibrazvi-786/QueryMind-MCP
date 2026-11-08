"""Unit tests for audit logging."""

from __future__ import annotations

from querymind.core.audit import AuditLogger, audit_logger
from querymind.core.rbac import Principal


def test_audit_log_append_only_record():
    logger = AuditLogger()
    principal = Principal(
        user_id="u1", username="alice", organization_id="org-1", role="viewer"
    )
    record = logger.log(
        action="sql:execute",
        principal=principal,
        resource_type="query",
        resource_id="q-1",
        outcome="success",
        correlation_id="corr-1",
        metadata={"rows": 10},
    )
    assert record.event_id
    assert record.action == "sql:execute"
    assert record.actor_user_id == "u1"
    assert record.organization_id == "org-1"
    assert record.outcome == "success"
    assert record.correlation_id == "corr-1"
    assert record.metadata == {"rows": 10}


def test_audit_redacts_sensitive_keys():
    logger = AuditLogger()
    record = logger.log(
        action="login",
        metadata={"password": "secret123", "api_key": "key-xyz", "username": "alice"},
    )
    assert record.metadata["password"] == "***"
    assert record.metadata["api_key"] == "***"
    assert record.metadata["username"] == "alice"


def test_audit_list_and_filter():
    logger = AuditLogger()
    p1 = Principal(user_id="u1", username="alice", organization_id="org-1", role="viewer")
    p2 = Principal(user_id="u2", username="bob", organization_id="org-2", role="viewer")
    logger.log(action="sql:generate", principal=p1, outcome="success")
    logger.log(action="sql:execute", principal=p2, outcome="denied")
    logger.log(action="sql:generate", principal=p1, outcome="failure")

    org1 = logger.list_records(organization_id="org-1")
    assert len(org1) == 2

    denied = logger.list_records(outcome="denied")
    assert len(denied) == 1
    assert denied[0].action == "sql:execute"

    gen = logger.list_records(action="sql:generate")
    assert len(gen) == 2


def test_audit_count():
    logger = AuditLogger()
    assert logger.count() == 0
    logger.log(action="x", metadata={})
    assert logger.count() == 1


def test_global_audit_logger():
    assert audit_logger is not None
