from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuditEvent

router = APIRouter()


@router.get("/audit")
def list_audit(db: Session = Depends(get_db), limit: int = 100):
    rows = db.scalars(select(AuditEvent).order_by(desc(AuditEvent.at)).limit(min(limit, 200))).all()
    return [
        {
            "id": str(row.id),
            "at": row.at.isoformat() if row.at else None,
            "actor": row.actor,
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "payload": row.payload_json,
        }
        for row in rows
    ]
