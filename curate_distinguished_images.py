"""
curate_distinguished_images.py

Build a smaller, stronger catalog: over-collect candidates with premium visual
queries, rank them, keep the best 30 per category, and optionally hide old
styles in Supabase.

Typical dry run:
  python curate_distinguished_images.py --source pexels --dry-run

Replace old visible catalog for all categories:
  python curate_distinguished_images.py --source pexels --per-cat 30 --hide-existing

Use AI only for prompt generation on the final selected images:
  python curate_distinguished_images.py --source pexels --llm gemini-direct --per-cat 30 --hide-existing

This script intentionally uses free/low-cost image APIs first. The expensive
step is prompt generation, and it runs only after candidates are narrowed down.
"""

import argparse
import sys
import time
from collections import OrderedDict

from seed_images import (
    SERVICE_KEY,
    SUPABASE_URL,
    PEXELS_KEY,
    PIXABAY_KEY,
    UNSPLASH_KEY,
    GEMINI_API_KEY,
    OPENROUTER_API_KEY,
    LLM_SLEEP,
    gen_prompt_gemini_direct,
    gen_prompt_openrouter,
    get_active_categories,
    insert_style,
    require,
    search_pexels,
    search_pixabay,
    search_unsplash,
    stub_prompt,
)
from supabase import create_client


# Each list is deliberately style-led, not object-led. Broad searches like
# "food photography" produce generic stock. These queries hunt for ads users
# will want to imitate.
STYLE_HUNTS = {
    "food": [
        "award winning restaurant food advertising hero shot",
        "fine dining plate dramatic lighting food photography",
        "gourmet burger splash sauce commercial photography",
        "overhead colorful food bowl premium advertisement",
        "dessert restaurant dark moody hero shot",
        "fresh drink splash food commercial photography",
    ],
    "pastry": [
        "luxury pastry advertisement macro photography",
        "croissant bakery editorial hero shot",
        "cake slice dramatic studio food photography",
        "chocolate dessert splash commercial photography",
        "artisan bakery flat lay premium photography",
        "macaron pastel luxury dessert advertising",
    ],
    "fashion": [
        "high fashion editorial campaign street style",
        "luxury clothing lookbook studio photography",
        "fashion flat lay colorful editorial advertisement",
        "model wearing outfit golden hour campaign",
        "streetwear product photography dramatic lighting",
        "premium accessories fashion editorial still life",
    ],
    "tools": [
        "power tools dramatic product advertising photography",
        "industrial tools flat lay dark background",
        "craftsman using tool sparks dramatic lighting",
        "hardware store premium tool product shot",
        "workshop action photo professional tools",
        "construction tools hero shot commercial photography",
    ],
    "bakery": [
        "artisan bread bakery advertisement photography",
        "fresh bread flour dust cinematic bakery",
        "sourdough loaf rustic premium hero shot",
        "bakery product flat lay commercial photography",
        "bread basket warm window light advertisement",
        "croissant pastry bakery luxury product shot",
    ],
    "mobiles": [
        "smartphone product advertising dramatic lighting",
        "phone in hand lifestyle app commercial photography",
        "mobile phone clean studio hero shot",
        "smartphone neon tech product photography",
        "premium device mockup lifestyle photography",
        "tablet smartphone flat lay modern tech ad",
    ],
    "beauty": [
        "luxury skincare product advertising photography",
        "cosmetics product splash studio photography",
        "makeup beauty campaign editorial portrait",
        "perfume bottle luxury still life advertisement",
        "clean beauty product lineup marble photography",
        "serum bottle premium cosmetic hero shot",
    ],
    "realestate": [
        "luxury real estate interior photography",
        "modern villa exterior golden hour architecture",
        "premium apartment interior design photography",
        "real estate living room editorial wide angle",
        "hotel suite luxury interior advertisement",
        "modern kitchen architecture magazine photography",
    ],
    "automotive": [
        "luxury car studio advertising dramatic lighting",
        "sports car motion blur commercial photography",
        "automotive detail macro premium photography",
        "car interior luxury editorial photography",
        "electric car hero shot city night neon",
        "SUV adventure road commercial photography",
    ],
    "health": [
        "supplement product advertising clean studio",
        "wellness lifestyle commercial photography",
        "pharmacy product clean medical advertisement",
        "vitamin bottle natural ingredients photography",
        "healthcare wellness premium product shot",
        "fitness recovery product lifestyle advertisement",
    ],
    "cafes": [
        "coffee advertising photography latte art premium",
        "iced coffee splash commercial photography",
        "cafe lifestyle warm editorial photography",
        "coffee beans product hero shot dramatic lighting",
        "espresso machine cafe advertisement photography",
        "takeaway coffee cup branded lifestyle shot",
    ],
    "electronics": [
        "premium laptop product advertising photography",
        "gaming setup RGB commercial photography",
        "headphones product hero shot dramatic lighting",
        "smart home device lifestyle advertisement",
        "electronics flat lay modern product photography",
        "tech gadget neon studio photography",
    ],
}

