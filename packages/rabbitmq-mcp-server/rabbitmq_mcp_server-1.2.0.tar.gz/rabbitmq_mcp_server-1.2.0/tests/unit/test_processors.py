import structlog

from src.logging import processors


def test_add_correlation_id_injects_current_value(monkeypatch):
    monkeypatch.setattr(processors, "get_correlation_id", lambda: "abc123")

    result = processors.add_correlation_id(None, "info", {})

    assert result["correlation_id"] == "abc123"


def test_add_correlation_id_skips_when_missing(monkeypatch):
    monkeypatch.setattr(processors, "get_correlation_id", lambda: None)

    result = processors.add_correlation_id(None, "info", {"existing": 1})

    assert "correlation_id" not in result
    assert result["existing"] == 1


def test_redaction_processor_applies_redaction(monkeypatch):
    def fake_apply(event):
        event = dict(event)
        event["password"] = "[REDACTED]"
        return event

    monkeypatch.setattr(processors, "apply_redaction_to_event", fake_apply)

    result = processors.redact_sensitive_data(
        None, "info", {"password": "secret", "other": "value"}
    )

    assert result["password"] == "[REDACTED]"
    assert result["other"] == "value"
