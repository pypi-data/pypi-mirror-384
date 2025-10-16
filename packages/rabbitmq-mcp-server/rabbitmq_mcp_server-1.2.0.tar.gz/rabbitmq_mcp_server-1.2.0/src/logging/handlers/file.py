from __future__ import annotations

import errno
import os
import sys
from pathlib import Path
from typing import Callable, Iterable, Optional

import orjson

from ..rotation import RotatingLogHandler
from ...models.log_config import LogConfig


class FileLogHandler:
    def __init__(
        self,
        path: Path,
        *,
        fallback: Optional[Callable[[Iterable[dict]], None]] = None,
        config: Optional[LogConfig] = None,
    ) -> None:
        self._path = Path(path)
        self._fallback = fallback
        self._permissions_attempted = False
        self._is_windows = os.name == "nt"
        self._config = config
        
        # Initialize rotation handler if rotation is enabled
        self._rotation_handler = None
        if config and (config.rotation_max_bytes > 0 or config.rotation_when):
            self._rotation_handler = RotatingLogHandler(config)

    def write_batch(self, batch: Iterable[dict]) -> None:
        entries = list(batch)
        
        # Use rotation handler if configured
        if self._rotation_handler:
            try:
                for item in entries:
                    self._rotation_handler.write_log(item)
            except Exception as exc:
                self._handle_fallback(entries, exc)
            return
        
        # Original non-rotating logic
        try:
            self._ensure_parent_directory()
            file_existed = self._path.exists()
            with self._path.open("ab") as file:
                if not file_existed:
                    self._apply_secure_permissions()
                for item in entries:
                    file.write(orjson.dumps(item) + b"\n")
        except (PermissionError, BlockingIOError) as exc:
            self._handle_fallback(entries, exc)
        except OSError as exc:
            if exc.errno in (errno.ENOSPC, errno.EROFS):
                self._handle_fallback(entries, exc)
            else:
                raise

    def _handle_fallback(self, batch: Iterable[dict], exc: Exception) -> None:
        if self._fallback:
            self._fallback(list(batch))
        else:
            raise exc

    def _ensure_parent_directory(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _apply_secure_permissions(self) -> None:
        if self._permissions_attempted:
            return
        self._permissions_attempted = True
        try:
            os.chmod(self._path, 0o600)
        except NotImplementedError:
            return
        except OSError as exc:
            if self._is_windows:
                return
            self._log_permission_warning(exc)
        else:
            self._log_permission_debug()

    def _log_permission_debug(self) -> None:
        sys.stderr.write(
            f"DEBUG: Secure permissions (600) set successfully on log file {self._path}\n"
        )

    def _log_permission_warning(self, exc: OSError) -> None:
        sys.stderr.write(
            "WARNING: Failed to set secure permissions (600) on log file "
            f"{self._path}: {exc}. Using OS default permissions. This may expose sensitive log data on multi-user systems.\n"
        )
