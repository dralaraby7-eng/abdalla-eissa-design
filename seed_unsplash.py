"""
seed_unsplash.py — Seed N images per category from Unsplash, generate
meta_prompts via Gemini, and insert into Supabase ad_styles table.

First --free-count images per category are inserted as is_premium=false,
the rest as is_premium=true.

Setup
─────
  pip install requests supabase python-dotenv google-generativeai

Required env vars (put in .env at repo root or export in shell):
  SUPABASE_URL              (defaults to project URL)
  SUPABASE_SERVICE_KEY      (required — never commit!)
  UNSPLASH_ACCESS_KEY       (required — https://unsplash.com/oauth/applications)
  GEMINI_API_KEY            (required unless --skip-prompts)

Usage
─────
  python seed_unsplash.py                          # all categories, 100 each, 5 free
  python seed_unsplash.py --per-cat 50             # 50 per category
  python seed_unsplash.py --free-count 10          # 10 free per category
  python seed_unsplash.py --category beauty        # only one category by slug
  python seed_unsplash.py --skip-prompts           # insert with stub prompt; fill later via generate_prompts.py
  python seed_unsplash.py --dry-run                # show what would happen, no DB writes

Notes
─────
- Idempotent: photos already in ad_styles (matched by image_url) are skipped.
- Respects Unsplash ToS: pings download_location for each used photo.
- Respects Gemini free-tier rate limit (15 RPM) by sleeping between calls.
"""

import os
import sys
import time
import base64
import argparse
from pathlib import Path
from typing import Optional
import requests
from supabase import create_client

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
    load_dotenv(Path(__file__).parent / "backend" / ".env")
except ImportError:
    pass


# ── Config ────────────────────────────────────────────────────────────────────

