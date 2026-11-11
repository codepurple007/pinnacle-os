from __future__ import annotations

from dataclasses import dataclass

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from pinnacle_google.errors import GoogleNotConfigured

# Phase 3: read-only. Do not add gmail.send or calendar write scopes here.
SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
)


@dataclass(frozen=True)
class OAuthTokens:
    refresh_token: str
    access_token: str
    expiry_iso: str | None
    scopes: tuple[str, ...]
    google_email: str | None


class GoogleOAuth:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> None:
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self.redirect_uri = redirect_uri
        if not self.client_id or not self.client_secret:
            raise GoogleNotConfigured(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are required to connect Gmail."
            )

    def _client_config(self) -> dict:
        return {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": [self.redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

    def authorization_url(self, state: str) -> str:
        flow = Flow.from_client_config(self._client_config(), scopes=list(SCOPES))
        flow.redirect_uri = self.redirect_uri
        url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )
        return url

    def exchange_code(self, code: str) -> OAuthTokens:
        flow = Flow.from_client_config(self._client_config(), scopes=list(SCOPES))
        flow.redirect_uri = self.redirect_uri
        flow.fetch_token(code=code)
        creds = flow.credentials
        email = _email_from_credentials(creds)
        expiry = creds.expiry.isoformat() if creds.expiry else None
        return OAuthTokens(
            refresh_token=creds.refresh_token or "",
            access_token=creds.token or "",
            expiry_iso=expiry,
            scopes=tuple(creds.scopes or SCOPES),
            google_email=email,
        )

    def credentials_from_refresh(self, refresh_token: str) -> Credentials:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=list(SCOPES),
        )
        creds.refresh(Request())
        return creds


def _email_from_credentials(creds: Credentials) -> str | None:
    try:
        from googleapiclient.discovery import build

        service = build("oauth2", "v2", credentials=creds, cache_discovery=False)
        info = service.userinfo().get().execute()
        return info.get("email")
    except Exception:
        return None
