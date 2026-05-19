"""
make_admin.py — Abdalla Eissa for Design
=========================================
- Creates or finds dr.alaraby7@gmail.com in Supabase Auth
- Confirms their email (no email verification step needed)
- Sets is_admin = True in profiles table
- Sets a temporary password (change it after first login)

Run: python make_admin.py
"""

import requests
from supabase import create_client

SUPABASE_URL  = "https://ukjwbcrbnutxemwsebsc.supabase.co"
SERVICE_KEY   = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVrandiY3JibnV0eGVtd3NlYnNjIiwi"
    "***SERVICE_ROLE_PAYLOAD_REMOVED***"
    "***SERVICE_ROLE_SIG_REMOVED***"
)
ADMIN_EMAIL    = "dr.alaraby7@gmail.com"
TEMP_PASSWORD  = "Admin@2024Design"   # User should change this after first login

headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
}
sb = create_client(SUPABASE_URL, SERVICE_KEY)


def find_user(email: str) -> dict | None:
    res = requests.get(
        f"{SUPABASE_URL}/auth/v1/admin/users?per_page=1000",
        headers=headers,
    )
    if res.status_code != 200:
        print(f"  ⚠️  Could not list users: {res.text}")
        return None
    for user in res.json().get("users", []):
        if user.get("email", "").lower() == email.lower():
            return user
    return None


def create_user(email: str, password: str, full_name: str) -> dict:
    res = requests.post(
        f"{SUPABASE_URL}/auth/v1/admin/users",
        headers=headers,
        json={
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"full_name": full_name},
        },
    )
    if res.status_code not in (200, 201):
        raise RuntimeError(f"Failed to create user: {res.text}")
    return res.json()


def confirm_user_email(user_id: str):
    res = requests.put(
        f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}",
        headers=headers,
        json={"email_confirm": True},
    )
    if res.status_code not in (200, 201):
        print(f"  ⚠️  Could not confirm email: {res.text}")


def set_admin_profile(user_id: str, full_name: str):
    existing = sb.table("profiles").select("id").eq("id", user_id).execute()
    if existing.data:
        sb.table("profiles").update({
            "is_admin": True,
            "full_name": full_name,
        }).eq("id", user_id).execute()
        print("  ✅ Profile updated — is_admin = True")
    else:
        sb.table("profiles").insert({
            "id": user_id,
            "full_name": full_name,
            "is_admin": True,
            "plan_type": "premium",
        }).execute()
        print("  ✅ Profile created — is_admin = True, plan = premium")


def main():
    print(f"\n🔐 Setting up admin: {ADMIN_EMAIL}\n" + "─" * 45)

    print("[1/3] Looking up user in Supabase Auth …")
    user = find_user(ADMIN_EMAIL)

    if user:
        uid = user["id"]
        confirmed = bool(user.get("email_confirmed_at"))
        print(f"  Found: id={uid[:8]}…  email_confirmed={confirmed}")
        if not confirmed:
            confirm_user_email(uid)
            print("  ✅ Email confirmed")
    else:
        print(f"  User not found — creating with temp password …")
        user = create_user(ADMIN_EMAIL, TEMP_PASSWORD, "Admin")
        uid = user["id"]
        print(f"  ✅ Created: id={uid[:8]}…  (email already confirmed)")
        print(f"\n  ⚠️  Temporary password: {TEMP_PASSWORD}")
        print("  ⚠️  Please log in and change it from the dashboard!\n")

    print("\n[2/3] Setting admin profile …")
    set_admin_profile(uid, "Admin")

    print("\n[3/3] Verifying …")
    result = sb.table("profiles").select("id, is_admin, plan_type").eq("id", uid).execute()
    if result.data and result.data[0].get("is_admin"):
        print(f"  ✅ Verified: is_admin=True, plan={result.data[0].get('plan_type')}")
    else:
        print("  ❌ Verification failed — check Supabase dashboard manually")

    print("\n" + "─" * 45)
    print(f"✅ Done!  {ADMIN_EMAIL} is now an admin.")
    print(f"   Login at: frontend/auth.html")
    if not find_user(ADMIN_EMAIL) or not user.get("email_confirmed_at"):
        print(f"   Password: {TEMP_PASSWORD}  ← change this after first login\n")


if __name__ == "__main__":
    main()
