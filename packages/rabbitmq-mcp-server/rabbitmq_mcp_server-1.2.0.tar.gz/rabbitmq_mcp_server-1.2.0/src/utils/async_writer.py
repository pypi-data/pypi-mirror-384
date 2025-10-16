from __future__ import annotations

import asyncio
import contextlib

from collections.abc import Awaitable, Callable
from typing import Any, Iterable, Optional

DEFAULT_QUEUE_SIZE = 10_000
DEFAULT_FLUSH_INTERVAL = 0.1
DEFAULT_BATCH_SIZE = 100


class AsyncLogWriter:
    def __init__(
        self,
        *,
        max_queue_size: int = DEFAULT_QUEUE_SIZE,
        flush_interval: float = DEFAULT_FLUSH_INTERVAL,
        batch_size: int = DEFAULT_BATCH_SIZE,
        write_batch: Optional[Callable[[Iterable[dict[str, Any]]], Awaitable[None]]] = None,
    ) -> None:
        if max_queue_size < 1:
            raise ValueError("max_queue_size must be >= 1")
        if flush_interval <= 0:
            raise ValueError("flush_interval must be > 0")
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")

        if write_batch is None:
            async def raise_if_not_provided(_: Iterable[dict[str, Any]]) -> None:
                raise RuntimeError("write_batch callable must be provided")

            write_batch = raise_if_not_provided

        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=max_queue_size)
        self._flush_interval = flush_interval
        self._batch_size = batch_size
        self._write_batch = write_batch

        self._worker_task: Optional[asyncio.Task[None]] = None
        self._shutdown_event = asyncio.Event()
        self._permit = asyncio.Semaphore(max_queue_size)

        self._flush_requested = asyncio.Event()

        self._lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._lock:
            if self._worker_task and not self._worker_task.done():
                raise RuntimeError("AsyncLogWriter already started")

            self._shutdown_event.clear()
            self._flush_requested.clear()
            self._worker_task = asyncio.create_task(self._run())

    async def stop(self, *, timeout: float = 30.0) -> None:
        """
        Stop the async log writer and flush all pending logs.
        
        Args:
            timeout: Maximum time to wait for flush completion (seconds).
                     Defaults to 30 seconds to prevent indefinite hang.
        
        Raises:
            asyncio.TimeoutError: If flush doesn't complete within timeout.
        """
        async with self._lock:
            if not self._worker_task:
                return

            self._shutdown_event.set()
            self._flush_requested.set()
            
            try:
                # Wait for flush with timeout
                await asyncio.wait_for(self.flush(), timeout=timeout)
                await asyncio.wait_for(self._worker_task, timeout=max(1.0, timeout - 1.0))
            except asyncio.TimeoutError:
                # Force cancel if timeout exceeded
                self._worker_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._worker_task
            
            self._worker_task = None
    
    async def shutdown(self, *, timeout: float = 30.0) -> None:
        """
        Gracefully shutdown the writer, flushing all buffered logs.
        
        This is an alias for stop() for clearer semantics.
        
        Args:
            timeout: Maximum time to wait for flush completion (seconds).
        """
        await self.stop(timeout=timeout)

    async def write_log(self, entry: dict[str, Any]) -> None:
        await self._permit.acquire()
        await self._queue.put(entry)

    async def flush(self) -> None:
        self._flush_requested.set()
        await self._queue.join()

    async def _run(self) -> None:
        batch: list[dict[str, Any]] = []

        get_task: Optional[asyncio.Task[dict[str, Any]]] = None
        sleep_task: Optional[asyncio.Task[Any]] = None
        flush_task: Optional[asyncio.Task[Any]] = None

        def _ensure_get_task() -> None:
            nonlocal get_task
            if get_task is None or get_task.done():
                get_task = asyncio.create_task(self._queue.get())

        def _restart_sleep_task() -> None:
            nonlocal sleep_task
            if sleep_task is not None:
                sleep_task.cancel()
            sleep_task = asyncio.create_task(asyncio.sleep(self._flush_interval))

        def _ensure_flush_task() -> None:
            nonlocal flush_task
            if flush_task is None or flush_task.done():
                flush_task = asyncio.create_task(self._flush_requested.wait())

        _ensure_get_task()
        _restart_sleep_task()
        _ensure_flush_task()

        flush_pending = False

        try:
            while True:
                if self._shutdown_event.is_set() and self._queue.empty() and not batch:
                    break

                wait_tasks = {t for t in (get_task, sleep_task, flush_task) if t is not None}
                if not wait_tasks:
                    await asyncio.sleep(self._flush_interval)
                    continue

                done, _ = await asyncio.wait(wait_tasks, return_when=asyncio.FIRST_COMPLETED)

                if get_task in done and get_task is not None:
                    item = get_task.result()
                    batch.append(item)
                    if len(batch) == 1:
                        _restart_sleep_task()
                    if len(batch) >= self._batch_size:
                        _restart_sleep_task()
                        await self._emit_batch(batch)
                        if flush_pending and self._queue.empty():
                            flush_pending = False
                    if flush_pending and self._queue.empty():
                        if batch:
                            _restart_sleep_task()
                            await self._emit_batch(batch)
                        flush_pending = False
                    _ensure_get_task()

                if sleep_task in done and sleep_task is not None:
                    _restart_sleep_task()
                    if batch:
                        await self._emit_batch(batch)
                        if flush_pending and self._queue.empty():
                            flush_pending = False

                if flush_task in done and flush_task is not None:
                    self._flush_requested.clear()
                    _ensure_flush_task()
                    flush_pending = True
                    if self._queue.empty():
                        if batch:
                            _restart_sleep_task()
                            await self._emit_batch(batch)
                        flush_pending = False
        finally:
            for task in (get_task, sleep_task, flush_task):
                if task is None:
                    continue
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

            if batch:
                await self._emit_batch(batch)

    async def _emit_batch(self, batch: list[dict[str, Any]]) -> None:
        if not batch:
            return

        to_write = list(batch)
        try:
            await self._write_batch(to_write)
        finally:
            for _ in to_write:
                self._queue.task_done()
                self._permit.release()
        batch.clear()
