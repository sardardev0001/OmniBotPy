# OmniBotPy

**English** | [فارسی](README.fa.md)

> Async-first, extensible Python bot SDK for **Telegram**, **Bale**, and **Soroush Plus (experimental)**. Write handlers with **decorators** or **OOP classes**, using one dispatcher and platform adapters.

![CI](https://img.shields.io/badge/CI-local%20tests-blue) ![Python](https://img.shields.io/badge/python-3.11%2B-3776AB) ![License](https://img.shields.io/badge/license-MIT-green) ![Status](https://img.shields.io/badge/status-0.2.0%20beta-orange)

## Features

- Shared async dispatcher and normalized event/context abstraction.
- Decorator-based, class-based and controller-based authoring styles.
- Multiple bots with a shared command handler (`MultiBot`).
- Async HTTP transport, explicit API error types, an escape hatch for native methods.
- Long polling, application-level webhook dispatcher, middleware.
- Capability status flags so unsupported platform features aren't silently simulated.
- Binary multipart uploads for photos/documents, keyboard builders, in-memory FSM.
- Catalogued native-method snake_case shortcuts and `call_method` fallback.
- Conservative retry on read-only methods; token redaction on server API errors.
- Unit and mocked HTTP contract tests; no credentials required for local tests.

**Important:** This is a tested **beta SDK foundation**, not a 100%-complete implementation of every upstream API. Soroush Plus support is **experimental and based on third-party documentation**. No live platform integrations have been validated without user bot credentials. See [implementation status](docs/STATUS.md).

## Installation

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux / macOS: source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

The PyPI package name in `pyproject.toml` is a proposed name; it has not been published or verified as available.

## 1 — Decorator style

```python
import os
from omnibotpy import Bot, Platform

bot = Bot(Platform.TELEGRAM, os.environ["BOT_TOKEN"])

@bot.command("start")
async def start(ctx):
    await ctx.reply("Hello!")

@bot.message()
async def echo(ctx):
    if ctx.text:
        await ctx.reply(ctx.text)

bot.run()
```

## 2 — Class / OOP style

```python
import os
from omnibotpy import Bot, Platform, CommandHandler, MessageHandler

class Start(CommandHandler):
    command = "start"
    async def handle(self, ctx):
        await ctx.reply("Hello from OOP!")

class Echo(MessageHandler):
    async def handle(self, ctx):
        if ctx.text:
            await ctx.reply(ctx.text)

bot = Bot(Platform.BALE, os.environ["BOT_TOKEN"])
bot.add_handler(Start())
bot.add_handler(Echo())
bot.run()
```

## 3 — Controller style

```python
from omnibotpy import BotController

class MainController(BotController):
    async def on_start(self, ctx):
        await ctx.reply("Welcome")

    async def on_message(self, ctx):
        await ctx.reply("Received")

bot.add_controller(MainController())
```

## Conversation state and files

```python
from omnibotpy import InlineButton, InlineKeyboard

@bot.command("start")
async def start(ctx):
    await ctx.set_state("waiting_for_name")
    await ctx.reply("Your name?", reply_markup=InlineKeyboard([
        [InlineButton("Docs", url="https://core.telegram.org/bots/api")]
    ]))

@bot.message()
async def conversation(ctx):
    current = await ctx.get_state()
    if current.state == "waiting_for_name" and ctx.text:
        await ctx.clear_state()
        await ctx.reply(f"Nice to meet you, {ctx.text}!")

# Outside a handler:
# await bot.adapter.send_document_file(chat_id, "example.pdf")
```

MemoryStorage is per-process only; distributed production bots need a custom
`StateStorage` implementation. Files are loaded into memory before uploading.

## Native methods

For methods that have not been wrapped yet, call the platform-native method directly:

```python
result = await bot.adapter.call_method("getChat", chat_id=123)
```

Catalogued method shortcuts are also provided, for example
`await bot.adapter.get_user_profile_photos(user_id=123)`. These shortcuts accept
native `**kwargs`, not independently validated typed argument schemas. Check
`bot.adapter.available_methods()` for the platform's documented catalog.

This call returns the API `result` value; it does **not** auto-validate platform-specific inputs or return typed models.

## How to run

1. Create your bot on the chosen platform and obtain its **token**.
2. Set `BOT_TOKEN` as an environment variable (do **not** commit it).
3. Run `python examples/decorators.py` from an installed editable checkout.
4. Default is Telegram; set `BOT_PLATFORM=bale` or `BOT_PLATFORM=soroush` to switch (Soroush: experimental).
5. Polling and webhook delivery should not run simultaneously for the same bot.

Windows PowerShell:

```powershell
$env:BOT_PLATFORM = 'telegram'
$env:BOT_TOKEN = 'replace-with-real-token'
python examples/decorators.py
```

For webhook integrations use `omnibotpy.webhook.handle_webhook` inside your own HTTP framework. Authenticate inbound requests and limit JSON body size; Telegram secret-header checking is available.

## Project layout

```text
src/omnibotpy/    Async client, adapters, dispatch, models, HTTP transport
tests/            28 mocked HTTP/unit tests
examples/         Functional, OOP, controller, and MultiBot samples
docs/STATUS.md    Support matrix, risks and outstanding work
.github/workflows CI on Python 3.11–3.13
```

## Support and limitations

See [STATUS](docs/STATUS.md), [architecture](docs/ARCHITECTURE.md), and
[contribution guidelines](CONTRIBUTING.md). **No live tests were performed**.
The Telegram/Bale catalogs are curated, not exhaustive or frozen. Soroush
Plus is an experimental integration. Do not claim a verified production
connection without testing with a real credential.

## Roadmap

- Generated typed wrapper coverage for documented Telegram and Bale methods.
- Verified and documented official Soroush Plus contracts.
- Fully typed request/response schemas and stricter update validation.
- Redis/durable FSM, offset persistence, deduplication, rate limiting, more upload streaming.
- Real-world integration test suite for opt-in test bots.

## Source documentation

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Bale Bot API](https://docs.bale.ai/)
- [Plustik Soroush Plus Bot Client (third-party)](https://plustik.readthedocs.io/en/latest/api/plustik/client/index.html)

## Contributing and license

Issues and PRs are welcome. Run `python -m pytest -q` and `ruff check src tests` before proposing changes. Distributed under the [MIT license](LICENSE). See [security notes](SECURITY.md).
