"""Public error hierarchy; never expose credentials in error messages."""

class BotError(Exception):
    """Base class for SDK errors."""

class APIError(BotError):
    def __init__(self, method: str, code: int | None, description: str, retry_after: float | None = None):
        self.method, self.code, self.description, self.retry_after = method, code, description, retry_after
        super().__init__(f"{method}: API error {code}: {description}")

class RateLimitError(APIError):
    pass

class TransportError(BotError):
    pass

class UnsupportedCapability(BotError):
    pass

class HandlerError(BotError):
    pass
