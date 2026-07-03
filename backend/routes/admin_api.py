"""
admin_api.py — Admin-only backend routes
- POST /api/admin/create-user   (create auth user from admin panel)
- GET  /api/admin/users         (list users with email + plan)
- POST /api/admin/grant-premium (grant/revoke lifetime premium)
"""
import json
import re
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from auth_utils import get_supabase as _get_supabase, require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _verify_admin(request: Request):
    """Verify the caller is an authenticated admin user."""
    return require_admin(request)


class CreateUserBody(BaseModel):
    name: str
    email: str
    password: str
    grant_premium: bool = False


class SetPremiumBody(BaseModel):
    user_id: str
    action: str  # "grant" or "revoke"


class CategoryBody(BaseModel):
    name: str
    slug: str
    icon: str = "🎨"
    description: Optional[str] = None
    display_order: int = 0

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        slug = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError("slug must contain lowercase letters, numbers, and hyphens only")
        return slug


class StyleBody(BaseModel):
    category_id: str
    title: str
    description: Optional[str] = None
    image_url: str
    meta_prompt: Optional[str] = None
    normal_prompt: Optional[str] = None
    json_prompt: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    is_premium: bool = False
    is_active: bool = True

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, value: str) -> str:
        url = value.strip()
        if not url.startswith("https://"):
            raise ValueError("image_url must use HTTPS")
        return url

    @field_validator("json_prompt")
    @classmethod
    def validate_json_prompt(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        text = value.strip()
        if not text:
            raise ValueError("json_prompt is required")
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("json_prompt must be valid JSON") from exc
        return text


class SetCategoryAccessBody(BaseModel):
    user_id: str
    category_id: str
    action: str  # "grant" or "revoke"


def _style_payload(body: StyleBody) -> dict:
    data = body.model_dump()
    normal_prompt = (body.normal_prompt or body.meta_prompt or "").strip()
    json_prompt = (body.json_prompt or "").strip()
    if not normal_prompt:
        raise HTTPException(status_code=422, detail="normal_prompt is required")
    if not json_prompt:
        raise HTTPException(status_code=422, detail="json_prompt is required")
    data["normal_prompt"] = normal_prompt
    data["json_prompt"] = json_prompt
    data["meta_prompt"] = normal_prompt
    data["prompt_preview"] = normal_prompt[:140]
    return data


@router.get("/catalog")
async def admin_catalog(request: Request):
    """Return all data needed by the admin panel."""
    _verify_admin(request)
    sb = _get_supabase()

    categories = sb.table("categories").select("*").order("display_order").execute()
    styles = (
        sb.table("ad_styles")
        .select("*, categories(name)")
        .order("created_at", desc=True)
        .execute()
    )
    profiles = sb.table("profiles").select("*").order("created_at", desc=True).execute()
    access = (
        sb.table("user_category_access")
        .select("user_id, category_id, status, expires_at, categories(name, slug)")
        .order("created_at", desc=True)
        .execute()
    )
    return {
        "categories": categories.data or [],
        "styles": styles.data or [],
        "users": profiles.data or [],
        "category_access": access.data or [],
    }


@router.post("/categories")
async def create_category(body: CategoryBody, request: Request):
    _verify_admin(request)
    result = _get_supabase().table("categories").insert(body.model_dump()).execute()
    return {"success": True, "category": (result.data or [None])[0]}


@router.put("/categories/{category_id}")
async def update_category(category_id: str, body: CategoryBody, request: Request):
    _verify_admin(request)
    result = _get_supabase().table("categories").update(body.model_dump()).eq("id", category_id).execute()
    return {"success": True, "category": (result.data or [None])[0]}


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str, request: Request):
    _verify_admin(request)
    _get_supabase().table("categories").delete().eq("id", category_id).execute()
    return {"success": True}


@router.post("/styles")
async def create_style(body: StyleBody, request: Request):
    _verify_admin(request)
    result = _get_supabase().table("ad_styles").insert(_style_payload(body)).execute()
    return {"success": True, "style": (result.data or [None])[0]}


@router.put("/styles/{style_id}")
async def update_style(style_id: str, body: StyleBody, request: Request):
    _verify_admin(request)
    result = _get_supabase().table("ad_styles").update(_style_payload(body)).eq("id", style_id).execute()
    return {"success": True, "style": (result.data or [None])[0]}


@router.delete("/styles/{style_id}")
async def delete_style(style_id: str, request: Request):
    _verify_admin(request)
    _get_supabase().table("ad_styles").delete().eq("id", style_id).execute()
    return {"success": True}


@router.post("/create-user")
async def create_user(body: CreateUserBody, request: Request):
    """Create a new user from the admin panel."""
    _verify_admin(request)
    sb = _get_supabase()
    if len(body.password) < 10:
        raise HTTPException(status_code=422, detail="Password must be at least 10 characters")

    try:
        result = sb.auth.admin.create_user({
            "email": body.email,
            "password": body.password,
            "email_confirm": True,
            "user_metadata": {"full_name": body.name}
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Could not create user. Check the email and password requirements.")

    if not result.user:
        raise HTTPException(status_code=400, detail="User creation failed")

    # Update profile with name + email (trigger should handle this, but be explicit)
    update_data = {"full_name": body.name, "email": body.email}
    if body.grant_premium:
        update_data["plan_type"] = "premium"
        update_data["subscription_expires_at"] = None  # lifetime

    sb.table("profiles").update(update_data).eq("id", result.user.id).execute()

    return {"success": True, "user_id": result.user.id}


@router.get("/users")
async def list_users(request: Request):
    """Return all users with email + plan info."""
    _verify_admin(request)
    sb = _get_supabase()

    profiles = sb.table("profiles").select("*").order("created_at", desc=True).execute()
    return {"users": profiles.data or []}


@router.post("/set-premium")
async def set_premium(body: SetPremiumBody, request: Request):
    """Grant or revoke lifetime premium for a user."""
    _verify_admin(request)
    sb = _get_supabase()

    if body.action == "grant":
        data = {"plan_type": "premium", "subscription_expires_at": None}
    elif body.action == "revoke":
        data = {"plan_type": "free", "subscription_expires_at": None}
    else:
        raise HTTPException(status_code=400, detail="action must be 'grant' or 'revoke'")

    result = sb.table("profiles").update(data).eq("id", body.user_id).execute()
    return {"success": True}


@router.post("/set-category-access")
async def set_category_access(body: SetCategoryAccessBody, request: Request):
    """Grant or revoke lifetime access to a single category."""
    _verify_admin(request)
    sb = _get_supabase()

    if body.action == "grant":
        sb.table("user_category_access").update({
            "status": "revoked",
        }).eq("user_id", body.user_id).eq("status", "active").neq("category_id", body.category_id).execute()
        sb.table("user_category_access").upsert({
            "user_id": body.user_id,
            "category_id": body.category_id,
            "source": "admin",
            "status": "active",
            "expires_at": None,
        }, on_conflict="user_id,category_id").execute()
    elif body.action == "revoke":
        sb.table("user_category_access").update({
            "status": "revoked",
        }).eq("user_id", body.user_id).eq("category_id", body.category_id).execute()
    else:
        raise HTTPException(status_code=400, detail="action must be 'grant' or 'revoke'")

    return {"success": True}