BAD_TERMS = {
    "cartoon", "illustration", "vector", "clipart", "logo", "text", "meme",
    "low quality", "isolated on white", "transparent",
}

GOOD_TERMS = {
    "advertising", "advertisement", "commercial", "campaign", "premium",
    "luxury", "dramatic", "editorial", "studio", "hero", "cinematic",
    "product", "lifestyle", "macro", "splash",
}


def source_functions(name: str):
    if name == "pexels":
        require("PEXELS_API_KEY", PEXELS_KEY)
        return [("pexels", search_pexels)]
    if name == "pixabay":
        require("PIXABAY_API_KEY", PIXABAY_KEY)
        return [("pixabay", search_pixabay)]
    if name == "unsplash":
        require("UNSPLASH_ACCESS_KEY", UNSPLASH_KEY)
        return [("unsplash", search_unsplash)]

    functions = []
    if PEXELS_KEY:
        functions.append(("pexels", search_pexels))
    if PIXABAY_KEY:
        functions.append(("pixabay", search_pixabay))
    if UNSPLASH_KEY:
        functions.append(("unsplash", search_unsplash))
    if not functions:
        sys.exit("Set at least one image API key for --source multi.")
    return functions


def choose_llm(name: str, skip_prompts: bool):
    if skip_prompts:
        return None, 0.0
    if name == "openrouter":
        require("OPENROUTER_API_KEY", OPENROUTER_API_KEY)
        return gen_prompt_openrouter, LLM_SLEEP["openrouter"]
    require("GEMINI_API_KEY", GEMINI_API_KEY)
    return gen_prompt_gemini_direct, LLM_SLEEP["gemini-direct"]


