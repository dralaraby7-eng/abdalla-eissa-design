"""
seed_images.py — Seed N high-quality images per category from Pexels or
Unsplash, generate meta_prompts via Gemini, and insert into the Supabase
ad_styles table.

First --free-count images per category are inserted as is_premium=false,
the rest as is_premium=true.

Why Pexels by default
─────────────────────
The Unsplash demo tier allows ~25–50 requests/hour. Pexels free tier gives
200 requests/hour AND up to 80 photos per request — meaning a full 100 photo
fetch is just 2 calls per category. Total budget for 12 categories ≈ 24
requests, well under the limit.

Setup
─────
  pip install requests supabase python-dotenv google-generativeai

Required env vars (in .env at repo root, or exported):
  SUPABASE_URL              (default: hardcoded project)
  SUPABASE_SERVICE_KEY      (required — never commit!)
  PEXELS_API_KEY            (required for --source pexels)
  UNSPLASH_ACCESS_KEY       (required for --source unsplash)
  GEMINI_API_KEY            (required unless --skip-prompts)
  GEMINI_MODEL              (optional, default gemini-2.5-flash)

Usage
─────
  python seed_images.py                          # Pexels, 100/cat, 5 free
  python seed_images.py --source unsplash        # use Unsplash instead
  python seed_images.py --per-cat 50             # 50 per category
  python seed_images.py --free-count 10          # 10 free per category
  python seed_images.py --category beauty        # only one category by slug
  python seed_images.py --skip-prompts           # insert with stub prompt
  python seed_images.py --dry-run                # plan only, no DB writes
"""

import os
import sys
import time
import base64
import argparse
from pathlib import Path
from typing import Optional, Callable
import requests
from supabase import create_client

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
    load_dotenv(Path(__file__).parent / "backend" / ".env")
except ImportError:
    pass


# ── Config ────────────────────────────────────────────────────────────────────

SUPABASE_URL    = os.getenv("SUPABASE_URL", "https://ukjwbcrbnutxemwsebsc.supabase.co")
SERVICE_KEY     = os.getenv("SUPABASE_SERVICE_KEY", "")
PEXELS_KEY      = os.getenv("PEXELS_API_KEY", "")
UNSPLASH_KEY    = os.getenv("UNSPLASH_ACCESS_KEY", "")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL    = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

GEMINI_SLEEP    = 4.5   # 15 RPM safe rate

SEARCH_MODIFIERS = {
    "food":        "food photography advertisement plated dish",
    "pastry":      "pastry dessert bakery photography",
    "fashion":     "fashion clothing product photography editorial",
    "tools":       "tools hardware product photography",
    "bakery":      "bakery bread artisan photography",
    "mobiles":     "smartphone product photography studio",
    "beauty":      "cosmetics beauty product photography",
    "realestate":  "real estate interior architecture photography",
    "automotive":  "car automotive product photography studio",
    "health":      "pharmacy health wellness product photography",
    "cafes":       "coffee cafe product photography",
    "electronics": "electronics tech product photography",
}


def require(name: str, value: str):
    if not value:
        sys.exit(f"ERROR: {name} is not set. Put it in .env at repo root or export in shell.")


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_active_categories(sb, only_slug: Optional[str]):
    q = sb.table("categories").select("id, slug, name").eq("is_active", True)
    if only_slug:
        q = q.eq("slug", only_slug)
    return q.order("display_order").execute().data or []


def existing_image_urls(sb) -> set:
    res = sb.table("ad_styles").select("image_url").execute()
    return {row["image_url"] for row in (res.data or [])}


def insert_style(sb, category, photo_record, is_premium, meta_prompt):
    raw_title = (photo_record.get("alt")
                 or photo_record.get("description")
                 or f"{category['name']} Style")
    title = (raw_title or "").strip().capitalize()[:80] or f"{category['name']} Style"
    tags = [t.lower() for t in (photo_record.get("tags") or []) if t][:8]
    sb.table("ad_styles").insert({
        "category_id": category["id"],
        "title":       title,
        "image_url":   photo_record["image_url"],
        "meta_prompt": meta_prompt,
        "description": photo_record.get("description") or photo_record.get("alt"),
        "tags":        tags,
        "is_premium":  is_premium,
    }).execute()


