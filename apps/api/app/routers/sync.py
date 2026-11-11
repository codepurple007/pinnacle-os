from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.crypto import decrypt_secret
from app.db import get_db
from app.models import OAuthAccount
from app.services.audit import write_audit
from app.services.founder import get_founder
from app.services.ingest import ingest_message, mark_synced

router = APIRouter()


@router.post("/sync/gmail")
def sync_gmail(db: Session = Depends(get_db)):
    """Read-only pull of recent inbox messages. No send."""
    founder = get_founder(db)
    account = db.scalar(
        select(OAuthAccount).where(OAuthAccount.founder_id == founder.id, OAuthAccount.provider == "google")
    )
    if account is None:
        raise HTTPException(status_code=400, detail="Google is not connected. Use Connect or demo ingest.")
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured on the server.")

    from pinnacle_google import GoogleOAuth, GoogleReadonlyClient, Phase3ReadOnly

    oauth = GoogleOAuth(settings.google_client_id, settings.google_client_secret, settings.google_redirect_uri)
    creds = oauth.credentials_from_refresh(decrypt_secret(account.refresh_token_enc))
    client = GoogleReadonlyClient(creds)
    try:
        client.send_email("phase3-guard")
    except Phase3ReadOnly:
        pass
    else:
        raise HTTPException(status_code=500, detail="Send guard failed: connector allowed send.")

    imported = 0
    for item in client.list_recent_messages(max_results=15):
        ingest_message(
            db,
            gmail_message_id=item.gmail_message_id,
            gmail_thread_id=item.gmail_thread_id,
            from_addr=item.from_addr,
            to_addrs=item.to_addrs,
            cc_addrs=item.cc_addrs,
            subject=item.subject,
            body_text=item.body_text,
            snippet=item.snippet,
            sent_at=item.sent_at,
            headers=item.headers,
            actor="agent",
        )
        imported += 1
    now = datetime.now(timezone.utc)
    mark_synced(db, founder, now)
    return {"imported": imported, "last_sync_at": now.isoformat(), "mode": "gmail_readonly"}


@router.get("/calendar/today")
def calendar_today(db: Session = Depends(get_db)):
    founder = get_founder(db)
    account = db.scalar(
        select(OAuthAccount).where(OAuthAccount.founder_id == founder.id, OAuthAccount.provider == "google")
    )
    if account is None:
        return {"events": [], "source": "disconnected"}
    settings = get_settings()
    if not settings.google_client_id:
        return {"events": [], "source": "oauth_not_configured"}

    from pinnacle_google import GoogleOAuth, GoogleReadonlyClient

    oauth = GoogleOAuth(settings.google_client_id, settings.google_client_secret, settings.google_redirect_uri)
    creds = oauth.credentials_from_refresh(decrypt_secret(account.refresh_token_enc))
    client = GoogleReadonlyClient(creds)
    events = client.list_today_events(founder.timezone)
    write_audit(db, actor="agent", action="calendar_read", entity_type="calendar", payload={"count": len(events)})
    return {
        "events": [
            {
                "id": event.google_event_id,
                "title": event.title,
                "start_at": event.start_at.isoformat() if event.start_at else None,
                "end_at": event.end_at.isoformat() if event.end_at else None,
            }
            for event in events
        ],
        "source": "google_readonly",
    }
