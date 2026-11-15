"""Platform API adapters. Raw calls expose documented platform-specific methods."""
from __future__ import annotations
from enum import StrEnum
from pathlib import Path
from typing import Any
import httpx
from .models import Event, normalize_event
from .method_catalog import TELEGRAM, BALE
from .transport import HTTPTransport
from .capabilities import capability, Support
from .errors import UnsupportedCapability

class Platform(StrEnum):
    TELEGRAM = "telegram"
    BALE = "bale"
    SOROUSH = "soroush"

URLS = {
    Platform.TELEGRAM: "https://api.telegram.org/bot",
    Platform.BALE: "https://tapi.bale.ai/bot",
    Platform.SOROUSH: "https://api.splus.ir/bot",
}

class BaseAdapter:
    def __init__(self, platform: Platform | str, token: str, *,
                 base_url: str | None = None, client: httpx.AsyncClient | None = None):
        self.platform = Platform(platform)
        self.transport = HTTPTransport(token, base_url or URLS[self.platform], client=client)

    async def __aenter__(self) -> BaseAdapter:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def close(self) -> None:
        await self.transport.close()

    async def call_method(self, method: str, **params: Any) -> Any:
        """Call a native platform method. Validation is delegated to platform API."""
        return await self.transport.request(method, params)

    async def call_method_upload(self, method: str, *,
                                 files: dict[str, tuple[str, bytes, str]],
                                 **params: Any) -> Any:
        """Call any native method using multipart files (filename, bytes, MIME)."""
        return await self.transport.request(method, params, files=files)

    def available_methods(self) -> frozenset[str]:
        if self.platform == Platform.TELEGRAM:
            return TELEGRAM
        if self.platform == Platform.BALE:
            return BALE
        return frozenset()  # Upstream Soroush method set not yet confirmed.

    async def get_me(self) -> dict[str, Any]:
        return await self.call_method("getMe")

    async def get_updates(self, *, offset: int | None = None, limit: int = 100,
                          timeout: int = 25, allowed_updates: list[str] | None = None) -> list[dict[str, Any]]:
        return await self.call_method("getUpdates", offset=offset, limit=limit,
                                      timeout=timeout, allowed_updates=allowed_updates)

    async def send_message(self, chat_id: int | str, text: str, **kwargs: Any) -> dict[str, Any]:
        return await self.call_method("sendMessage", chat_id=chat_id, text=text, **kwargs)

    async def send_photo(self, chat_id: int | str, photo: str, **kwargs: Any) -> dict[str, Any]:
        return await self.call_method("sendPhoto", chat_id=chat_id, photo=photo, **kwargs)

    async def send_document(self, chat_id: int | str, document: str, **kwargs: Any) -> dict[str, Any]:
        return await self.call_method("sendDocument", chat_id=chat_id, document=document, **kwargs)

    async def send_video(self, chat_id: int | str, video: str, **kwargs: Any) -> dict[str, Any]:
        return await self.call_method("sendVideo", chat_id=chat_id, video=video, **kwargs)

    async def send_audio(self, chat_id: int | str, audio: str, **kwargs: Any) -> dict[str, Any]:
        return await self.call_method("sendAudio", chat_id=chat_id, audio=audio, **kwargs)

    async def send_voice(self, chat_id: int | str, voice: str, **kwargs: Any) -> dict[str, Any]:
        return await self.call_method("sendVoice", chat_id=chat_id, voice=voice, **kwargs)

    async def answer_callback_query(self, callback_query_id: str, **kwargs: Any) -> Any:
        if capability(self.platform.value, "callback") is not Support.SUPPORTED:
            raise UnsupportedCapability(f"Callback replies not verified for {self.platform.value}")
        return await self.call_method("answerCallbackQuery", callback_query_id=callback_query_id, **kwargs)

    async def set_webhook(self, url: str, **kwargs: Any) -> Any:
        if capability(self.platform.value, "webhook") is not Support.SUPPORTED:
            raise UnsupportedCapability(f"Webhook setup not verified for {self.platform.value}")
        if not url.startswith("https://"):
            raise ValueError("Webhook URL must be HTTPS")
        return await self.call_method("setWebhook", url=url, **kwargs)

    async def delete_webhook(self, **kwargs: Any) -> Any:
        if capability(self.platform.value, "webhook") is not Support.SUPPORTED:
            raise UnsupportedCapability(f"Webhook removal not verified for {self.platform.value}")
        return await self.call_method("deleteWebhook", **kwargs)

    def normalize(self, update: dict[str, Any]) -> Event:
        return normalize_event(update, self.platform.value)