def collect_candidates(category_slug: str, source_name: str, oversample: int) -> list[dict]:
    hunts = STYLE_HUNTS.get(category_slug, [f"{category_slug} premium advertising photography"])
    per_query = max(12, oversample // max(1, len(hunts)))
    candidates = OrderedDict()

    for query_index, query in enumerate(hunts):
        for provider_name, fn in source_functions(source_name):
            try:
                photos = fn(query, per_query)
            except Exception as exc:
                print(f"   Source failed {provider_name}: {str(exc)[:120]}")
                continue

            for rank, photo in enumerate(photos):
                key = photo["image_url"]
                if key in candidates:
                    continue
                photo["_provider"] = provider_name
                photo["_query"] = query
                photo["_query_rank"] = rank
                photo["_query_boost"] = max(0, 40 - query_index * 4)
                candidates[key] = photo
    return list(candidates.values())


def score_candidate(photo: dict) -> float:
    text = " ".join([
        str(photo.get("alt") or ""),
        str(photo.get("description") or ""),
        " ".join(photo.get("tags") or []),
        str(photo.get("_query") or ""),
    ]).lower()

    score = float(photo.get("_quality") or 0)
    # Compress huge provider-specific popularity scores so one source does not
    # dominate solely by scale.
    if score > 1000:
        score = 1000 + (score - 1000) ** 0.5

    score += float(photo.get("_query_boost") or 0)
    score -= float(photo.get("_query_rank") or 0) * 1.5

    for term in GOOD_TERMS:
        if term in text:
            score += 25
    for term in BAD_TERMS:
        if term in text:
            score -= 150

    # Prefer sources by likely visual curation, not legality or cost.
    provider = photo.get("_provider")
    if provider == "unsplash":
        score += 35
    elif provider == "pexels":
        score += 20

    return score


def hide_existing_styles(sb, category_id: str, dry_run: bool):
    if dry_run:
        print("   Would hide existing active styles")
        return
    sb.table("ad_styles").update({"is_active": False}).eq("category_id", category_id).execute()


def active_style_count(sb, category_id: str) -> int:
    result = (
        sb.table("ad_styles")
        .select("id")
        .eq("category_id", category_id)
        .eq("is_active", True)
        .execute()
    )
    return len(result.data or [])


def existing_style_urls(sb, category_id: str) -> set[str]:
    result = sb.table("ad_styles").select("image_url").eq("category_id", category_id).execute()
    return {row["image_url"] for row in (result.data or []) if row.get("image_url")}


def generate_prompt_with_retry(llm_fn, category_name: str, photo: dict, retries: int = 2) -> str:
    last_error = None
    for attempt in range(retries + 1):
        try:
            return llm_fn(category_name, photo)
        except Exception as exc:
            last_error = exc
            msg = str(exc).lower()
            if "quota" in msg or "resource_exhausted" in msg or "free_tier_requests" in msg:
                raise
            if attempt < retries:
                time.sleep(5 * (attempt + 1))
    raise last_error


def insert_selected(sb, category, photos, llm_fn, llm_sleep, free_count, dry_run):
    inserted = 0
    failed = 0
    for index, photo in enumerate(photos):
        is_premium = index >= free_count
        tier = "PREM" if is_premium else "FREE"
        if dry_run:
            print(
                f"   [{index + 1:02d}] {tier} score={photo['_final_score']:.1f} "
                f"{photo['_provider']} - {photo.get('alt') or photo['id']}"
            )
            continue

        try:
            prompt = (
                generate_prompt_with_retry(llm_fn, category["name"], photo)
                if llm_fn else stub_prompt(category["name"])
            )
            insert_style(sb, category, photo, is_premium, prompt)
            inserted += 1
            print(f"   Inserted {index + 1:02d}/{len(photos)} {tier}: {photo['id']}")
            if llm_fn:
                time.sleep(llm_sleep)
        except Exception as exc:
            failed += 1
            msg = str(exc)
            print(f"   Failed {index + 1:02d}/{len(photos)} {tier}: {photo['id']} - {msg[:180]}")
            if "quota" in msg.lower() or "resource_exhausted" in msg.lower():
                print("   Gemini quota/rate limit reached. Stop now and resume later, or use --llm openrouter.")
                break
    return inserted, failed


def main():
    parser = argparse.ArgumentParser(description="Curate distinguished premium images.")
    parser.add_argument("--source", choices=["pexels", "pixabay", "unsplash", "multi"], default="pexels")
    parser.add_argument("--llm", choices=["gemini-direct", "openrouter"], default="gemini-direct")
    parser.add_argument("--per-cat", type=int, default=30)
    parser.add_argument("--free-count", type=int, default=5)
    parser.add_argument("--oversample", type=int, default=240)
    parser.add_argument("--category", default=None, help="Only process one category slug")
    parser.add_argument("--hide-existing", action="store_true", help="Set old styles is_active=false")
    parser.add_argument("--skip-prompts", action="store_true", help="Use stub prompts")
    parser.add_argument("--dry-run", action="store_true", help="No database writes")
    args = parser.parse_args()

    require("SUPABASE_SERVICE_KEY", SERVICE_KEY)
    llm_fn, llm_sleep = choose_llm(args.llm, args.skip_prompts or args.dry_run)
    sb = create_client(SUPABASE_URL, SERVICE_KEY)

    categories = get_active_categories(sb, args.category)
    if not categories:
        sys.exit("No categories found.")

    print(
        f"Curating source={args.source} per_cat={args.per_cat} "
        f"oversample={args.oversample} hide_existing={args.hide_existing} "
        f"dry_run={args.dry_run}"
    )

    total = 0
    total_failed = 0
    for category in categories:
        print(f"\nCategory: {category['name']} ({category['slug']})")
        active_count = 0 if args.hide_existing else active_style_count(sb, category["id"])
        needed = max(0, args.per_cat - active_count)
        if needed == 0:
            print(f"   Already has {active_count} active styles. Skipping.")
            continue

        candidates = collect_candidates(category["slug"], args.source, args.oversample)
        if not candidates:
            print("   No candidates found")
            continue

        existing_urls = existing_style_urls(sb, category["id"])
        candidates = [photo for photo in candidates if photo["image_url"] not in existing_urls]

        for photo in candidates:
            photo["_final_score"] = score_candidate(photo)

        selected = sorted(candidates, key=lambda p: p["_final_score"], reverse=True)[:needed]
        print(
            f"   Active now: {active_count}  Need: {needed}  "
            f"Candidates: {len(candidates)}  Selected: {len(selected)}"
        )

        if args.hide_existing:
            hide_existing_styles(sb, category["id"], args.dry_run)

        inserted, failed = insert_selected(sb, category, selected, llm_fn, llm_sleep, args.free_count, args.dry_run)
        total += inserted
        total_failed += failed

    print(f"\nDone. Inserted {total} styles. Failed {total_failed}.")


if __name__ == "__main__":
    main()
