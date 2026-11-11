from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.audit import write_audit
from app.services.founder import get_founder

router = APIRouter()


class KillSwitchBody(BaseModel):
    writes_enabled: bool


@router.post("/settings/kill-switch")
def kill_switch(body: KillSwitchBody, db: Session = Depends(get_db)):
    founder = get_founder(db)
    founder.writes_enabled = body.writes_enabled
    write_audit(
        db,
        actor="founder",
        action="kill_switch_toggled",
        entity_type="founder",
        entity_id=str(founder.id),
        payload={"writes_enabled": body.writes_enabled},
    )
    return {
        "writes_enabled": founder.writes_enabled,
        "note": "Phase 3 cannot send or book regardless of this switch. The switch is wired so later phases honor it.",
    }
