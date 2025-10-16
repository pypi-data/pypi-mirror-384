from __future__ import annotations

import pytest

from src.models.log_entry import LogEntry, LogCategory, LogLevel


def _base_payload() -> dict:
    return {
        "schema_version": "1.0.0",
        "timestamp": "2025-10-15T12:00:00Z",
        "level": LogLevel.INFO.value,
        "category": LogCategory.OPERATION.value,
        "correlation_id": "cid-123",
        "message": "operation completed",
    }


def test_old_parser_reads_logs_with_minor_version_bump() -> None:
    payload = _base_payload()
    payload["schema_version"] = "1.1.0"
    payload["context"] = {"new_optional_field": "extra info"}

    entry = LogEntry.model_validate(payload)

    assert entry.schema_version == "1.1.0"
    assert entry.context == {"new_optional_field": "extra info"}


def test_old_parser_reads_logs_with_patch_version_bump() -> None:
    payload = _base_payload()
    payload["schema_version"] = "1.0.1"

    entry = LogEntry.model_validate(payload)

    assert entry.schema_version == "1.0.1"


def test_parser_warns_on_major_version_mismatch() -> None:
    payload = _base_payload()
    payload["schema_version"] = "2.0.0"

    with pytest.raises(ValueError, match="unsupported schema_version major component"):
        LogEntry.model_validate(payload)


@pytest.mark.parametrize("invalid_version", ["1.0", "1", "v1.0.0", "1.0.0.0"])
def test_schema_version_increment_follows_semver_rules(invalid_version: str) -> None:
    payload = _base_payload()
    payload["schema_version"] = invalid_version

    with pytest.raises(ValueError):
        LogEntry.model_validate(payload)
