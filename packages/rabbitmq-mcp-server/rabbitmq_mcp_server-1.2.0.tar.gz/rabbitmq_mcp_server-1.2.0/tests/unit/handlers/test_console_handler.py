import io
import json
from contextlib import redirect_stderr

import pytest

from src.logging.handlers.console import ConsoleLogHandler


@pytest.fixture
def handler_and_buffer():
    buffer = io.StringIO()
    handler = ConsoleLogHandler(stream=buffer)
    return handler, buffer


def _read_output(buffer: io.StringIO):
    buffer.seek(0)
    return [json.loads(line) for line in buffer.read().splitlines() if line]


def test_console_handler_writes_to_stderr(handler_and_buffer):
    handler, buffer = handler_and_buffer

    handler.write_batch([{ "event": "test" }])

    output = buffer.getvalue().strip()
    assert output


def test_console_handler_writes_json_format(handler_and_buffer):
    handler, buffer = handler_and_buffer

    handler.write_batch([
        {"event": "first"},
        {"event": "second", "value": 2}
    ])

    records = _read_output(buffer)
    assert records == [
        {"event": "first"},
        {"event": "second", "value": 2},
    ]


def test_console_handler_never_raises_exception():
    handler = ConsoleLogHandler()

    buffer = io.StringIO()
    with redirect_stderr(buffer):
        handler.write_batch([{"event": "test"}])

    with redirect_stderr(io.StringIO()):
        handler.write_batch([{"event": "test"}])
