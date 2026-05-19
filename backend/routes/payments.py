import os
import hashlib
import hmac
import requests
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/payments", tags=["payments"])

PAYMOB_API_KEY    = os.getenv("PAYMOB_API_KEY")
INTEGRATION_ID    = int(os.getenv("PAYMOB_INTEGRATION_ID", "0"))
IFRAME_ID         = os.getenv("PAYMOB_IFRAME_ID")
HMAC_SECRET       = os.getenv("PAYMOB_HMAC_SECRET", "")
PRICE_MONTHLY     = int(os.getenv("PRICE_MONTHLY_CENTS", "19900"))
PRICE_YEARLY      = int(os.getenv("PRICE_YEARLY_CENTS", "178800"))
FRONTEND_URL      = os.getenv("FRONTEND_URL", "http://localhost:5500")

PAYMOB_BASE = "https://accept.paymob.com/api"


class OrderRequest(BaseModel):
    user_id: str
    email: str
    billing: str = "monthly"   # "monthly" | "yearly"


def _get_auth_token() -> str:
    res = requests.post(f"{PAYMOB_BASE}/auth/tokens", json={"api_key": PAYMOB_API_KEY})
    res.raise_for_status()
    return res.json()["token"]


def _create_order(auth_token: str, amount_cents: int) -> int:
    payload = {
        "auth_token": auth_token,
        "delivery_needed": False,
        "amount_cents": amount_cents,
        "currency": "EGP",
        "items": []
    }
    res = requests.post(f"{PAYMOB_BASE}/ecommerce/orders", json=payload)
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
    res = requests.post(f"{PAYMOB_BASE}/acceptance/payment_keys", json=payload)
    res.raise_for_status()
    return res.json()["token"]


@router.post("/create-order")
async def create_order(body: OrderRequest):
    amount = PRICE_YEARLY if body.billing == "yearly" else PRICE_MONTHLY
    try:
        auth = _get_auth_token()
        order_id = _create_order(auth, amount)
        payment_key = _get_payment_key(auth, order_id, amount, body.email)
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Paymob error: {e}")

    payment_url = f"https://accept.paymob.com/api/acceptance/iframes/{IFRAME_ID}?payment_token={payment_key}"
    return {"payment_url": payment_url, "order_id": order_id}


def _verify_hmac(data: dict) -> bool:
    """Verify Paymob HMAC callback signature."""
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
    return expected == data.get("hmac", "")


@router.post("/webhook")
async def payment_webhook(request: Request):
    """Paymob sends a POST to this endpoint after each transaction."""
    from main import supabase  # imported here to avoid circular import

    body = await request.json()
    obj = body.get("obj", {})

    if not _verify_hmac({**obj, "hmac": body.get("hmac", "")}):
        raise HTTPException(status_code=400, detail="Invalid HMAC")

    if not obj.get("success"):
        return {"status": "ignored", "reason": "payment not successful"}

    # The order's merchant order data should carry user_id — set via metadata
    # For now we match by email stored in billing_data
    email = obj.get("order", {}).get("shipping_data", {}).get("email", "")
    billing = obj.get("amount_cents", PRICE_MONTHLY)
    months = 12 if billing >= PRICE_YEARLY else 1

    expires = datetime.utcnow() + timedelta(days=30 * months)

    # Update user plan via Supabase service key
    result = supabase.table("profiles").update({
        "plan_type": "premium",
        "subscription_expires_at": expires.isoformat(),
        "paymob_order_id": str(obj.get("order", {}).get("id", ""))
    }).eq("id", obj.get("order", {}).get("merchant_order_id", "UNKNOWN")).execute()

    return {"status": "ok"}
