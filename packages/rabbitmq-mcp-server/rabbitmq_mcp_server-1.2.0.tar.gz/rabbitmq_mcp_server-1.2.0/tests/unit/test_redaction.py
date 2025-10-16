from copy import deepcopy
from typing import Iterable

import pytest

from src.logging.redaction import apply_redaction, apply_redaction_to_event


@pytest.fixture
def base_event():
    return {
        "message": "Connecting to broker",
        "connection": "amqp://user:supersecret@localhost",
        "password": "plainpassword",
        "api_key": "abc123",
        "token": "xyz987",
        "authorization": "Bearer token-value",
    }


def test_apply_redaction_does_not_mutate_original(base_event):
    original = deepcopy(base_event)
    apply_redaction(base_event)
    assert base_event == original


def test_redact_password_in_connection_string(base_event):
    redacted = apply_redaction(base_event)
    assert redacted["connection"] == "amqp://user:[REDACTED]@localhost"


def test_redact_password_field(base_event):
    redacted = apply_redaction(base_event)
    assert redacted["password"] == "[REDACTED]"


def test_redact_api_key(base_event):
    redacted = apply_redaction(base_event)
    assert redacted["api_key"] == "[REDACTED]"


def test_redact_token(base_event):
    redacted = apply_redaction(base_event)
    assert redacted["token"] == "[REDACTED]"


def test_redact_bearer_token(base_event):
    redacted = apply_redaction(base_event)
    assert redacted["authorization"] == "Bearer [REDACTED]"


def test_redact_amqp_password_preserves_username():
    event = {"connection": "amqp://important-user:secret-pass@localhost"}
    redacted = apply_redaction(event)
    assert redacted["connection"].startswith("amqp://important-user:")
    assert redacted["connection"] == "amqp://important-user:[REDACTED]@localhost"


def test_redaction_works_in_nested_context():
    event = {
        "outer": {
            "token": "nested-secret",
            "details": ["no-secret", "Bearer abc"],
            "connection": "amqp://user:nestedpass@host",
        }
    }

    redacted = apply_redaction(event)

    assert redacted["outer"]["token"] == "[REDACTED]"
    assert redacted["outer"]["details"][1] == "Bearer [REDACTED]"
    assert redacted["outer"]["connection"] == "amqp://user:[REDACTED]@host"


def test_redact_keys_containing_token_suffix():
    event = {
        "secondary_token": "should-hide",
        "refresh_token": "also-hidden",
    }

    redacted = apply_redaction_to_event(event)

    assert redacted["secondary_token"] == "[REDACTED]"
    assert redacted["refresh_token"] == "[REDACTED]"

def test_no_credentials_in_log_output(base_event):
    redacted = apply_redaction(base_event)

    sensitive_patterns: Iterable[str] = ["plainpassword", "abc123", "xyz987", "token-value"]
    serialized = " ".join(str(value) for value in redacted.values())
    for pattern in sensitive_patterns:
        assert pattern not in serialized


def test_apply_redaction_keeps_unrelated_fields():
    event = {"message": "Everything is fine", "count": 42}
    redacted = apply_redaction(event)
    assert redacted == event
