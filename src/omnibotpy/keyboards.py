"""Portable keyboard builders for Telegram-like APIs."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class InlineButton:
    text: str
    callback_data: str | None = None
    url: str | None = None

    def __post_init__(self) -> None:
        if (self.callback_data is None) == (self.url is None):
            raise ValueError("Exactly one of callback_data or url is required")
        if self.callback_data is not None and len(self.callback_data.encode("utf-8")) > 64:
            raise ValueError("callback_data exceeds 64 UTF-8 bytes")

    def to_dict(self) -> dict[str, str]:
        result = {"text": self.text}
        if self.callback_data is not None:
            result["callback_data"] = self.callback_data
        else:
            result["url"] = self.url  # type: ignore[assignment]
        return result

@dataclass(slots=True)
class InlineKeyboard:
    rows: list[list[InlineButton]]

    def to_dict(self) -> dict[str, Any]:
        return {"inline_keyboard": [[button.to_dict() for button in row] for row in self.rows]}

@dataclass(slots=True)
class ReplyKeyboard:
    rows: list[list[str]]
    resize_keyboard: bool = True
    one_time_keyboard: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"keyboard": [[{"text": text} for text in row] for row in self.rows],
                "resize_keyboard": self.resize_keyboard,
                "one_time_keyboard": self.one_time_keyboard}
