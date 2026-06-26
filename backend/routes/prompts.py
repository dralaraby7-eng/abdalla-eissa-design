from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from auth_utils import get_current_user, get_profile, get_supabase, profile_has_premium

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


class PromptBatchRequest(BaseModel):
    style_ids: list[str] = Field(default_factory=list, max_length=200)


def _current_profile(request: Request) -> tuple[object | None, dict]:
    user = get_current_user(request, required=False)
    profile = get_profile(user.id) if user else {}
    return user, profile


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
    user, profile = _current_profile(request)

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


@router.post("/batch")
async def get_prompts_batch(payload: PromptBatchRequest, request: Request):
    """Return accessible prompts in one request for a smoother gallery."""
    style_ids = []
    seen = set()
    for style_id in payload.style_ids:
        if style_id and style_id not in seen:
            style_ids.append(style_id)
            seen.add(style_id)

    if not style_ids:
        return {"prompts": {}}

    sb = get_supabase()
    result = (
        sb.table("ad_styles")
        .select("id, is_premium, is_active, meta_prompt")
        .in_("id", style_ids)
        .execute()
    )

    user, profile = _current_profile(request)
    can_view_premium = bool(user and profile_has_premium(profile))
    is_admin = bool(profile.get("is_admin"))

    prompts = {}
    for style in result.data or []:
        if not style.get("is_active", True) and not is_admin:
            continue
        if style.get("is_premium") and not can_view_premium:
            continue
        prompts[style["id"]] = style.get("meta_prompt") or ""

    return {"prompts": prompts}
