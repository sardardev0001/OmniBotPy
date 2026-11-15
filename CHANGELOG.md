# Changelog

## 0.2.0 — 2026-11-15
- Added multipart photo/document upload helpers and generic multipart API calls.
- Added portable inline/reply keyboard builders.
- Added FSM state operations with in-memory storage and a storage protocol.
- Added curated native-method catalog and snake_case shortcuts for Telegram/Bale.
- Added decorator-based error handler and conservative read-only HTTP retries.
- Redacted bot token in upstream API error descriptions.
- Added tests for these features, two examples, bilingual docs and architecture notes.
- No live validation performed; Soroush remains experimental.

## 0.1.0 — 2026-11-15
- Initial async adapters for Telegram, Bale, and experimental Soroush Plus.
- Unified Bot API and decorator/OOP/controller writing styles.
- Controller and MultiBot support, normalized events, polling, webhook dispatcher.
