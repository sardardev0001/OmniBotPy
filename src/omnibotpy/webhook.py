"""Framework-agnostic webhook delivery with optional Telegram secret verification."""
from __future__ import annotations
import hmac
from typing import Mapping
from .bot import Bot

async def handle_webhook(bot: Bot, update: dict, headers: Mapping[str, str] | None = None,
                         *, secret_token: str | None = None) -> bool:
    """Invoke after your HTTP framework has parsed JSON (and applied body size limits).

    Telegram secret token is supported; Bale/Soroush validation must be configured
    according to their individual documented mechanisms.
    """
    if secret_token is not None:
        if bot.platform.value != "telegram":
            raise ValueError("Telegram secret-token scheme is only validated for Telegram")
        received = next((v for k, v in (headers or {}).items()
                         if k.lower() == "x-telegram-bot-api-secret-token"), "")
        if not hmac.compare_digest(received, secret_token):
            raise PermissionError("Invalid webhook secret")
    return await bot.dispatch_raw(update)
