from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from pinnacle_google.errors import Phase3ReadOnly


@dataclass(frozen=True)
class GmailMessage:
    gmail_message_id: str
    gmail_thread_id: str
    from_addr: str
    to_addrs: list[str]
    cc_addrs: list[str]
    subject: str
    body_text: str
    snippet: str
    sent_at: datetime | None
    headers: dict[str, str]


@dataclass(frozen=True)
class CalendarItem:
    google_event_id: str
    title: str
    start_at: datetime | None
    end_at: datetime | None


class GoogleReadonlyClient:
    """Read Gmail and Calendar. Mutation methods exist only to fail closed."""

    def __init__(self, credentials: Credentials) -> None:
        self._credentials = credentials

    def send_email(self, *_args, **_kwargs) -> None:
        raise Phase3ReadOnly("Gmail send is disabled in Phase 3.")

    def create_calendar_event(self, *_args, **_kwargs) -> None:
        raise Phase3ReadOnly("Calendar writes are disabled in Phase 3.")

    def list_recent_messages(self, max_results: int = 20) -> list[GmailMessage]:
        gmail = build("gmail", "v1", credentials=self._credentials, cache_discovery=False)
        listed = (
            gmail.users()
            .messages()
            .list(userId="me", maxResults=max_results, labelIds=["INBOX"])
            .execute()
        )
        out: list[GmailMessage] = []
        for item in listed.get("messages", []):
            raw = (
                gmail.users()
                .messages()
                .get(userId="me", id=item["id"], format="full")
                .execute()
            )
            out.append(_parse_gmail_message(raw))
        return out

    def list_today_events(self, timezone_name: str = "America/New_York") -> list[CalendarItem]:
        calendar = build("calendar", "v3", credentials=self._credentials, cache_discovery=False)
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        events = (
            calendar.events()
            .list(
                calendarId="primary",
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                timeZone=timezone_name,
            )
            .execute()
        )
        items: list[CalendarItem] = []
        for event in events.get("items", []):
            items.append(
                CalendarItem(
                    google_event_id=event.get("id", ""),
                    title=event.get("summary") or "(no title)",
                    start_at=_parse_event_time(event.get("start") or {}),
                    end_at=_parse_event_time(event.get("end") or {}),
                )
            )
        return items


def _header_map(payload: dict) -> dict[str, str]:
    headers = {}
    for item in payload.get("headers") or []:
        name = (item.get("name") or "").lower()
        headers[name] = item.get("value") or ""
    return headers


def _walk_body(payload: dict) -> str:
    mime = payload.get("mimeType") or ""
    body = payload.get("body") or {}
    data = body.get("data")
    if mime.startswith("text/plain") and data:
        import base64

        padded = data + "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", errors="replace")
    for part in payload.get("parts") or []:
        text = _walk_body(part)
        if text:
            return text
    if data:
        import base64

        padded = data + "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", errors="replace")
    return ""


def _parse_gmail_message(raw: dict) -> GmailMessage:
    payload = raw.get("payload") or {}
    headers = _header_map(payload)
    to_addrs = [part.strip() for part in (headers.get("to") or "").split(",") if part.strip()]
    cc_addrs = [part.strip() for part in (headers.get("cc") or "").split(",") if part.strip()]
    sent_at = None
    if headers.get("date"):
        try:
            sent_at = parsedate_to_datetime(headers["date"])
        except Exception:
            sent_at = None
    return GmailMessage(
        gmail_message_id=raw.get("id") or "",
        gmail_thread_id=raw.get("threadId") or "",
        from_addr=headers.get("from") or "",
        to_addrs=to_addrs,
        cc_addrs=cc_addrs,
        subject=headers.get("subject") or "(no subject)",
        body_text=_walk_body(payload),
        snippet=raw.get("snippet") or "",
        sent_at=sent_at,
        headers=headers,
    )


def _parse_event_time(blob: dict) -> datetime | None:
    value = blob.get("dateTime") or blob.get("date")
    if not value:
        return None
    try:
        if len(value) == 10:
            return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
