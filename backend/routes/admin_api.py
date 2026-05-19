"""
admin_api.py — Admin-only backend routes
- POST /api/admin/create-user   (create auth user from admin panel)
- GET  /api/admin/users         (list users with email + plan)
- POST /api/admin/grant-premium (grant/revoke lifetime premium)
"""
import os
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _get_supabase():
    from main import supabase
    return supabase


def _verify_admin(request: Request):
    """Verify the caller is an authenticated admin user."""
    sb = _get_supabase()
    auth = request.headers.get("authorization", "")
    token = auth.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing auth token")

    try:
        user_resp = sb.auth.get_user(token)
        user = user_resp.user
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Token verification failed")

    profile = sb.table("profiles").select("is_admin").eq("id", user.id).single().execute()
    if not profile.data or not profile.data.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


class CreateUserBody(BaseModel):
    name: str
    email: str
    password: str
    grant_premium: bool = False


class SetPremiumBody(BaseModel):
    user_id: str
    action: str  # "grant" or "revoke"


@router.post("/create-user")
async def create_user(body: CreateUserBody, request: Request):
    """Create a new user from the admin panel."""
    _verify_admin(request)
    sb = _get_supabase()

    try:
        result = sb.auth.admin.create_user({
            "email": body.email,
            "password": body.password,
            "email_confirm": True,
            "user_metadata": {"full_name": body.name}
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not create user: {e}")

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
