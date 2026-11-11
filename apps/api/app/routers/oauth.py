from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.crypto import encrypt_secret
from app.db import get_db
from app.models import OAuthAccount, OAuthState
from app.services.audit import write_audit
from app.services.founder import get_founder

router = APIRouter()


def _oauth():
    from pinnacle_google import GoogleNotConfigured, GoogleOAuth

    settings = get_settings()
    try:
        return GoogleOAuth(
            settings.google_client_id,
            settings.google_client_secret,
            settings.google_redirect_uri,
        )
    except GoogleNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/oauth/google/start")
def google_start(db: Session = Depends(get_db)):
    oauth = _oauth()
    state = uuid4().hex
    db.add(OAuthState(state=state))
    write_audit(db, actor="founder", action="oauth_start", entity_type="oauth_account", payload={"provider": "google"})
    return {"authorization_url": oauth.authorization_url(state), "state": state}


@router.get("/oauth/google/callback")
def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    settings = get_settings()
    saved = db.scalar(select(OAuthState).where(OAuthState.state == state))
    if saved is None:
        raise HTTPException(status_code=400, detail="Unknown OAuth state.")
    db.delete(saved)
    oauth = _oauth()
    tokens = oauth.exchange_code(code)
    if not tokens.refresh_token:
        raise HTTPException(
            status_code=400,
            detail="Google did not return a refresh token. Reconnect and grant consent again.",
        )
    founder = get_founder(db)
    account = db.scalar(
        select(OAuthAccount).where(OAuthAccount.founder_id == founder.id, OAuthAccount.provider == "google")
    )
    if account is None:
        account = OAuthAccount(founder_id=founder.id, provider="google")
        db.add(account)
    account.refresh_token_enc = encrypt_secret(tokens.refresh_token)
    account.access_token_enc = encrypt_secret(tokens.access_token)
    account.google_email = tokens.google_email
    account.scopes = " ".join(tokens.scopes)
    if tokens.expiry_iso:
        account.expiry = datetime.fromisoformat(tokens.expiry_iso)
    write_audit(
        db,
        actor="founder",
        action="oauth_connected",
        entity_type="oauth_account",
        entity_id=str(account.id),
        payload={"google_email": tokens.google_email, "scopes": list(tokens.scopes)},
    )
    db.commit()
    return RedirectResponse(f"{settings.web_origin}/?connected=1")


@router.delete("/oauth/google")
def google_disconnect(db: Session = Depends(get_db)):
    founder = get_founder(db)
    account = db.scalar(
        select(OAuthAccount).where(OAuthAccount.founder_id == founder.id, OAuthAccount.provider == "google")
    )
    if account is None:
        return {"disconnected": False, "reason": "not_connected"}
    db.delete(account)
    write_audit(
        db,
        actor="founder",
        action="oauth_disconnected",
        entity_type="oauth_account",
        payload={"google_email": account.google_email},
    )
    return {"disconnected": True}
