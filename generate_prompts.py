"""
generate_prompts.py — Analyze images with no meta_prompt and generate them via Gemini.

Setup:
  pip install google-generativeai requests supabase python-dotenv

Run:
  python generate_prompts.py
"""

import os
import sys
import base64
import requests
from supabase import create_client

# ── Config ────────────────────────────────────────────────────────────────────

SUPABASE_URL = "https://ukjwbcrbnutxemwsebsc.supabase.co"
SERVICE_KEY  = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVrandiY3JibnV0eGVtd3NlYnNjIiwi"
    "***SERVICE_ROLE_PAYLOAD_REMOVED***"
    "***SERVICE_ROLE_SIG_REMOVED***"
)

# Your Google AI Studio / Gemini API key
# Get it from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

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
    """Returns (base64_data, mime_type)"""
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        mime = r.headers.get("Content-Type", "image/jpeg").split(";")[0]
        return base64.b64encode(r.content).decode("utf-8"), mime
    except Exception as e:
        raise RuntimeError(f"Failed to download image: {e}")

# ── Generate prompt via Gemini ────────────────────────────────────────────────

def generate_meta_prompt(title: str, category_name: str, description: str,
                          tags: list, image_b64: str, mime: str) -> str:
    try:
        import google.generativeai as genai
    except ImportError:
        print("❌  google-generativeai is not installed.")
        print("    Run: pip install google-generativeai")
        sys.exit(1)

    if not GEMINI_API_KEY:
        print("❌  GEMINI_API_KEY is not set.")
        print("    Set it: set GEMINI_API_KEY=your_key_here  (or add to .env)")
        sys.exit(1)

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

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
        print(f"[{i}/{len(styles)}] Processing: {title}")

        try:
            cat_name = get_category_name(style["category_id"])
            print(f"         Category: {cat_name}")
            print(f"         Downloading image…")
            b64, mime = image_to_base64(style["image_url"])

            print(f"         Generating prompt with Gemini…")
            prompt = generate_meta_prompt(
                title       = title,
                category_name = cat_name,
                description = style.get("description") or "",
                tags        = style.get("tags") or [],
                image_b64   = b64,
                mime        = mime
            )

            save_prompt(style["id"], prompt)
            print(f"         ✅ Saved ({len(prompt)} chars)\n")
            ok += 1

        except Exception as e:
            print(f"         ❌ Failed: {e}\n")
            failed += 1

    print("─" * 55)
    print(f"Done!  ✅ {ok} generated  |  ❌ {failed} failed\n")

if __name__ == "__main__":
    main()
