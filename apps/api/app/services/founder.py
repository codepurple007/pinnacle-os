from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Founder, FounderSettings


def get_founder(db: Session) -> Founder:
    settings = get_settings()
    founder = db.scalar(select(Founder).where(Founder.email == settings.founder_email))
    if founder is None:
        founder = Founder(email=settings.founder_email, display_name=settings.founder_name)
        db.add(founder)
        db.flush()
        db.add(FounderSettings(founder_id=founder.id))
        db.flush()
    elif founder.settings is None:
        db.add(FounderSettings(founder_id=founder.id))
        db.flush()
    return founder
