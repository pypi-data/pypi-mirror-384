from __future__ import annotations

import sys
from typing import IO, Iterable, Optional

import orjson


class ConsoleLogHandler:
    def __init__(self, stream: Optional[IO[str]] = None) -> None:
        self._stream = stream or sys.stderr

    def write_batch(self, batch: Iterable[dict]) -> None:
        for item in batch:
            try:
                serialized = orjson.dumps(item).decode("utf-8")
                self._stream.write(serialized)
                self._stream.write("\n")
            except Exception:
                # Console handler deve ser à prova de falhas.
                continue
        try:
            self._stream.flush()
        except Exception:
            pass
