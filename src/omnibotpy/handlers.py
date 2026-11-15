"""Decorator and OOP handlers compile to the same HandlerSpec."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Awaitable, Callable, Any
from .models import Event

Callback = Callable[[Any], Awaitable[None]]

@dataclass(slots=True)
class HandlerSpec:
    callback: Callback
    kind: str = "message"
    command: str | None = None
    text: str | None = None
    callback_prefix: str | None = None
    priority: int = 0

    def matches(self, event: Event) -> bool:
        if self.kind != event.kind:
            return False
        if self.command is not None:
            return event.command == self.command.lower()
        if self.text is not None:
            return event.text == self.text
        if self.callback_prefix is not None:
            return (event.callback_data or "").startswith(self.callback_prefix)
        return True

class BaseHandler:
    priority: int = 0
    async def handle(self, ctx: Any) -> None:
        raise NotImplementedError
    def as_spec(self) -> HandlerSpec:
        raise NotImplementedError

class CommandHandler(BaseHandler):
    command: str = ""
    def as_spec(self) -> HandlerSpec:
        if not self.command:
            raise ValueError("Set CommandHandler.command")
        return HandlerSpec(self.handle, command=self.command, priority=self.priority)

class MessageHandler(BaseHandler):
    text: str | None = None
    def as_spec(self) -> HandlerSpec:
        return HandlerSpec(self.handle, text=self.text, priority=self.priority)

class CallbackHandler(BaseHandler):
    prefix: str | None = None
    def as_spec(self) -> HandlerSpec:
        return HandlerSpec(self.handle, kind="callback", callback_prefix=self.prefix,
                           priority=self.priority)

class BotController:
    """Convention-based methods: on_start/on_help -> commands; on_message -> fallback."""
    priority: int = 0
    def specs(self) -> list[HandlerSpec]:
        result: list[HandlerSpec] = []
        for name in sorted(dir(self)):
            method = getattr(self, name)
            if name in ("on_message", "on_callback") and callable(method):
                result.append(HandlerSpec(method, kind="message" if name == "on_message" else "callback",
                                          priority=self.priority - 100))
            elif name.startswith("on_") and callable(method) and not name.startswith("on__"):
                result.append(HandlerSpec(method, command=name[3:].replace("_", ""), priority=self.priority))
        return result
