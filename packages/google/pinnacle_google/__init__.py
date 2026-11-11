"""Google Connector Hub — the only module allowed to handle Google credentials.

Phase 3 is read-only. There is no send or calendar-write API on this package.
"""

from pinnacle_google.errors import ConnectorError, GoogleNotConfigured, Phase3ReadOnly
from pinnacle_google.oauth import GoogleOAuth
from pinnacle_google.readonly import GoogleReadonlyClient

__all__ = [
    "ConnectorError",
    "GoogleNotConfigured",
    "GoogleOAuth",
    "GoogleReadonlyClient",
    "Phase3ReadOnly",
]
