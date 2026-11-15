"""Shared dispatch machinery for class-based and functional bots."""
from __future__ import annotations
import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from .adapters import BaseAdapter
from .handlers import HandlerSpec
from .models import Event
from .errors import HandlerError
from .fsm import MemoryStorage, StateStorage, StateRecord

logger = logging.getLogger(__name__)
Middleware = Callable[["Context", Callable[[], Awaitable[None]]], Awaitable[None]]

@dataclass(slots=True)
class Context:
    adapter: BaseAdapter
    event: Event
    storage: StateStorage | None = None

    @property
    def platform(self) -> str:
        return self.event.platform

    @property
    def text(self) -> str | None:
        return self.event.text

    @property
    def args(self) -> str:
        return self.event.args

    @property
    def chat_id(self) -> int | str | None:
        return self.event.chat.id if self.event.chat else None

    @property
    def state_key(self) -> str:
        if self.chat_id is None:
            raise HandlerError('State requires an event chat')
        user_id = self.event.user.id if self.event.user else 'anonymous'
        return f'{self.platform}:{self.chat_id}:{user_id}'

    async def get_state(self) -> StateRecord:
        if self.storage is None:
            raise HandlerError('No state storage configured')
        return await self.storage.get(self.state_key)

    async def set_state(self, state: str | None) -> None:
        if self.storage is None:
            raise HandlerError('No state storage configured')
        await self.storage.set_state(self.state_key, state)

    async def update_data(self, **data: Any) -> None:
        if self.storage is None:
            raise HandlerError('No state storage configured')
        await self.storage.update_data(self.state_key, **data)

    async def clear_state(self) -> None:
        if self.storage is None:
            raise HandlerError('No state storage configured')
        await self.storage.clear(self.state_key)

    async def reply(self, text: str, **kwargs: Any) -> Any:
        if self.chat_id is None:
            raise HandlerError("Cannot reply: event has no chat")
        return await self.adapter.send_message(self.chat_id, text, **kwargs)

    async def answer_callback(self, text: str | None = None) -> Any:
        if not self.event.callback_id:
            raise HandlerError("Cannot answer callback: missing callback ID")
        return await self.adapter.answer_callback_query(self.event.callback_id, text=text)

class Dispatcher:
    def __init__(self, storage: StateStorage | None = None):
        self.storage = storage or MemoryStorage()
        self.handlers: list[HandlerSpec] = []
        self.middleware: list[Middleware] = []
        self.error_handler: Callable[[Context, Exception], Awaitable[None]] | None = None

    def add_handler(self, spec: HandlerSpec) -> None:
        self.handlers.append(spec)
        self.handlers.sort(key=lambda h: (h.priority, h.command is not None, h.text is not None,
                                          h.callback_prefix is not None), reverse=True)

    def add_middleware(self, middleware: Middleware) -> None:
        self.middleware.append(middleware)

    async def dispatch(self, event: Event, adapter: BaseAdapter) -> bool:
        ctx = Context(adapter, event, self.storage)
        for spec in self.handlers:
            if not spec.matches(event):
                continue
            async def invoke() -> None:
                await spec.callback(ctx)
            run = invoke
            for mw in reversed(self.middleware):
                previous = run
                async def wrap(mw: Middleware = mw, previous: Callable[[], Awaitable[None]] = previous) -> None:
                    await mw(ctx, previous)
                run = wrap
            try:
                await run()
            except Exception as exc:
                if self.error_handler:
                    await self.error_handler(ctx, exc)
                else:
                    logger.exception("Bot handler failed (platform=%s)", event.platform)
                    raise
            return True  # First matching handler wins.
        return False

async def poll(adapter: BaseAdapter, dispatcher: Dispatcher, stop: asyncio.Event,
               *, timeout: int = 25, retry_delay: float = 2) -> None:
    offset: int | None = None
    while not stop.is_set():
        try:
            updates = await adapter.get_updates(offset=offset, timeout=timeout)
            for raw in updates:
                update_id = raw.get("update_id")
                # Advance the offset only after successful processing, allowing retry on failure.
                await dispatcher.dispatch(adapter.normalize(raw), adapter)
                if isinstance(update_id, int):
                    offset = update_id + 1
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Polling failed for %s; retrying", adapter.platform.value)
            try:
                await asyncio.wait_for(stop.wait(), timeout=retry_delay)
            except TimeoutError:
                pass
