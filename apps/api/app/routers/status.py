from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import EmailMessage, OAuthAccount
from app.services.founder import get_founder

router = APIRouter()


@router.get("/status")
def status(db: Session = Depends(get_db)):
    settings = get_settings()
    founder = get_founder(db)
    account = db.scalar(
        select(OAuthAccount).where(OAuthAccount.founder_id == founder.id, OAuthAccount.provider == "google")
    )
    count = db.scalar(select(func.count()).select_from(EmailMessage)) or 0
    return {
        "founder": {
            "name": founder.display_name,
            "email": founder.email,
            "timezone": founder.timezone,
            "writes_enabled": founder.writes_enabled,
            "last_sync_at": founder.last_sync_at.isoformat() if founder.last_sync_at else None,
        },
        "google": {
            "connected": account is not None,
            "email": account.google_email if account else None,
            "oauth_configured": bool(settings.google_client_id and settings.google_client_secret),
            "scopes": (account.scopes if account else ""),
            "readonly": True,
        },
        "inbox": {"message_count": int(count)},
        "phase": 3,
        "agent_can_send": False,
        "agent_can_write_calendar": False,
    }
