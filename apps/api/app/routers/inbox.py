from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import EmailMessage, EmailThread

router = APIRouter()


@router.get("/inbox/messages")
def list_messages(db: Session = Depends(get_db)):
    rows = db.scalars(
        select(EmailMessage)
        .options(selectinload(EmailMessage.thread))
        .order_by(desc(EmailMessage.created_at))
        .limit(100)
    ).all()
    return [_serialize_message(row) for row in rows]


@router.get("/inbox/needs-you")
def needs_you():
    """Classifier is Phase 4. Empty on purpose."""
    return {"items": [], "phase": 3, "reason": "escalation requires the gatekeeper"}


@router.get("/inbox/approvals")
def approvals():
    """Drafts are Phase 4. Empty on purpose."""
    return {"items": [], "phase": 3, "reason": "no drafts until the gatekeeper exists"}


def _serialize_message(row: EmailMessage) -> dict:
    thread: EmailThread = row.thread
    return {
        "id": str(row.id),
        "thread_id": str(row.thread_id),
        "gmail_message_id": row.gmail_message_id,
        "gmail_thread_id": thread.gmail_thread_id,
        "subject": thread.subject,
        "from_addr": row.from_addr,
        "to_addrs": row.to_addrs,
        "snippet": row.snippet,
        "body_text": row.body_text,
        "sent_at": row.sent_at.isoformat() if row.sent_at else None,
        "direction": row.direction,
    }
