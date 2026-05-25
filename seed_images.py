"""
seed_images.py — Seed N high-quality images per category from Pexels,
Unsplash, or Pixabay, generate meta_prompts via Gemini (direct API) or
OpenRouter (cheapest vision model), and insert into the Supabase
ad_styles table.

First --free-count images per category are inserted as is_premium=false,
the rest as is_premium=true.

Image sources (compare)
───────────────────────
  pexels   — 200 req/hour, up to 80 per page.  Best default.
  pixabay  — 100 req/MINUTE, up to 200 per page. Most generous.
  unsplash — 25–50 req/hour on demo. Best curation but slowest.

LLM options for meta_prompt
───────────────────────────
  gemini-direct  — calls Google AI Studio directly. Free tier: 15 RPM,
                   ~1500 req/day on gemini-2.5-flash.
  openrouter     — uses your OpenRouter credit. Default model is
                   google/gemini-2.5-flash-lite (cheapest vision-capable
                   ≈ $0.10/M input, $0.40/M output → ~$1.50 for 1200 images).

Setup
─────
  pip install requests supabase python-dotenv google-generativeai openai

Required env vars (in .env at repo root, or exported):
  SUPABASE_URL              (default: hardcoded project)
  SUPABASE_SERVICE_KEY      (required — never commit!)

  PEXELS_API_KEY            (required if --source pexels)
  PIXABAY_API_KEY           (required if --source pixabay)
  UNSPLASH_ACCESS_KEY       (required if --source unsplash)

  GEMINI_API_KEY            (required if --llm gemini-direct)
  GEMINI_MODEL              (optional, default gemini-2.5-flash)

  OPENROUTER_API_KEY        (required if --llm openrouter)
  OPENROUTER_MODEL          (optional, default google/gemini-2.5-flash-lite)

Usage
─────
  python seed_images.py                                    # pexels + gemini-direct
  python seed_images.py --source pixabay                   # 100 RPM throughput
  python seed_images.py --llm openrouter                   # pay-per-call via OpenRouter
  python seed_images.py --source pixabay --llm openrouter  # max throughput
  python seed_images.py --per-cat 50 --free-count 10
  python seed_images.py --category beauty
  python seed_images.py --skip-prompts                     # insert with stub prompt
  python seed_images.py --dry-run                          # plan only, no DB writes
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

SUPABASE_URL       = os.getenv("SUPABASE_URL", "https://ukjwbcrbnutxemwsebsc.supabase.co")
SERVICE_KEY        = os.getenv("SUPABASE_SERVICE_KEY", "")

PEXELS_KEY         = os.getenv("PEXELS_API_KEY", "")
PIXABAY_KEY        = os.getenv("PIXABAY_API_KEY", "")
UNSPLASH_KEY       = os.getenv("UNSPLASH_ACCESS_KEY", "")

GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL       = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL   = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash-lite")

# Per-LLM throttle (seconds between calls) to stay under free-tier limits.
LLM_SLEEP = {
    "gemini-direct": 4.5,   # 15 RPM safe rate
    "openrouter":    0.5,   # pay-per-call, but be gentle
}

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
#     "tags": [str], "_ping": Callable | None, "_quality": float }
#
# _quality is a relative score used later to put the very best photos in the
# FREE tier and the rest in PREMIUM.

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
            sys.exit("Pexels 429: rate limit. Wait an hour or switch --source pixabay.")
        r.raise_for_status()
        results = r.json().get("photos", [])
        if not results:
            break
        # Pexels orders results by curated relevance; earlier = better.
        base = 100000 - (page - 1) * 100
        for idx, p in enumerate(results):
            photos.append({
                "id":          str(p["id"]),
                "image_url":   p["src"]["large"],
                "alt":         p.get("alt") or "",
                "description": p.get("alt") or None,
                "tags":        [],
                "_ping":       None,
                "_quality":    float(base - idx),
            })
        page += 1
    return photos[:count]


def search_pixabay(query: str, count: int) -> list[dict]:
    photos, page = [], 1
    while len(photos) < count and page <= 10:
        per_page = min(200, count - len(photos))
        if per_page < 3:        # Pixabay requires per_page >= 3
            per_page = 3
        r = requests.get(
            "https://pixabay.com/api/",
            params={
                "key": PIXABAY_KEY,
                "q": query,
                "image_type": "photo",
                "orientation": "all",
                "category": "",
                "min_width": 800,
                "safesearch": "true",
                "per_page": per_page,
                "page": page,
                "order": "popular",
            },
            timeout=20,
        )
        if r.status_code == 429:
            sys.exit("Pixabay 429: rate limit. Wait one minute and re-run.")
        r.raise_for_status()
        data = r.json()
        results = data.get("hits", [])
        if not results:
            break
        for p in results:
            tags_csv = p.get("tags", "")
            likes     = int(p.get("likes", 0) or 0)
            downloads = int(p.get("downloads", 0) or 0)
            views     = int(p.get("views", 0) or 0)
            # Weight: likes count strongest, then downloads, then views.
            quality = likes * 5 + downloads * 1 + views * 0.05
            photos.append({
                "id":          str(p["id"]),
                "image_url":   p.get("largeImageURL") or p.get("webformatURL"),
                "alt":         tags_csv,
                "description": tags_csv or None,
                "tags":        [t.strip() for t in tags_csv.split(",") if t.strip()],
                "_ping":       None,
                "_quality":    float(quality),
            })
        page += 1
        time.sleep(0.6)   # stay well under 100/min
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
                     "Wait an hour, request production access, or switch --source pexels.")
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            break
        for p in results:
            dl_loc = p.get("links", {}).get("download_location")
            ping = (lambda url=dl_loc: _safe_get(url, headers)) if dl_loc else None
            likes = int(p.get("likes", 0) or 0)
            photos.append({
                "id":          p["id"],
                "image_url":   p["urls"]["regular"],
                "alt":         p.get("alt_description") or "",
                "description": p.get("description") or p.get("alt_description"),
                "tags":        [t.get("title", "") for t in p.get("tags", []) if t.get("title")],
                "_ping":       ping,
                "_quality":    float(likes),
            })
        page += 1
    return photos[:count]


def _safe_get(url: str, headers: dict):
    try:
        requests.get(url, headers=headers, timeout=10)
    except Exception:
        pass


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt_instructions(category_name: str, photo: dict) -> str:
    photo_desc = photo.get("description") or photo.get("alt") or "(none)"
    return f"""You are an expert advertising prompt engineer for AI image
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