# ── Image-source adapters ─────────────────────────────────────────────────────
# Each adapter returns a list of dicts with a unified shape:
#   { "id": str, "image_url": str, "alt": str, "description": str|None,
#     "tags": [str], "_ping": Callable | None }

def search_pexels(query: str, count: int) -> list[dict]:
    photos, page = [], 1
    headers = {"Authorization": PEXELS_KEY}
    while len(photos) < count and page <= 10:
        per_page = min(80, count - len(photos))
        r = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": per_page, "page": page,
                    "orientation": "square", "size": "large"},
            headers=headers, timeout=20,
        )
        if r.status_code == 429:
            sys.exit("Pexels 429: rate limit. Wait an hour or use --source unsplash.")
        r.raise_for_status()
        results = r.json().get("photos", [])
        if not results:
            break
        for p in results:
            photos.append({
                "id":          str(p["id"]),
                "image_url":   p["src"]["large"],
                "alt":         p.get("alt") or "",
                "description": p.get("alt") or None,
                "tags":        [],   # Pexels doesn't expose tags
                "_ping":       None,
            })
        page += 1
    return photos[:count]


def search_unsplash(query: str, count: int) -> list[dict]:
    photos, page = [], 1
    headers = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}
    while len(photos) < count and page <= 10:
        per_page = min(30, count - len(photos))
        r = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "page": page, "per_page": per_page,
                    "orientation": "squarish", "content_filter": "high"},
            headers=headers, timeout=20,
        )
        if r.status_code == 403:
            sys.exit("Unsplash 403: rate limit hit or invalid key. "
                     "Wait an hour, request production access, or use --source pexels.")
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            break
        for p in results:
            dl_loc = p.get("links", {}).get("download_location")
            ping = (lambda url=dl_loc: _safe_get(url, headers)) if dl_loc else None
            photos.append({
                "id":          p["id"],
                "image_url":   p["urls"]["regular"],
                "alt":         p.get("alt_description") or "",
                "description": p.get("description") or p.get("alt_description"),
                "tags":        [t.get("title", "") for t in p.get("tags", []) if t.get("title")],
                "_ping":       ping,
            })
        page += 1
    return photos[:count]


def _safe_get(url: str, headers: dict):
    try:
        requests.get(url, headers=headers, timeout=10)
    except Exception:
        pass


# ── Gemini ────────────────────────────────────────────────────────────────────

def gen_meta_prompt(category_name: str, photo: dict) -> str:
    import google.generativeai as genai

    img_resp = requests.get(photo["image_url"], timeout=25)
    img_resp.raise_for_status()
    img_b64 = base64.b64encode(img_resp.content).decode()
    mime = img_resp.headers.get("Content-Type", "image/jpeg").split(";")[0]

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    photo_desc = photo.get("description") or photo.get("alt") or "(none)"
    sys_prompt = f"""You are an expert advertising prompt engineer for AI image
generation tools (Midjourney, DALL-E 3, Stable Diffusion, Adobe Firefly).

The image belongs to the category "{category_name}".
Photo description: {photo_desc}

Write a META PROMPT to recreate this exact style as an advertisement for a generic [BRAND].

FORMAT RULES:
- Open line in CAPITALS describing the shot
  (e.g. "Create a BRIGHT OVERHEAD PRODUCT ADVERTISEMENT for [YOUR BRAND].")
- Use [PLACEHOLDER] for any brand/product details
- Include sections: SUBJECT, LIGHTING, BACKGROUND, MOOD, CAMERA/ANGLE, FORMAT, POST-PROCESSING
- End with: "⚙ Replace every [PLACEHOLDER] with your actual details."
- Length: 250-400 words, English, professional tone.

Match the prompt to the exact visual style, lighting, composition, and mood
of the supplied image."""

    image_part = {"inline_data": {"mime_type": mime, "data": img_b64}}
    resp = model.generate_content([sys_prompt, image_part])
    return resp.text.strip()


