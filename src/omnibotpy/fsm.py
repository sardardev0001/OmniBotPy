"""Minimal async finite-state storage; memory backend is process-local."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from typing import Any, Protocol

@dataclass(slots=True)
class StateRecord:
    state: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

class StateStorage(Protocol):
    async def get(self, key: str) -> StateRecord: ...
    async def set_state(self, key: str, state: str | None) -> None: ...
    async def update_data(self, key: str, **data: Any) -> None: ...
    async def clear(self, key: str) -> None: ...

class MemoryStorage:
    def __init__(self) -> None:
        self._records: dict[str, StateRecord] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> StateRecord:
        async with self._lock:
            record = self._records.get(key, StateRecord())
            return StateRecord(record.state, record.data.copy())

    async def set_state(self, key: str, state: str | None) -> None:
        async with self._lock:
            self._records.setdefault(key, StateRecord()).state = state

    async def update_data(self, key: str, **data: Any) -> None:
        async with self._lock:
            self._records.setdefault(key, StateRecord()).data.update(data)

    async def clear(self, key: str) -> None:
        async with self._lock:
            self._records.pop(key, None)
