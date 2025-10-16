"""Unit tests for metadata models."""

from __future__ import annotations

from datetime import datetime

from zoho_creator_sdk.models.metadata import AuditMetadata, Metadata, SystemMetadata


def test_audit_metadata_parses_iso_strings() -> None:
    meta = AuditMetadata(createdAt="2024-01-01T00:00:00Z")
    assert isinstance(meta.created_at, datetime)

    meta_invalid = AuditMetadata(createdAt="invalid")
    assert meta_invalid.created_at is None

    now = datetime.utcnow()
    meta_direct = AuditMetadata(createdAt=now)
    assert meta_direct.created_at == now


def test_system_metadata_parses_archive_time() -> None:
    system = SystemMetadata(archivedAt="2024-01-01T00:00:00Z")
    assert isinstance(system.archived_at, datetime)
    assert system.is_active is True

    system_invalid = SystemMetadata(archivedAt="not-a-date")
    assert system_invalid.archived_at is None


def test_metadata_tag_and_property_helpers() -> None:
    meta = Metadata()
    meta.update_tags("a", "b")
    assert "a" in meta.tags

    meta.remove_tags("a")
    assert "a" not in meta.tags

    meta.set_property("key", "value")
    assert meta.get_property("key") == "value"

    meta.remove_tags("missing")
    assert meta.get_property("missing") is None

    meta.custom_properties = None  # type: ignore[assignment]
    assert meta.get_property("key") is None
