"""Componentes de retry/backoff usados no gerenciamento de conexão."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RetryStats(BaseModel):
    attempts: int = Field(ge=0)
    current_delay: float = Field(gt=0)
    max_delay: float = Field(gt=0)


class RetryPolicy(BaseModel):
    """Política de retry com backoff exponencial."""

    initial_delay: float = Field(default=1.0, gt=0, le=60)
    backoff_factor: float = Field(default=2.0, gt=1.0, le=10.0)
    max_delay: float = Field(default=60.0, gt=0, le=3600)
    current_delay: float = Field(default=1.0, gt=0)
    attempts: int = Field(default=0, ge=0)

    def next_delay(self) -> float:
        delay = min(self.current_delay, self.max_delay)
        self.current_delay = min(self.current_delay * self.backoff_factor, self.max_delay)
        self.attempts += 1
        return delay

    def reset(self) -> None:
        self.current_delay = self.initial_delay
        self.attempts = 0

    def get_stats(self) -> RetryStats:
        return RetryStats(
            attempts=self.attempts,
            current_delay=self.current_delay,
            max_delay=self.max_delay,
        )
