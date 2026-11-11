from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AuditEvent


def write_audit(
    db: Session,
    *,
    actor: str,
    action: str,
    entity_type: str = "",
    entity_id: str | None = None,
    message_id=None,
    payload: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        message_id=message_id,
        payload_json=payload or {},
    )
    db.add(event)
    db.flush()
    return event
