"""Unit tests for :mod:`zoho_creator_sdk.models.bulk_operations`."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from zoho_creator_sdk.models.bulk_operations import BulkOperation
from zoho_creator_sdk.models.enums import BulkOperationStatus, BulkOperationType


def _base_payload() -> dict[str, object]:
    now = datetime.utcnow()
    return {
        "operation_id": "op",
        "operation_type": BulkOperationType.IMPORT,
        "status": BulkOperationStatus.IN_PROGRESS,
        "application_id": "app",
        "form_id": "form",
        "initiated_by": "user",
        "initiated_at": now,
        "started_at": now,
        "completed_at": now + timedelta(seconds=10),
        "total_records": 10,
        "processed_records": 8,
        "successful_records": 6,
        "failed_records": 2,
        "progress_percentage": 0,
        "duration_seconds": None,
    }


def test_bulk_operation_progress_and_duration() -> None:
    payload = _base_payload()
    bulk = BulkOperation(**payload)

    assert pytest.approx(bulk.progress_percentage, rel=1e-3) == 80.0
    assert bulk.duration_seconds == 10
    assert bulk.is_complete is False
    assert pytest.approx(bulk.success_rate) == 75.0
    assert pytest.approx(bulk.failure_rate) == 25.0

    payload_done = _base_payload()
    payload_done.update(
        {
            "status": BulkOperationStatus.CANCELLED,
            "processed_records": 0,
            "successful_records": 0,
            "failed_records": 0,
            "total_records": 0,
        }
    )
    assert BulkOperation(**payload_done).is_complete is True


def test_bulk_operation_completed_requires_timestamp() -> None:
    payload = _base_payload()
    payload.update({"status": BulkOperationStatus.COMPLETED, "completed_at": None})

    with pytest.raises(ValueError):
        BulkOperation(**payload)


def test_bulk_operation_failed_requires_error_message() -> None:
    payload = _base_payload()
    payload.update({"status": BulkOperationStatus.FAILED, "error_message": None})

    with pytest.raises(ValueError):
        BulkOperation(**payload)


def test_bulk_operation_processed_constraints() -> None:
    payload = _base_payload()
    payload["processed_records"] = 5
    payload["successful_records"] = 5
    payload["failed_records"] = 1

    with pytest.raises(ValueError):
        BulkOperation(**payload)

    payload_over = _base_payload()
    payload_over["processed_records"] = 11

    with pytest.raises(ValueError):
        BulkOperation(**payload_over)


def test_bulk_operation_duration_mismatch() -> None:
    payload = _base_payload()
    payload["duration_seconds"] = 1

    with pytest.raises(ValueError):
        BulkOperation(**payload)


def test_zero_processed_records_rates() -> None:
    payload = _base_payload()
    payload.update(
        {"processed_records": 0, "successful_records": 0, "failed_records": 0}
    )

    bulk = BulkOperation(**payload)

    assert bulk.failure_rate == 0.0
    assert bulk.success_rate == 10.0


def test_bulk_operation_in_progress_requires_start_time() -> None:
    payload = _base_payload()
    payload["started_at"] = None

    with pytest.raises(ValueError):
        BulkOperation(**payload)