def stub_prompt(category_name: str) -> str:
    return (
        f"Create a PROFESSIONAL ADVERTISEMENT for [YOUR BRAND] in the {category_name} category.\n\n"
        f"SUBJECT: [YOUR PRODUCT] as the hero\n"
        f"LIGHTING: bright, soft, directional\n"
        f"BACKGROUND: clean studio surface, complementary color\n"
        f"MOOD: aspirational, modern, premium\n"
        f"CAMERA/ANGLE: front, eye-level, shallow depth of field\n"
        f"FORMAT: 1:1 square, 4K\n"
        f"POST-PROCESSING: subtle color grading, slight contrast boost\n\n"
        f"⚙ Replace every [PLACEHOLDER] with your actual details."
    )


# ── Pipeline ─────────────────────────────────────────────────────────────────

def process_category(sb, cat, per_cat, free_count, existing,
                     skip_prompts, dry_run, source_fn: Callable):
    print(f"\n📂 {cat['name']} ({cat['slug']})")
    query = SEARCH_MODIFIERS.get(cat["slug"], f"{cat['name']} product photography advertisement")
    print(f"   Query: {query}")

    try:
        photos = source_fn(query, per_cat * 2)   # over-fetch to skip duplicates
    except Exception as e:
        print(f"   ❌ Source search failed: {e}")
        return 0, 0
    print(f"   {len(photos)} candidates returned")

    inserted, failed = 0, 0
    for photo in photos:
        if inserted >= per_cat:
            break
        if photo["image_url"] in existing:
            continue
        existing.add(photo["image_url"])
        is_premium = inserted >= free_count
        tier = "PREM" if is_premium else "FREE"

        if dry_run:
            inserted += 1
            print(f"   [{inserted:3d}/{per_cat}] {tier} (dry-run) {photo['id']}")
            continue

        try:
            prompt = stub_prompt(cat["name"]) if skip_prompts else gen_meta_prompt(cat["name"], photo)
            insert_style(sb, cat, photo, is_premium, prompt)
            if photo.get("_ping"):
                photo["_ping"]()
            inserted += 1
            print(f"   [{inserted:3d}/{per_cat}] {tier}: {photo['id']}")
            if not skip_prompts:
                time.sleep(GEMINI_SLEEP)
        except Exception as e:
            failed += 1
            print(f"   ❌ Failed {photo['id']}: {e}")

    return inserted, failed


def main():
    p = argparse.ArgumentParser(description="Seed images + Gemini prompts.")
    p.add_argument("--source",      choices=["pexels", "unsplash"], default="pexels",
                   help="Image source (default: pexels)")
    p.add_argument("--per-cat",     type=int, default=100, help="Images per category (default 100)")
    p.add_argument("--free-count",  type=int, default=5,   help="Free images per category (default 5)")
    p.add_argument("--category",    type=str, default=None, help="Only process this category slug")
    p.add_argument("--skip-prompts", action="store_true", help="Insert with stub prompt instead of calling Gemini")
    p.add_argument("--dry-run",     action="store_true", help="Print plan, no DB writes")
    args = p.parse_args()

    require("SUPABASE_SERVICE_KEY", SERVICE_KEY)
    if args.source == "pexels":
        require("PEXELS_API_KEY", PEXELS_KEY)
        source_fn = search_pexels
    else:
        require("UNSPLASH_ACCESS_KEY", UNSPLASH_KEY)
        source_fn = search_unsplash
    if not args.skip_prompts and not args.dry_run:
        require("GEMINI_API_KEY", GEMINI_API_KEY)

    sb = create_client(SUPABASE_URL, SERVICE_KEY)

    print(f"🌱 Seeding from {args.source.upper()}: per_cat={args.per_cat}, "
          f"free_count={args.free_count}, category={args.category or 'ALL'}, "
          f"skip_prompts={args.skip_prompts}, dry_run={args.dry_run}")

    cats = get_active_categories(sb, args.category)
    if not cats:
        sys.exit("No active categories found.")
    print(f"   Categories ({len(cats)}): {', '.join(c['slug'] for c in cats)}")

    existing = existing_image_urls(sb)
    print(f"   {len(existing)} image URLs already in DB will be skipped\n")

    total_ok = total_fail = 0
    for cat in cats:
        ok, fail = process_category(
            sb, cat, args.per_cat, args.free_count,
            existing, args.skip_prompts, args.dry_run, source_fn,
        )
        total_ok += ok
        total_fail += fail

    print(f"\n{'─' * 55}")
    print(f"✅ Inserted: {total_ok}   ❌ Failed: {total_fail}\n")


if __name__ == "__main__":
    main()
