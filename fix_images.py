"""
fix_images.py — Verify and fix Supabase Storage image URLs
Run: python fix_images.py
"""
from supabase import create_client

SUPABASE_URL = "https://ukjwbcrbnutxemwsebsc.supabase.co"
SERVICE_KEY  = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVrandiY3JibnV0eGVtd3NlYnNjIiwi"
    "***SERVICE_ROLE_PAYLOAD_REMOVED***"
    "***SERVICE_ROLE_SIG_REMOVED***"
)
BUCKET = "style-images"

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
            print("  → Run upload_styles.py first to upload images")
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
        # Get the public URL via SDK for any storage URL
        # Extract storage path from existing URL if it's a storage URL
        if "/storage/v1/object/public/" in url:
            path = url.split(f"/storage/v1/object/public/{BUCKET}/")[-1]
            # Re-construct URL using SDK method
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

    # Step 4: Print sample URL to test manually
    print("\n[4] Sample URLs to test in browser:")
    if files:
        for f in files[:3]:
            path = f"pastry/{f['name']}"
            url = sb.storage.from_(BUCKET).get_public_url(path)
            print(f"  {url}")

    print("\n" + "─" * 45)
    print("Done!\n")
    print("If images still don't appear, go to:")
    print("Supabase Dashboard → Storage → style-images bucket")
    print("→ Click the three dots (⋮) → Edit bucket → Enable 'Public bucket' → Save\n")

if __name__ == "__main__":
    main()
