from fastapi import HTTPException, Request
from datetime import datetime, timezone


def get_supabase():
    from main import supabase
    return supabase


def bearer_token(request: Request, required: bool = True) -> str | None:
    auth = request.headers.get("authorization", "")
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        if required:
            raise HTTPException(status_code=401, detail="Missing auth token")
        return None
    return token.strip()


def get_current_user(request: Request, required: bool = True):
    token = bearer_token(request, required=required)
    if not token:
        return None

    try:
        user_resp = get_supabase().auth.get_user(token)
        user = user_resp.user
    except Exception:
        raise HTTPException(status_code=401, detail="Token verification failed")

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def get_profile(user_id: str) -> dict:
    result = (
        get_supabase()
        .table("profiles")
        .select("id, email, full_name, is_admin, plan_type, subscription_expires_at")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else {}


def require_admin(request: Request):
    user = get_current_user(request)
    profile = get_profile(user.id)
    if not profile.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def profile_has_premium(profile: dict) -> bool:
    if profile.get("is_admin"):
        return True
    if profile.get("plan_type") != "premium":
        return False
    # A null expiry means lifetime access. Expiring subscriptions are not used
    # currently; SQL keeps this field for future plans.
    expires_at = profile.get("subscription_expires_at")
    if not expires_at:
        return True
    try:
        expires = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
        return expires > datetime.now(timezone.utc)
    except ValueError:
        return False