class TelegramAdapter(BaseAdapter):
    def __init__(self, token: str, **kwargs: Any):
        super().__init__(Platform.TELEGRAM, token, **kwargs)

class BaleAdapter(BaseAdapter):
    def __init__(self, token: str, **kwargs: Any):
        super().__init__(Platform.BALE, token, **kwargs)

class SoroushAdapter(BaseAdapter):
    """Experimental: API inferred from third-party Plustik docs; validate with live credentials."""
    def __init__(self, token: str, **kwargs: Any):
        super().__init__(Platform.SOROUSH, token, **kwargs)

ADAPTERS = {
    Platform.TELEGRAM: TelegramAdapter,
    Platform.BALE: BaleAdapter,
    Platform.SOROUSH: SoroushAdapter,
}

# A deliberately explicit set of convenience methods backed by native API names.
# More methods remain accessible via call_method(), without pretending parity.
_METHODS = {
    'forward_message': 'forwardMessage', 'copy_message': 'copyMessage',
    'send_animation': 'sendAnimation', 'send_location': 'sendLocation',
    'send_contact': 'sendContact', 'send_chat_action': 'sendChatAction',
    'get_file': 'getFile', 'get_chat': 'getChat',
    'get_chat_member': 'getChatMember', 'get_chat_administrators': 'getChatAdministrators',
    'get_webhook_info': 'getWebhookInfo', 'edit_message_text': 'editMessageText',
    'edit_message_caption': 'editMessageCaption',
    'edit_message_reply_markup': 'editMessageReplyMarkup',
    'delete_message': 'deleteMessage', 'pin_chat_message': 'pinChatMessage',
    'unpin_chat_message': 'unpinChatMessage', 'leave_chat': 'leaveChat',
    'set_my_commands': 'setMyCommands', 'get_my_commands': 'getMyCommands',
    'delete_my_commands': 'deleteMyCommands', 'send_invoice': 'sendInvoice',
    'answer_pre_checkout_query': 'answerPreCheckoutQuery',
    'create_invoice_link': 'createInvoiceLink', 'send_media_group': 'sendMediaGroup',
}

def _method_factory(native_name: str):
    async def method(self: BaseAdapter, **params: Any) -> Any:
        return await self.call_method(native_name, **params)
    method.__doc__ = f"Call the native {native_name} API method; pass upstream parameter names."
    return method

for _name, _native in _METHODS.items():
    setattr(BaseAdapter, _name, _method_factory(_native))

async def _upload_file(self: BaseAdapter, method: str, field: str, chat_id: int | str,
                       file: str | Path | bytes, *, filename: str | None = None, **params: Any) -> Any:
    from mimetypes import guess_type
    if isinstance(file, (str, Path)):
        path = Path(file)
        filename = filename or path.name
        content = path.read_bytes()
    else:
        content = file
        filename = filename or 'upload.bin'
    if not isinstance(content, bytes):
        raise TypeError('file must be bytes or local file path')
    if '/' in filename or '\\' in filename:
        raise ValueError('filename must not contain path separators')
    content_type = guess_type(filename)[0] or 'application/octet-stream'
    return await self.transport.request(method, {'chat_id': chat_id, **params},
                                        files={field: (filename, content, content_type)})

async def _send_document_file(self: BaseAdapter, chat_id: int | str,
                              file: str | Path | bytes, **params: Any) -> Any:
    return await _upload_file(self, 'sendDocument', 'document', chat_id, file, **params)

async def _send_photo_file(self: BaseAdapter, chat_id: int | str,
                           file: str | Path | bytes, **params: Any) -> Any:
    return await _upload_file(self, 'sendPhoto', 'photo', chat_id, file, **params)

BaseAdapter.upload_file = _upload_file
BaseAdapter.send_document_file = _send_document_file
BaseAdapter.send_photo_file = _send_photo_file

# Expose a discoverable snake_case shortcut for every *catalogued* Telegram/Bale
# method. No platform compatibility is implied: check available_methods() first.
import re as _re

def _snake(name: str) -> str:
    return _re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

for _native_name in TELEGRAM | BALE:
    _shortcut = _snake(_native_name)
    if not hasattr(BaseAdapter, _shortcut):
        setattr(BaseAdapter, _shortcut, _method_factory(_native_name))

# Some upstream names differ from the snake_case convention (e.g. unPinChatMessage).
# Prefer explicit documented native names through call_method when in doubt.
