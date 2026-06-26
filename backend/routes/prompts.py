from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from auth_utils import get_current_user, get_profile, get_supabase, profile_has_premium
from rate_limit import enforce_rate_limit

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


class PromptBatchRequest(BaseModel):
    style_ids: list[str] = Field(default_factory=list, max_length=200)


def _current_profile(request: Request) -> tuple[object | None, dict]:
    user = get_current_user(request, required=False)
    profile = get_profile(user.id) if user else {}
    return user, profile


def _user_category_ids(user_id: str) -> set[str]:
    result = (
        get_supabase()
        .table("user_category_access")
        .select("category_id, status, expires_at")
        .eq("user_id", user_id)
        .eq("status", "active")
        .execute()
    )
    rows = result.data or []
    active_ids = set()
    now = datetime.now(timezone.utc)
    for row in rows:
        category_id = row.get("category_id")
        if not category_id:
            continue
        expires_at = row.get("expires_at")
        if expires_at:
            try:
                expires = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
                if expires <= now:
                    continue
            except ValueError:
                continue
        active_ids.add(category_id)
    return active_ids


def _has_style_access(style: dict, user, profile: dict, category_ids: set[str] | None = None) -> bool:
    if not style.get("is_premium"):
        return True
    if not user:
        return False
    if profile_has_premium(profile):
        return True
    category_ids = category_ids if category_ids is not None else _user_category_ids(user.id)
    return bool(style.get("category_id") in category_ids)


@router.get("/access")
async def get_access_summary(request: Request):
    """Return a browser-safe summary of the caller's prompt access."""
    user, profile = _current_profile(request)
    if not user:
        return {"all_access": False, "category_ids": []}
    return {
        "all_access": profile_has_premium(profile),
        "category_ids": sorted(_user_category_ids(user.id)),
    }


@router.get("/{style_id}")
async def get_prompt(style_id: str, request: Request):
    """Return full prompt text only when the caller is allowed to see it."""
    enforce_rate_limit(request, "prompt-single", limit=120, window_seconds=60)
    sb = get_supabase()
    result = (
        sb.table("ad_styles")
        .select("id, category_id, title, is_premium, is_active, meta_prompt, normal_prompt, json_prompt")
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

    if not _has_style_access(style, user, profile):
        if not user:
            raise HTTPException(status_code=401, detail="Login required")
        raise HTTPException(status_code=403, detail="Category access or All Access required")

    normal_prompt = style.get("normal_prompt") or style.get("meta_prompt") or ""
    json_prompt = style.get("json_prompt") or ""

    return {
        "id": style["id"],
        "title": style.get("title"),
        "prompt": normal_prompt,
        "normal_prompt": normal_prompt,
        "json_prompt": json_prompt,
    }


@router.post("/batch")
async def get_prompts_batch(payload: PromptBatchRequest, request: Request):
    """Return accessible prompts in one request for a smoother gallery."""
    enforce_rate_limit(request, "prompt-batch", limit=30, window_seconds=60)
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
        .select("id, category_id, is_premium, is_active, meta_prompt, normal_prompt, json_prompt")
        .in_("id", style_ids)
        .execute()
    )

    user, profile = _current_profile(request)
    is_admin = bool(profile.get("is_admin"))
    category_ids = _user_category_ids(user.id) if user and not profile_has_premium(profile) else set()

    prompts = {}
    prompt_details = {}
    for style in result.data or []:
        if not style.get("is_active", True) and not is_admin:
            continue
        if not _has_style_access(style, user, profile, category_ids):
            continue
        normal_prompt = style.get("normal_prompt") or style.get("meta_prompt") or ""
        prompts[style["id"]] = normal_prompt
        prompt_details[style["id"]] = {
            "normal_prompt": normal_prompt,
            "json_prompt": style.get("json_prompt") or "",
        }

    return {"prompts": prompts, "prompt_details": prompt_details}
