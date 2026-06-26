"""
Seed bakery ad styles from bakery_meta_prompts.csv.

By default this clears existing ad_styles rows, then inserts every CSV row as a
Bakery style. It stores CSV image paths as public Supabase Storage URLs under
the style-images bucket, for example:

  BAKERY/example.jpg -> {SUPABASE_URL}/storage/v1/object/public/style-images/BAKERY/example.jpg

Run:
  python seed_bakery_from_csv.py --execute

Useful options:
  python seed_bakery_from_csv.py --dry-run
  python seed_bakery_from_csv.py --execute --clear-scope bakery
  python seed_bakery_from_csv.py --execute --image-base-url https://example.com
"""

from __future__ import annotations

import argparse
import csv
import mimetypes
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv
from supabase import create_client


ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "bakery_meta_prompts.csv"
DEFAULT_BUCKET = "style-images"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "bakery"


def title_from_row(row: dict[str, str]) -> str:
    row_id = (row.get("id") or "").strip()
    return f"Bakery Style {int(row_id):03d}" if row_id.isdigit() else "Bakery Style"


def description_from_prompt(prompt: str) -> str:
    marker = "Photograph DNA:"
    if marker not in prompt:
        return "Premium bakery advertising image style."
    tail = prompt.split(marker, 1)[1].strip()
    first_sentence = tail.split("Design DNA:", 1)[0].strip()
    return first_sentence[:300].rstrip(" ;,.") + "."


def build_image_url(image_path: str, supabase_url: str, bucket: str, image_base_url: str | None) -> str:
    image_path = image_path.strip().replace("\\", "/").lstrip("/")
    if image_path.startswith(("http://", "https://")):
        return image_path
    if image_base_url:
        return f"{image_base_url.rstrip('/')}/{quote(image_path, safe='/')}"
    return f"{supabase_url.rstrip('/')}/storage/v1/object/public/{bucket}/{quote(image_path, safe='/')}"


def local_image_path(image_path: str, image_dir: Path) -> Path | None:
    image_path = image_path.strip().replace("\\", "/").lstrip("/")
    if image_path.startswith(("http://", "https://")):
        return None
    direct = ROOT / image_path
    if direct.exists():
        return direct
    relative_to_dir = image_dir / image_path
    if relative_to_dir.exists():
        return relative_to_dir
    basename_in_dir = image_dir / Path(image_path).name
    if basename_in_dir.exists():
        return basename_in_dir
    return None