# ── LLM adapters ─────────────────────────────────────────────────────────────

def _fetch_image_bytes(url: str) -> tuple[bytes, str]:
    r = requests.get(url, timeout=25)
    r.raise_for_status()
    mime = r.headers.get("Content-Type", "image/jpeg").split(";")[0]
    return r.content, mime


def gen_prompt_gemini_direct(category_name: str, photo: dict) -> str:
    import google.generativeai as genai
    img_bytes, mime = _fetch_image_bytes(photo["image_url"])
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    image_part = {"inline_data": {"mime_type": mime,
                                  "data": base64.b64encode(img_bytes).decode()}}
    resp = model.generate_content([build_prompt_instructions(category_name, photo), image_part])
    return resp.text.strip()


def gen_prompt_openrouter(category_name: str, photo: dict) -> str:
    """Use any OpenRouter vision-capable model via the OpenAI-compatible API."""
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("ERROR: openai package not installed. Run: pip install openai")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        default_headers={
            "HTTP-Referer": "https://abdalla-eissa-design.vercel.app",
            "X-Title": "Abdalla Eissa for Design - seeding script",
        },
    )

    img_bytes, mime = _fetch_image_bytes(photo["image_url"])
    b64 = base64.b64encode(img_bytes).decode()
    data_url = f"data:{mime};base64,{b64}"

    resp = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": build_prompt_instructions(category_name, photo)},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        max_tokens=1000,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


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
                     skip_prompts, dry_run, source_fn, llm_fn, llm_sleep):
    print(f"\n📂 {cat['name']} ({cat['slug']})")
    query = SEARCH_MODIFIERS.get(cat["slug"], f"{cat['name']} product photography advertisement")
    print(f"   Query: {query}")

    try:
        photos = source_fn(query, per_cat * 2)
    except Exception as e:
        print(f"   ❌ Source search failed: {e}")
        return 0, 0
    print(f"   {len(photos)} candidates returned")

    # Drop dupes (already in DB) BEFORE sorting so we always pick from
    # fresh candidates only.
    photos = [p for p in photos if p["image_url"] not in existing]

    # Sort by quality DESC so the highest-scored photos take the FREE slots.
    photos.sort(key=lambda p: p.get("_quality", 0.0), reverse=True)
    photos = photos[:per_cat]

    if photos:
        top_q = photos[0].get("_quality", 0.0)
        last_q = photos[-1].get("_quality", 0.0)
        print(f"   Top quality score: {top_q:.0f}   Lowest in batch: {last_q:.0f}")

    inserted, failed = 0, 0
    for idx, photo in enumerate(photos):
        existing.add(photo["image_url"])
        is_premium = idx >= free_count
        tier = "PREM" if is_premium else "FREE"

        if dry_run:
            inserted += 1
            print(f"   [{inserted:3d}/{per_cat}] {tier} (dry-run) "
                  f"q={photo.get('_quality', 0):.0f}  {photo['id']}")
            continue

        try:
            prompt = stub_prompt(cat["name"]) if skip_prompts else llm_fn(cat["name"], photo)
            insert_style(sb, cat, photo, is_premium, prompt)
            if photo.get("_ping"):
                photo["_ping"]()
            inserted += 1
            print(f"   [{inserted:3d}/{per_cat}] {tier} "
                  f"q={photo.get('_quality', 0):.0f}: {photo['id']}")
            if not skip_prompts:
                time.sleep(llm_sleep)
        except Exception as e:
            failed += 1
            err_msg = str(e)
            print(f"   ❌ Failed {photo['id']}: {err_msg[:140]}")
            # Fail fast on Gemini daily-quota exhaustion — no point continuing.
            if "free_tier_requests" in err_msg or "quota_id" in err_msg.lower():
                sys.exit(
                    "\n💥 Gemini free-tier DAILY quota exhausted. Retrying won't help "
                    "until the quota resets (tomorrow PST).\n"
                    "Switch to OpenRouter for unlimited paid calls:\n"
                    "   python seed_images.py --source pixabay --llm openrouter ...\n"
                )

    return inserted, failed


