# Architecture

The package uses a small modular architecture:

```text
User code (decorators / Handler / Controller)
             |
         HandlerSpec
             |
           Bot -> Dispatcher -> Context -> FSM / Middleware
                                         |
                                 Platform adapter
                                         |
                                 HTTPTransport (httpx)
                                         |
                   Telegram / Bale / Soroush Plus (experimental)
```

`HandlerSpec.matches()` filters events; the first match wins, ordered by priority and specificity. Both functional and OOP handlers compile into the same runtime path.

`BaseAdapter` exposes common convenient methods, a curated set of native method shortcuts and `call_method()` for the platform's documented native API. The transport unwraps the `{ok, result}` response, validates the method component, avoids leaking tokens in transport errors and supports multipart uploads.

`Context` offers reply, callback answer, and state operations. The default storage is memory-only. Webhook adapters are designed to be used behind a real ASGI server rather than embedding one in the SDK.

## Extension

- Create a `BaseAdapter` subclass and extend the `ADAPTERS` registry for a new platform.
- Implement normalization into `Event` for any non-Telegram-compatible updates.
- Add or update platform capability evidence independently of the method catalog.
- Add contract tests against captured, sanitized upstream traffic (without tokens).

## Boundaries

This SDK is not a visual bot builder, payment processor, a persistent job queue, or a server. For distributed operation, host the webhook HTTP layer in an ASGI framework and provide durable state/offset stores.