def upload_csv_images(sb, rows: list[dict[str, str]], bucket: str, image_dir: Path) -> tuple[int, list[str]]:
    uploaded = 0
    missing: list[str] = []
    for row in rows:
        image_path = (row.get("image") or "").strip().replace("\\", "/").lstrip("/")
        if not image_path or image_path.startswith(("http://", "https://")):
            continue

        source = local_image_path(image_path, image_dir)
        if not source:
            missing.append(image_path)
            continue

        mime = mimetypes.guess_type(source.name)[0] or "image/jpeg"
        with source.open("rb") as f:
            sb.storage.from_(bucket).upload(
                path=image_path,
                file=f,
                file_options={"content-type": mime, "upsert": "true"},
            )
        uploaded += 1
    return uploaded, missing


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        sys.exit(f"CSV not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    required = {"id", "image", "category"}
    missing = required - set(rows[0].keys() if rows else [])
    if missing:
        sys.exit(f"CSV is missing required column(s): {', '.join(sorted(missing))}")
    has_prompt = "meta_prompt" in rows[0] or "normal_prompt" in rows[0]
    if not has_prompt:
        sys.exit("CSV must include either meta_prompt or normal_prompt")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Clear ad_styles and seed Bakery rows from CSV.")
    parser.add_argument("--csv", default=str(CSV_PATH), help="CSV file path")
    parser.add_argument("--bucket", default=os.getenv("SUPABASE_BUCKET", DEFAULT_BUCKET), help="Supabase storage bucket")
    parser.add_argument("--image-base-url", default=os.getenv("BAKERY_IMAGE_BASE_URL"), help="Override base URL for relative CSV image paths")
    parser.add_argument("--image-dir", default=str(ROOT), help="Local folder containing CSV image files")
    parser.add_argument("--skip-upload-images", action="store_true", help="Do not upload local image files to Supabase Storage")
    parser.add_argument("--clear-scope", choices=["all", "bakery"], default="all", help="Rows to delete before inserting")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen without writing")
    parser.add_argument("--execute", action="store_true", help="Required for writes")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    service_key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    if not supabase_url or not service_key:
        sys.exit("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")

    rows = load_rows(Path(args.csv))
    category_name = (rows[0].get("category") or "Bakery").strip()
    category_slug = slugify(category_name)
    if category_slug != "bakery":
        category_slug = "bakery"

    records = []
    for row in rows:
        prompt = (row.get("normal_prompt") or row.get("meta_prompt") or "").strip()
        json_prompt = (row.get("json_prompt") or "").strip()
        image_path = (row.get("image") or "").strip()
        if not prompt or not image_path:
            sys.exit(f"Invalid row {row.get('id')}: image and prompt are required")
        records.append(
            {
                "title": title_from_row(row),
                "image_url": build_image_url(image_path, supabase_url, args.bucket, args.image_base_url),
                "meta_prompt": prompt,
                "normal_prompt": prompt,
                "json_prompt": json_prompt,
                "description": description_from_prompt(prompt),
                "tags": ["bakery", "ad style", "meta prompt"],
                "is_premium": False,
                "is_active": True,
            }
        )

    print(f"CSV rows: {len(records)}")
    print(f"Category: {category_name} ({category_slug})")
    print(f"Clear scope: {args.clear_scope}")
    print(f"Image URL sample: {records[0]['image_url']}")
    local_images = [
        local_image_path((row.get("image") or ""), Path(args.image_dir))
        for row in rows
        if (row.get("image") or "").strip() and not (row.get("image") or "").startswith(("http://", "https://"))
    ]
    local_count = sum(1 for p in local_images if p)
    print(f"Local CSV images found: {local_count}/{len(local_images)}")

    if args.dry_run or not args.execute:
        print("Dry run only. Add --execute to write to Supabase.")
        return 0

    sb = create_client(supabase_url, service_key)

    cat_rows = (
        sb.table("categories")
        .select("id")
        .eq("slug", category_slug)
        .limit(1)
        .execute()
        .data
        or []
    )
    if cat_rows:
        category_id = cat_rows[0]["id"]
        sb.table("categories").update(
            {
                "name": "Bakery Products",
                "icon": "🍞",
                "description": "Fresh bread, baked goods, and bakery promotions",
                "is_active": True,
            }
        ).eq("id", category_id).execute()
    else:
        inserted = (
            sb.table("categories")
            .insert(
                {
                    "name": "Bakery Products",
                    "slug": category_slug,
                    "icon": "🍞",
                    "description": "Fresh bread, baked goods, and bakery promotions",
                    "display_order": 5,
                    "is_active": True,
                }
            )
            .execute()
            .data
        )
        category_id = inserted[0]["id"]

    if args.clear_scope == "all":
        existing_count = sb.table("ad_styles").select("id", count="exact").execute().count or 0
        sb.table("ad_styles").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"Deleted ad_styles rows: {existing_count}")
    else:
        existing_count = (
            sb.table("ad_styles")
            .select("id", count="exact")
            .eq("category_id", category_id)
            .execute()
            .count
            or 0
        )
        sb.table("ad_styles").delete().eq("category_id", category_id).execute()
        print(f"Deleted bakery ad_styles rows: {existing_count}")

    if not args.skip_upload_images and not args.image_base_url:
        uploaded, missing = upload_csv_images(sb, rows, args.bucket, Path(args.image_dir))
        print(f"Uploaded CSV images to storage: {uploaded}")
        if missing:
            print(f"Missing local image files: {len(missing)}")
            print("First missing files:")
            for image_path in missing[:10]:
                print(f"  - {image_path}")

    for record in records:
        record["category_id"] = category_id

    batch_size = 100
    inserted_count = 0
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        inserted = sb.table("ad_styles").insert(batch).execute().data or []
        inserted_count += len(inserted) if inserted else len(batch)

    print(f"Inserted bakery ad_styles rows: {inserted_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
