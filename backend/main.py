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
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Allowed origins (comma-separated in .env)
_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5500")
allowed_origins = [o.strip() for o in _origins_raw.split(",")]

app = FastAPI(
    title="Abdalla Eissa for Design API",
    description="Backend API for payment processing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- Routes -------------------------------------------------
from routes.payments import router as payments_router
app.include_router(payments_router)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "Abdalla Eissa for Design API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
