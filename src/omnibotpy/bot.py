"""Primary user-facing Bot and MultiBot APIs."""
from __future__ import annotations
import asyncio
from collections.abc import Callable
from typing import Any
import httpx
from .adapters import ADAPTERS, BaseAdapter, Platform
from .capabilities import Support, capability
from .handlers import BaseHandler, BotController, HandlerSpec
from .models import Event
from .runtime import Context, Dispatcher, Middleware, poll
from .fsm import StateStorage

class Bot:
    def __init__(self, platform: Platform | str, token: str, *,
                 base_url: str | None = None, client: httpx.AsyncClient | None = None,
                 storage: StateStorage | None = None):
        self.platform = Platform(platform)
        self.adapter = ADAPTERS[self.platform](token, base_url=base_url, client=client)
        self.dispatcher = Dispatcher(storage=storage)

    def supports(self, name: str) -> Support:
        return capability(self.platform.value, name)

    def command(self, command: str, *, priority: int = 0) -> Callable:
        def decorator(func: Callable) -> Callable:
            self.dispatcher.add_handler(HandlerSpec(func, command=command.lstrip("/"), priority=priority))
            return func
        return decorator

    def message(self, *, text: str | None = None, priority: int = 0) -> Callable:
        def decorator(func: Callable) -> Callable:
            self.dispatcher.add_handler(HandlerSpec(func, text=text, priority=priority))
            return func
        return decorator

    on_message = message

    def callback(self, prefix: str | None = None, *, priority: int = 0) -> Callable:
        def decorator(func: Callable) -> Callable:
            self.dispatcher.add_handler(HandlerSpec(func, kind="callback", callback_prefix=prefix,
                                                    priority=priority))
            return func
        return decorator

    on_callback = callback

    def add_handler(self, handler: BaseHandler) -> None:
        self.dispatcher.add_handler(handler.as_spec())

    def add_controller(self, controller: BotController) -> None:
        for spec in controller.specs():
            self.dispatcher.add_handler(spec)

    def add_middleware(self, middleware: Middleware) -> None:
        self.dispatcher.add_middleware(middleware)

    def on_error(self, func: Callable) -> Callable:
        """Register async error handler: async def handler(ctx, exc)."""
        self.dispatcher.error_handler = func
        return func

    async def dispatch_raw(self, update: dict[str, Any]) -> bool:
        return await self.dispatcher.dispatch(self.adapter.normalize(update), self.adapter)

    async def start_polling(self, stop: asyncio.Event | None = None) -> None:
        stop = stop or asyncio.Event()
        try:
            await poll(self.adapter, self.dispatcher, stop)
        finally:
            await self.adapter.close()

    async def close(self) -> None:
        await self.adapter.close()

    def run(self) -> None:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self.start_polling())
        else:
            raise RuntimeError("Use `await bot.start_polling()` inside an async event loop")

class MultiBot:
    def __init__(self):
        self.bots: list[Bot] = []
        self._specs: list[HandlerSpec] = []

    def add_bot(self, platform: Platform | str, token: str, **kwargs: Any) -> Bot:
        bot = Bot(platform, token, **kwargs)
        for spec in self._specs:
            bot.dispatcher.add_handler(spec)
        self.bots.append(bot)
        return bot

    def command(self, name: str) -> Callable:
        def decorator(func: Callable) -> Callable:
            spec = HandlerSpec(func, command=name.lstrip("/"))
            self._specs.append(spec)
            for bot in self.bots:
                bot.dispatcher.add_handler(spec)
            return func
        return decorator

    def message(self, *, text: str | None = None) -> Callable:
        def decorator(func: Callable) -> Callable:
            spec = HandlerSpec(func, text=text)
            self._specs.append(spec)
            for bot in self.bots:
                bot.dispatcher.add_handler(spec)
            return func
        return decorator

    async def start_polling(self) -> None:
        if not self.bots:
            raise ValueError("Add at least one bot")
        stop = asyncio.Event()
        await asyncio.gather(*(bot.start_polling(stop) for bot in self.bots))

    def run(self) -> None:
        asyncio.run(self.start_polling())
