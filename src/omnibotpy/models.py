"""Portable event models. Original platform payload is preserved in `raw`."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(slots=True, frozen=True)
class User:
    id: int | str
    first_name: str | None = None
    username: str | None = None

@dataclass(slots=True, frozen=True)
class Chat:
    id: int | str
    type: str | None = None
    title: str | None = None

@dataclass(slots=True, frozen=True)
class Event:
    platform: str
    kind: str
    update_id: int | str | None
    chat: Chat | None = None
    user: User | None = None
    text: str | None = None
    message_id: int | str | None = None
    callback_id: str | None = None
    callback_data: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def command(self) -> str | None:
        if not self.text or not self.text.startswith("/"):
            return None
        first = self.text.split(maxsplit=1)[0][1:].split("@", 1)[0]
        return first.lower() or None

    @property
    def args(self) -> str:
        if self.command is None or self.text is None:
            return ""
        return self.text.partition(" ")[2]


def normalize_event(payload: dict[str, Any], platform: str) -> Event:
    """Normalize Telegram-like updates; unknown shapes remain accessible through raw."""
    message = payload.get("message") or payload.get("edited_message") or payload.get("channel_post")
    callback = payload.get("callback_query")
    kind = "callback" if callback else "message" if message else "unknown"
    if callback:
        message = callback.get("message") or {}
    message = message or {}
    chat_data = message.get("chat") or {}
    from_data = (callback or message).get("from") or {}
    chat = Chat(chat_data["id"], chat_data.get("type"), chat_data.get("title")) if "id" in chat_data else None
    user = User(from_data["id"], from_data.get("first_name"), from_data.get("username")) if "id" in from_data else None
    return Event(
        platform=platform, kind=kind, update_id=payload.get("update_id"),
        chat=chat, user=user, text=message.get("text"), message_id=message.get("message_id"),
        callback_id=callback.get("id") if callback else None,
        callback_data=callback.get("data") if callback else None, raw=payload,
    )
