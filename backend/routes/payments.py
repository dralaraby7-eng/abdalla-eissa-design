import os
import hashlib
import hmac
import requests
import uuid
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from auth_utils import get_current_user, get_supabase
from rate_limit import enforce_rate_limit

router = APIRouter(prefix="/api/payments", tags=["payments"])

PAYMOB_API_KEY    = os.getenv("PAYMOB_API_KEY")
INTEGRATION_ID    = int(os.getenv("PAYMOB_INTEGRATION_ID", "0"))
IFRAME_ID         = os.getenv("PAYMOB_IFRAME_ID")
HMAC_SECRET       = os.getenv("PAYMOB_HMAC_SECRET", "")
PRICE_LIFETIME_EGP = int(os.getenv("PRICE_LIFETIME_EGP_CENTS", "25000"))   # 250 EGP, backwards compatible
PRICE_ALL_ACCESS_EGP = int(os.getenv("PRICE_ALL_ACCESS_EGP_CENTS", str(PRICE_LIFETIME_EGP)))
PRICE_CATEGORY_EGP = int(os.getenv("PRICE_CATEGORY_EGP_CENTS", "9900"))     # 99 EGP
FRONTEND_URL      = os.getenv("FRONTEND_URL", "http://localhost:5500")

PAYMOB_BASE = "https://accept.paymob.com/api"


class OrderRequest(BaseModel):
    billing: str = "all_access_lifetime_egp"
    category_slug: str | None = None


def _require_paymob_config():
    missing = [
        key for key, value in {
            "PAYMOB_API_KEY": PAYMOB_API_KEY,
            "PAYMOB_INTEGRATION_ID": INTEGRATION_ID,
            "PAYMOB_IFRAME_ID": IFRAME_ID,
            "PAYMOB_HMAC_SECRET": HMAC_SECRET,
        }.items()
        if not value
    ]
    if missing:
        raise HTTPException(status_code=500, detail=f"Missing payment configuration: {', '.join(missing)}")


def _get_auth_token() -> str:
    res = requests.post(f"{PAYMOB_BASE}/auth/tokens", json={"api_key": PAYMOB_API_KEY}, timeout=20)
    res.raise_for_status()
    return res.json()["token"]


def _create_order(auth_token: str, amount_cents: int, merchant_order_id: str) -> int:
    payload = {
        "auth_token": auth_token,
        "delivery_needed": False,
        "amount_cents": amount_cents,
        "currency": "EGP",
        "merchant_order_id": merchant_order_id,
        "items": []
    }
    res = requests.post(f"{PAYMOB_BASE}/ecommerce/orders", json=payload, timeout=20)
    res.raise_for_status()
    return res.json()["id"]


def _get_payment_key(auth_token: str, order_id: int, amount_cents: int, email: str) -> str:
    payload = {
        "auth_token": auth_token,
        "amount_cents": amount_cents,
        "expiration": 3600,
        "order_id": order_id,
        "billing_data": {
            "apartment": "NA", "email": email, "floor": "NA",
            "first_name": "Customer", "street": "NA", "building": "NA",
            "phone_number": "NA", "shipping_method": "NA", "postal_code": "NA",
            "city": "NA", "country": "NA", "last_name": "NA", "state": "NA"
        },
        "currency": "EGP",
        "integration_id": INTEGRATION_ID,
    }
    res = requests.post(f"{PAYMOB_BASE}/acceptance/payment_keys", json=payload, timeout=20)
    res.raise_for_status()
    return res.json()["token"]