def main():
    p = argparse.ArgumentParser(description="Seed images + meta_prompts.")
    p.add_argument("--source", choices=["pexels", "pixabay", "unsplash"], default="pexels",
                   help="Image source (default: pexels)")
    p.add_argument("--llm", choices=["gemini-direct", "openrouter"], default="gemini-direct",
                   help="Prompt generator (default: gemini-direct)")
    p.add_argument("--per-cat",     type=int, default=100, help="Images per category (default 100)")
    p.add_argument("--free-count",  type=int, default=5,   help="Free images per category (default 5)")
    p.add_argument("--category",    type=str, default=None, help="Only process this category slug")
    p.add_argument("--skip-prompts", action="store_true", help="Insert with stub prompt only")
    p.add_argument("--dry-run",     action="store_true", help="Print plan, no DB writes")
    args = p.parse_args()

    require("SUPABASE_SERVICE_KEY", SERVICE_KEY)

    if args.source == "pexels":
        require("PEXELS_API_KEY", PEXELS_KEY);    source_fn = search_pexels
    elif args.source == "pixabay":
        require("PIXABAY_API_KEY", PIXABAY_KEY);  source_fn = search_pixabay
    else:
        require("UNSPLASH_ACCESS_KEY", UNSPLASH_KEY); source_fn = search_unsplash

    if args.skip_prompts or args.dry_run:
        llm_fn, llm_sleep = (lambda *_: ""), 0.0
    elif args.llm == "openrouter":
        require("OPENROUTER_API_KEY", OPENROUTER_API_KEY)
        llm_fn, llm_sleep = gen_prompt_openrouter, LLM_SLEEP["openrouter"]
    else:
        require("GEMINI_API_KEY", GEMINI_API_KEY)
        llm_fn, llm_sleep = gen_prompt_gemini_direct, LLM_SLEEP["gemini-direct"]

    sb = create_client(SUPABASE_URL, SERVICE_KEY)

    print(f"🌱 Seeding source={args.source} llm={args.llm} "
          f"per_cat={args.per_cat} free={args.free_count} "
          f"category={args.category or 'ALL'} "
          f"skip_prompts={args.skip_prompts} dry_run={args.dry_run}")
    if args.llm == "openrouter" and not args.skip_prompts and not args.dry_run:
        print(f"   OpenRouter model: {OPENROUTER_MODEL}")

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
            source_fn, llm_fn, llm_sleep,
        )
        total_ok += ok
        total_fail += fail

    print(f"\n{'─' * 55}")
    print(f"✅ Inserted: {total_ok}   ❌ Failed: {total_fail}\n")


if __name__ == "__main__":
    main()
