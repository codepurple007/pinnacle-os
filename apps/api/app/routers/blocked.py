from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/drafts/{draft_id}/approve")
def approve_blocked(draft_id: str):
    raise HTTPException(
        status_code=403,
        detail=f"Phase 3 cannot send mail. Draft {draft_id} was not approved. Gatekeeper is Phase 4.",
    )


@router.post("/drafts/{draft_id}/reject")
def reject_blocked(draft_id: str):
    raise HTTPException(status_code=403, detail="No drafts exist in Phase 3.")
