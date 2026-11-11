from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EmailMessage, EmailThread, Founder
from app.services.audit import write_audit


def upsert_thread(db: Session, gmail_thread_id: str, subject: str) -> EmailThread:
    thread = db.scalar(select(EmailThread).where(EmailThread.gmail_thread_id == gmail_thread_id))
    if thread is None:
        thread = EmailThread(gmail_thread_id=gmail_thread_id, subject=subject)
        db.add(thread)
        db.flush()
    elif subject and not thread.subject:
        thread.subject = subject
    return thread


def ingest_message(
    db: Session,
    *,
    gmail_message_id: str,
    gmail_thread_id: str,
    from_addr: str,
    to_addrs: list[str] | str,
    cc_addrs: list[str] | str | None = None,
    subject: str,
    body_text: str,
    snippet: str = "",
    sent_at: datetime | None = None,
    headers: dict | None = None,
    actor: str = "agent",
) -> EmailMessage:
    existing = db.scalar(select(EmailMessage).where(EmailMessage.gmail_message_id == gmail_message_id))
    if existing:
        return existing

    thread = upsert_thread(db, gmail_thread_id, subject)
    to_value = to_addrs if isinstance(to_addrs, str) else ", ".join(to_addrs)
    cc_value = cc_addrs if isinstance(cc_addrs, str) else ", ".join(cc_addrs or [])
    message = EmailMessage(
        thread_id=thread.id,
        gmail_message_id=gmail_message_id,
        from_addr=from_addr,
        to_addrs=to_value,
        cc_addrs=cc_value,
        sent_at=sent_at,
        body_text=body_text,
        snippet=snippet or body_text[:240],
        raw_headers_json=headers or {"subject": subject},
    )
    db.add(message)
    db.flush()
    write_audit(
        db,
        actor=actor,
        action="message_ingested",
        entity_type="email_message",
        entity_id=str(message.id),
        message_id=message.id,
        payload={"from": from_addr, "subject": subject, "thread_id": gmail_thread_id},
    )
    return message


def mark_synced(db: Session, founder: Founder, at: datetime) -> None:
    founder.last_sync_at = at
    write_audit(
        db,
        actor="agent",
        action="mailbox_synced",
        entity_type="founder",
        entity_id=str(founder.id),
        payload={"at": at.isoformat()},
    )


def new_demo_gmail_id() -> str:
    return f"demo-{uuid4()}"