SUPABASE_URL   = os.getenv("SUPABASE_URL", "https://ukjwbcrbnutxemwsebsc.supabase.co")
SERVICE_KEY    = os.getenv("SUPABASE_SERVICE_KEY", "")
UNSPLASH_KEY   = os.getenv("UNSPLASH_ACCESS_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

UNSPLASH_BASE = "https://api.unsplash.com"
GEMINI_SLEEP  = 4.5   # 15 RPM safe rate

SEARCH_MODIFIERS = {
    "food":        "food photography advertisement plated",
    "pastry":      "pastry dessert bakery photography",
    "fashion":     "fashion product photography editorial",
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


def insert_style(sb, category, photo, is_premium, meta_prompt):
    raw_title = (photo.get("description")
                 or photo.get("alt_description")
                 or f"{category['name']} Style")
    title = raw_title.strip().capitalize()[:80] or f"{category['name']} Style"
    tags = [t.get("title", "").lower() for t in photo.get("tags", []) if t.get("title")][:8]
    sb.table("ad_styles").insert({
        "category_id": category["id"],
        "title":       title,
        "image_url":   photo["urls"]["regular"],
        "meta_prompt": meta_prompt,
        "description": photo.get("description") or photo.get("alt_description"),
        "tags":        tags,
        "is_premium":  is_premium,
    }).execute()


# ── Unsplash ──────────────────────────────────────────────────────────────────

def search_unsplash(query: str, count: int) -> list:
    """Return up to `count` photo objects from Unsplash search."""
    photos, page = [], 1
    headers = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}
    while len(photos) < count and page <= 10:
        per_page = min(30, count - len(photos))
        r = requests.get(
            f"{UNSPLASH_BASE}/search/photos",
            params={"query": query, "page": page, "per_page": per_page,
                    "orientation": "squarish", "content_filter": "high"},
            headers=headers, timeout=20,
        )
        if r.status_code == 403:
            sys.exit("Unsplash 403: rate limit hit or invalid access key. "
                     "Wait an hour or request production access.")
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            break
        photos.extend(results)
        page += 1
    return photos[:count]


def ping_download(photo):
    """Required by Unsplash ToS when a photo is used."""
    url = photo.get("links", {}).get("download_location")
    if not url:
        return
    try:
        requests.get(url, headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"}, timeout=10)
    except Exception:
        pass


# ── Gemini ────────────────────────────────────────────────────────────────────

def gen_meta_prompt(category_name: str, photo: dict) -> str:
    import google.generativeai as genai

    img_url = photo["urls"]["regular"]
    img_resp = requests.get(img_url, timeout=25)
    img_resp.raise_for_status()
    img_b64 = base64.b64encode(img_resp.content).decode()
    mime = img_resp.headers.get("Content-Type", "image/jpeg").split(";")[0]

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    photo_desc = photo.get("description") or photo.get("alt_description") or "(none)"
    sys_prompt = f"""You are an expert advertising prompt engineer for AI image generation
tools (Midjourney, DALL-E 3, Stable Diffusion, Adobe Firefly).

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

Match the prompt to the exact visual style, lighting, composition, and mood of the supplied image."""

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

def process_category(sb, cat, per_cat, free_count, existing, skip_prompts, dry_run):
    print(f"\n📂 {cat['name']} ({cat['slug']})")
    query = SEARCH_MODIFIERS.get(cat["slug"], f"{cat['name']} product photography advertisement")
    print(f"   Query: {query}")

    try:
        photos = search_unsplash(query, per_cat * 2)
    except Exception as e:
        print(f"   ❌ Unsplash search failed: {e}")
        return 0, 0
    print(f"   {len(photos)} Unsplash candidates returned")

    inserted, failed = 0, 0
    for photo in photos:
        if inserted >= per_cat:
            break
        img_url = photo["urls"]["regular"]
        if img_url in existing:
            continue
        existing.add(img_url)
        is_premium = inserted >= free_count
        tier = "PREM" if is_premium else "FREE"

        if dry_run:
            inserted += 1
            print(f"   [{inserted:3d}/{per_cat}] {tier} (dry-run) {photo['id']}")
            continue

        try:
            prompt = stub_prompt(cat["name"]) if skip_prompts else gen_meta_prompt(cat["name"], photo)
            insert_style(sb, cat, photo, is_premium, prompt)
            ping_download(photo)
            inserted += 1
            print(f"   [{inserted:3d}/{per_cat}] {tier}: {photo['id']}")
            if not skip_prompts:
                time.sleep(GEMINI_SLEEP)
        except Exception as e:
            failed += 1
            print(f"   ❌ Failed {photo['id']}: {e}")

    return inserted, failed


def main():
    p = argparse.ArgumentParser(description="Seed Unsplash images + Gemini prompts.")
    p.add_argument("--per-cat",     type=int, default=100, help="Images per category (default 100)")
    p.add_argument("--free-count",  type=int, default=5,   help="Free images per category (default 5)")
    p.add_argument("--category",    type=str, default=None, help="Only process this category slug")
    p.add_argument("--skip-prompts", action="store_true", help="Insert with stub prompt instead of calling Gemini")
    p.add_argument("--dry-run",     action="store_true", help="Print plan, no DB writes")
    args = p.parse_args()

    require("SUPABASE_SERVICE_KEY", SERVICE_KEY)
    require("UNSPLASH_ACCESS_KEY",  UNSPLASH_KEY)
    if not args.skip_prompts and not args.dry_run:
        require("GEMINI_API_KEY", GEMINI_API_KEY)

    sb = create_client(SUPABASE_URL, SERVICE_KEY)

    print(f"🌱 Seeding: per_cat={args.per_cat}, free_count={args.free_count}, "
          f"category={args.category or 'ALL'}, "
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
            existing, args.skip_prompts, args.dry_run,
        )
        total_ok += ok
        total_fail += fail

    print(f"\n{'─' * 55}")
    print(f"✅ Inserted: {total_ok}   ❌ Failed: {total_fail}")
    free = sum(min(args.free_count, args.per_cat) for _ in cats)
    print(f"   Tier split (target): ~{free} free, ~{total_ok - free} premium\n")


if __name__ == "__main__":
    main()
