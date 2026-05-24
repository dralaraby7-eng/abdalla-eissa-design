"""
fix_images.py — Verify and fix Supabase Storage image URLs

Run:
  set SUPABASE_SERVICE_KEY=...        (or put it in .env at repo root)
  python fix_images.py
"""
import os
import sys
from pathlib import Path
from supabase import create_client

# Load .env from repo root if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
    load_dotenv(Path(__file__).parent / "backend" / ".env")
except ImportError:
    pass

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ukjwbcrbnutxemwsebsc.supabase.co")
SERVICE_KEY  = os.getenv("SUPABASE_SERVICE_KEY", "")
BUCKET       = os.getenv("SUPABASE_BUCKET", "style-images")

if not SERVICE_KEY:
    sys.exit(
        "ERROR: SUPABASE_SERVICE_KEY is not set.\n"
        "Set it via env var or .env file. NEVER hardcode it in this file."
    )

sb = create_client(SUPABASE_URL, SERVICE_KEY)


def main():
    print("\n🔧 Fixing Supabase Storage image URLs\n" + "─" * 45)

    # Step 1: Ensure bucket is public
    print("\n[1] Ensuring bucket is public …")
    try:
        sb.storage.update_bucket(BUCKET, options={"public": True})
        print("  ✅ Bucket updated to public")
    except Exception as e:
        print(f"  ℹ️  Note: {e}")

    # Step 2: List files in the bucket
    print("\n[2] Listing files in storage …")
    try:
        files = sb.storage.from_(BUCKET).list("pastry")
        if files:
            print(f"  ✅ Found {len(files)} files in pastry/")
            for f in files:
                print(f"    - pastry/{f['name']}")
        else:
            print("  ⚠️  No files found in pastry/ folder")
    except Exception as e:
        print(f"  ❌ Error listing files: {e}")
        files = []

    # Step 3: Check/fix URLs in ad_styles table
    print("\n[3] Checking image URLs in database …")
    res = sb.table("ad_styles").select("id, title, image_url").execute()
    styles = res.data or []
    print(f"  Found {len(styles)} styles in database")

    fixed = 0
    for style in styles:
        url = style["image_url"]
        if "/storage/v1/object/public/" in url:
            path = url.split(f"/storage/v1/object/public/{BUCKET}/")[-1]
            try:
                public_url = sb.storage.from_(BUCKET).get_public_url(path)
                if public_url != url:
                    sb.table("ad_styles").update({"image_url": public_url}).eq("id", style["id"]).execute()
                    print(f"  🔄 Updated URL for: {style['title']}")
                    fixed += 1
                else:
                    print(f"  ✅ URL OK: {style['title']}")
            except Exception as e:
                print(f"  ⚠️  Could not verify URL for {style['title']}: {e}")
        else:
            print(f"  ℹ️  Non-storage URL (external): {style['title']}")

    print(f"\n  Fixed {fixed} URLs")
    print("\n" + "─" * 45)
    print("Done!\n")


if __name__ == "__main__":
    main()
