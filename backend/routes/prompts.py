from fastapi import APIRouter, HTTPException, Request
from auth_utils import get_current_user, get_profile, get_supabase, profile_has_premium

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.get("/{style_id}")
async def get_prompt(style_id: str, request: Request):
    """Return full prompt text only when the caller is allowed to see it."""
    sb = get_supabase()
    result = (
        sb.table("ad_styles")
        .select("id, title, is_premium, is_active, meta_prompt")
        .eq("id", style_id)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Style not found")

    style = rows[0]
    user = get_current_user(request, required=False)
    profile = get_profile(user.id) if user else {}

    if not style.get("is_active", True) and not profile.get("is_admin"):
        raise HTTPException(status_code=404, detail="Style not found")

    if style.get("is_premium"):
        if not user:
            raise HTTPException(status_code=401, detail="Login required")
        if not profile_has_premium(profile):
            raise HTTPException(status_code=403, detail="Premium access required")

    return {
        "id": style["id"],
        "title": style.get("title"),
        "prompt": style.get("meta_prompt") or "",
    }
