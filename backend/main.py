"""
Abdalla Eissa for Design — FastAPI Backend
Handles Paymob payment processing (API keys stay server-side).
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

load_dotenv()

# Supabase service-role client (admin access, bypasses RLS)
SUPABASE_URL         = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError(
        "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY. "
        "Set them in Render → Environment (or local .env). See backend/.env.example."
    )
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Allowed origins (comma-separated in env)
_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5500")
allowed_origins = [o.strip() for o in _origins_raw.split(",") if o.strip()]
frontend_url = os.getenv("FRONTEND_URL", "").strip()
if frontend_url and frontend_url not in allowed_origins:
    allowed_origins.append(frontend_url)

app = FastAPI(
    title="Abdalla Eissa for Design API",
    description="Backend API for payment processing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https://[a-z0-9-]+\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- Routes -------------------------------------------------
from routes.payments import router as payments_router
from routes.admin_api import router as admin_router
from routes.prompts import router as prompts_router
app.include_router(payments_router)
app.include_router(admin_router)
app.include_router(prompts_router)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "Abdalla Eissa for Design API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