@router.post("/create-order")
async def create_order(body: OrderRequest, request: Request):
    enforce_rate_limit(request, "payment-create", limit=10, window_seconds=60)
    _require_paymob_config()
    user = get_current_user(request)
    email = user.email
    if not email:
        raise HTTPException(status_code=400, detail="Authenticated user has no email")

    sb = get_supabase()
    billing = body.billing or "all_access_lifetime_egp"
    category_id = None
    access_scope = "all"
    if billing in {"lifetime_egp", "all_access_lifetime_egp", "all_access"}:
        amount = PRICE_ALL_ACCESS_EGP
    elif billing in {"category_lifetime_egp", "category"}:
        if not body.category_slug:
            raise HTTPException(status_code=400, detail="category_slug is required for category purchases")
        cat_result = (
            sb.table("categories")
            .select("id, slug, is_active")
            .eq("slug", body.category_slug)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        cat_rows = cat_result.data or []
        if not cat_rows:
            raise HTTPException(status_code=404, detail="Category not found")
        category_id = cat_rows[0]["id"]
        access_scope = "category"
        amount = PRICE_CATEGORY_EGP
    else:
        raise HTTPException(status_code=400, detail="Unsupported billing option")

    merchant_order_id = f"{user.id}-{uuid.uuid4().hex[:12]}"
    try:
        auth = _get_auth_token()
        order_id = _create_order(auth, amount, merchant_order_id)
        payment_key = _get_payment_key(auth, order_id, amount, email)
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Paymob error: {e}")

    sb.table("payment_orders").insert({
        "user_id": user.id,
        "email": email,
        "paymob_order_id": str(order_id),
        "merchant_order_id": merchant_order_id,
        "amount_cents": amount,
        "currency": "EGP",
        "status": "pending",
        "billing": billing,
        "access_scope": access_scope,
        "category_id": category_id,
    }).execute()

    payment_url = f"https://accept.paymob.com/api/acceptance/iframes/{IFRAME_ID}?payment_token={payment_key}"
    return {"payment_url": payment_url, "order_id": order_id}


def _verify_hmac(data: dict) -> bool:
    """Verify Paymob HMAC callback signature."""
    if not HMAC_SECRET:
        return False
    fields = [
        "amount_cents", "created_at", "currency", "error_occured",
        "has_parent_transaction", "id", "integration_id", "is_3d_secure",
        "is_auth", "is_capture", "is_refunded", "is_standalone_payment",
        "is_voided", "order", "owner", "pending",
        "source_data_pan", "source_data_sub_type", "source_data_type",
        "success"
    ]
    concat = "".join(str(data.get(f, "")) for f in fields)
    expected = hmac.new(HMAC_SECRET.encode(), concat.encode(), hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, str(data.get("hmac", "")))


def _extract_order_id(order_value) -> str:
    if isinstance(order_value, dict):
        return str(order_value.get("id", ""))
    return str(order_value or "")


@router.post("/webhook")
async def payment_webhook(request: Request):
    """Paymob sends a POST to this endpoint after each transaction."""
    supabase = get_supabase()

    body = await request.json()
    obj = body.get("obj", {})

    if not _verify_hmac({**obj, "hmac": body.get("hmac", "")}):
        raise HTTPException(status_code=400, detail="Invalid HMAC")

    if not obj.get("success"):
        return {"status": "ignored", "reason": "payment not successful"}

    order_id = _extract_order_id(obj.get("order"))
    if not order_id:
        raise HTTPException(status_code=400, detail="Missing order id")

    pending = (
        supabase.table("payment_orders")
        .select("*")
        .eq("paymob_order_id", order_id)
        .limit(1)
        .execute()
    )
    pending_rows = pending.data or []
    if not pending_rows:
        raise HTTPException(status_code=400, detail="Unknown payment order")
    pending_order = pending_rows[0]

    amount = int(obj.get("amount_cents") or 0)
    integration_id = int(obj.get("integration_id") or 0)
    if pending_order.get("status") == "paid":
        return {"status": "ok", "already_paid": True}

    if (
        amount != int(pending_order["amount_cents"])
        or obj.get("currency") != pending_order["currency"]
        or integration_id != INTEGRATION_ID
    ):
        raise HTTPException(status_code=400, detail="Payment verification failed")

    if pending_order.get("access_scope") == "category" and pending_order.get("category_id"):
        supabase.table("user_category_access").upsert({
            "user_id": pending_order["user_id"],
            "category_id": pending_order["category_id"],
            "source": "paymob",
            "status": "active",
            "expires_at": None,
        }, on_conflict="user_id,category_id").execute()
    else:
        # Grant lifetime all access (legacy premium users remain supported).
        supabase.table("profiles").update({
            "plan_type": "premium",
            "subscription_expires_at": None,
            "paymob_order_id": order_id
        }).eq("id", pending_order["user_id"]).execute()

    supabase.table("payment_orders").update({
        "status": "paid",
        "transaction_id": str(obj.get("id", "")),
    }).eq("id", pending_order["id"]).execute()

    return {"status": "ok"}
