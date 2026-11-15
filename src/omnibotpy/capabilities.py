"""Explicit support table; 'unknown' is not synonymous with supported."""
from enum import StrEnum

class Support(StrEnum):
    SUPPORTED = "supported"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"

# Implementation status in this SDK, NOT a claim about the platform's full feature set.
IMPLEMENTED = {
    "telegram": frozenset({"message", "polling", "webhook", "media", "callback", "raw_api"}),
    "bale": frozenset({"message", "polling", "webhook", "media", "callback", "raw_api"}),
    # Experimental adapter is coded, but platform behavior remains unverified.
    "soroush": frozenset(),
}

def capability(platform: str, name: str) -> Support:
    if name in IMPLEMENTED.get(platform, ()):
        return Support.SUPPORTED
    return Support.UNKNOWN
