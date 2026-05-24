"""
generate_prompts.py — Analyze images with no meta_prompt and generate them via Gemini.

Setup:
  pip install google-generativeai requests supabase python-dotenv

Run:
  set SUPABASE_SERVICE_KEY=...   (or put it in .env at repo root)
  set GEMINI_API_KEY=...
  python generate_prompts.py
"""

import os
import sys
import base64
import time
from pathlib import Path
import requests
from supabase import create_client

# Load .env from repo root and backend/ if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
    load_dotenv(Path(__file__).parent / "backend" / ".env")
except ImportError:
    pass

# ── Config ────────────────────────────────────────────────────────────────────

SUPABASE_URL   = os.getenv("SUPABASE_URL", "https://ukjwbcrbnutxemwsebsc.supabase.co")
SERVICE_KEY    = os.getenv("SUPABASE_SERVICE_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not SERVICE_KEY:
    sys.exit("ERROR: SUPABASE_SERVICE_KEY is not set. Use env or .env file.")
if not GEMINI_API_KEY:
    sys.exit("ERROR: GEMINI_API_KEY is not set. Get one at https://aistudio.google.com/app/apikey")

sb = create_client(SUPABASE_URL, SERVICE_KEY)

# ── Fetch styles with missing prompts ─────────────────────────────────────────

def get_styles_without_prompts():
    res = sb.table("ad_styles").select(
        "id, title, image_url, description, tags, category_id"
    ).or_("meta_prompt.is.null,meta_prompt.eq.").execute()
    return res.data or []


def get_category_name(category_id: str) -> str:
    res = sb.table("categories").select("name, slug").eq("id", category_id).single().execute()
    if res.data:
        return res.data["name"]
    return "General"


# ── Download image → base64 ───────────────────────────────────────────────────

def image_to_base64(url: str) -> tuple[str, str]:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    mime = r.headers.get("Content-Type", "image/jpeg").split(";")[0]
    return base64.b64encode(r.content).decode("utf-8"), mime


# ── Generate prompt via Gemini ────────────────────────────────────────────────

def generate_meta_prompt(title: str, category_name: str, description: str,
                         tags: list, image_b64: str, mime: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))

    tags_str = ", ".join(tags) if tags else "none"

    system_instruction = f"""You are an expert advertising prompt engineer for AI image generation tools
(Midjourney, DALL-E 3, Stable Diffusion, Adobe Firefly).

You will receive an ad style image from the category "{category_name}".
The style title is: "{title}"
Tags: {tags_str}
{"Description: " + description if description else ""}

Your task: Write a professional, detailed AI image generation META PROMPT for this advertising style.

FORMAT RULES:
- Start with a bold description of the shot type in CAPITALS (e.g. "Create a DRAMATIC OVERHEAD FOOD ADVERTISEMENT for [YOUR BRAND].")
- Use [PLACEHOLDER] for any client-specific details (brand name, product name, colors, etc.)
- Include sections for: SUBJECT, LIGHTING, BACKGROUND, MOOD, CAMERA/ANGLE, FORMAT, POST-PROCESSING
- End with: "⚙ Replace every [PLACEHOLDER] with your actual details."
- Length: 250-450 words
- Language: English
- Use clear paragraph breaks between sections

Analyze the image carefully — match the prompt to the exact visual style, lighting, composition, and mood shown."""

    image_part = {"inline_data": {"mime_type": mime, "data": image_b64}}
    response = model.generate_content([system_instruction, image_part])
    return response.text.strip()


# ── Update database ───────────────────────────────────────────────────────────

def save_prompt(style_id: str, prompt: str):
    sb.table("ad_styles").update({"meta_prompt": prompt}).eq("id", style_id).execute()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n🤖 Generating meta prompts for styles with missing prompts\n" + "─" * 55)

    styles = get_styles_without_prompts()
    if not styles:
        print("✅  All styles already have meta prompts. Nothing to do.")
        return

    print(f"Found {len(styles)} style(s) with no meta_prompt.\n")

    ok = failed = 0
    for i, style in enumerate(styles, 1):
        title = style["title"]
        print(f"[{i}/{len(styles)}] {title}")

        try:
            cat_name = get_category_name(style["category_id"])
            b64, mime = image_to_base64(style["image_url"])
            prompt = generate_meta_prompt(
                title=title, category_name=cat_name,
                description=style.get("description") or "",
                tags=style.get("tags") or [],
                image_b64=b64, mime=mime
            )
            save_prompt(style["id"], prompt)
            print(f"         ✅ Saved ({len(prompt)} chars)")
            ok += 1
            # Gemini free tier: 15 RPM. Sleep 4.5s between calls to be safe.
            time.sleep(4.5)

        except Exception as e:
            print(f"         ❌ Failed: {e}")
            failed += 1

    print("─" * 55)
    print(f"Done!  ✅ {ok} generated  |  ❌ {failed} failed\n")


if __name__ == "__main__":
    main()
