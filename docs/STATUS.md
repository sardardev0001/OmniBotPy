# Implementation status — OmniBotPy 0.2.0 (2026-11-15)

**A functional, locally tested SDK foundation — not a claim of full API feature parity.**

| Feature | Telegram | Bale | Soroush Plus |
|---|---|---|---|
| HTTPS transport and native `call_method` | tested with mocks | tested with mocks | experimental mock only |
| Handler decorators, OOP, controllers | tested | tested | dispatcher works on sample shapes only |
| Polling and normalized Telegram-like updates | mocked | mocked | assumed shape, unverified |
| Webhook API setup | implemented, mocked | implemented, mocked | explicitly blocked pending verification |
| Incoming webhook dispatch | generic helper + Telegram secret check | generic helper | authentication unverified |
| Multipart photo/document uploads | implemented + mocked | implemented + mocked | implementation only; unverified |
| Inline/reply keyboard builders | serialized + mocked | serialized + mocked | unverified |
| FSM | process memory only | process memory only | process memory only |
| Native method catalog | curated shortcuts + raw access | curated shortcuts + raw access | no verified catalog |
| Full typed API models/arguments | not complete | not complete | not available |
| Live API credentials/end-to-end checks | **not performed** | **not performed** | **not performed** |

Local tests validate runtime behavior and generated HTTP requests but **do not** verify the live upstream servers. At the time of writing, the current Telegram official Bot API is rapidly evolving. Unlisted new methods remain accessible via `call_method` but method support must be validated with upstream.

## Production constraints

- Updates are processed sequentially. The polling offset lives in process memory and may redeliver after restart.
- Telegram disallows simultaneous long polling and outgoing webhooks for one bot.
- Transport retries *read-only* methods only after transient transport failure. Send methods are not automatically retried to avoid duplicate messages. No automatic handling of upstream 429 responses and no distributed rate limiter.
- FSM MemoryStorage is process-local; for distributed workloads implement the `StateStorage` protocol using Redis or a database.
- Multipart file helpers buffer file bytes in memory. Do not pass untrusted arbitrary file paths.
- Incoming webhook receivers must enforce TLS, authenticate requests, limit body size and ensure durable deduplication as needed.
- Webhook secret-header helper currently implements Telegram's header scheme only.
- `available_methods()` is a curated documentation catalog, NOT a supported-method guarantee. Typed per-method argument schemas, richer media/objects, payment workflows and all edge-case events remain incomplete.
- Soroush Plus endpoint and Telegram-like semantics are based on **third-party Plustik documentation**. Real support is not proven. Avoid using it for sensitive/production workloads until an official contract and actual bot-token tests are available.

## Primary sources

- https://core.telegram.org/bots/api
- https://core.telegram.org/bots/api-changelog
- https://docs.bale.ai/
- https://plustik.readthedocs.io/en/latest/api/plustik/client/index.html (third party)
