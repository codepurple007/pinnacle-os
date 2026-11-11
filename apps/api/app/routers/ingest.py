from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.services.ingest import ingest_message, new_demo_gmail_id

router = APIRouter()

TUESDAY_CORPUS = [
    {
        "from_addr": "Dana Voss <dana@northline.co>",
        "subject": "Re: Weekly recap — week of 10 Mar",
        "thread_id": "thread-northline-recap",
        "body_text": (
            "Quick one before my standup — what did we spend on Facebook last month? "
            "I have a board packet at 9. The recap PDF is huge and I can’t find the number."
        ),
    },
    {
        "from_addr": "Maya Chen <maya@freelance.example>",
        "subject": "Thu shoot — Northline still on?",
        "thread_id": "thread-maya-hold",
        "body_text": (
            "Hi Alex, confirming I’m holding Thursday 2–6. Need a yes/no by 9 or I’ll take "
            "another booking. Also, invoice from last month still outstanding?"
        ),
    },
    {
        "from_addr": "Ellis Ward <ellis@harborandpine.com>",
        "subject": "Can we move tomorrow?",
        "thread_id": "thread-harbor-reschedule",
        "body_text": (
            "Hey — I need to move tomorrow’s 11 AM to Thursday. Morning is better if you can. "
            "Also still waiting on the PDP hero set — we were supposed to have options Monday."
        ),
    },
    {
        "from_addr": "Ellis Ward <ellis@harborandpine.com>",
        "subject": "Creative quality",
        "thread_id": "thread-harbor-creative",
        "body_text": (
            "I am unhappy with the creative quality on the last round. The PDP heroes feel "
            "generic and not like us. Let’s jump on a call about this today."
        ),
    },
    {
        "from_addr": "Priya Raman <priya@kiteandco.example>",
        "subject": "Q3 brief — call or doc?",
        "thread_id": "thread-kite-q3",
        "body_text": "Do we need a call to walk through the Q3 brief or can you just send the doc?",
    },
]


class IngestBody(BaseModel):
    from_addr: str
    subject: str
    body_text: str
    to_addrs: list[str] = Field(default_factory=lambda: ["alex@pinnacle.example"])
    cc_addrs: list[str] = Field(default_factory=list)
    thread_id: str | None = None
    gmail_message_id: str | None = None
    sent_at: datetime | None = None


def _ingest_one(db: Session, body: IngestBody):
    gmail_message_id = body.gmail_message_id or new_demo_gmail_id()
    gmail_thread_id = body.thread_id or gmail_message_id
    return ingest_message(
        db,
        gmail_message_id=gmail_message_id,
        gmail_thread_id=gmail_thread_id,
        from_addr=body.from_addr,
        to_addrs=body.to_addrs,
        cc_addrs=body.cc_addrs,
        subject=body.subject,
        body_text=body.body_text,
        snippet=body.body_text[:240],
        sent_at=body.sent_at or datetime.now(timezone.utc),
        headers={"subject": body.subject, "from": body.from_addr},
        actor="founder",
    )


@router.post("/dev/ingest")
def dev_ingest(body: IngestBody, db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.dev_ingest_enabled:
        raise HTTPException(status_code=403, detail="Demo ingest is disabled.")
    message = _ingest_one(db, body)
    return {
        "id": str(message.id),
        "gmail_message_id": message.gmail_message_id,
        "thread_id": str(message.thread_id),
        "subject": body.subject,
    }


@router.post("/dev/seed-tuesday")
def seed_tuesday(db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.dev_ingest_enabled:
        raise HTTPException(status_code=403, detail="Demo ingest is disabled.")
    created = []
    for item in TUESDAY_CORPUS:
        message = _ingest_one(
            db,
            IngestBody(
                from_addr=item["from_addr"],
                subject=item["subject"],
                body_text=item["body_text"],
                thread_id=item["thread_id"],
                gmail_message_id=item["thread_id"] + "-msg-1",
            ),
        )
        created.append({"id": str(message.id), "subject": item["subject"]})
    return {"seeded": len(created), "items": created}
