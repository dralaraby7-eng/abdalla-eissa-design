import csv
import html
import io
import os
import re
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import requests
from fastapi import APIRouter, HTTPException, Request
from starlette.background import BackgroundTask
from starlette.responses import StreamingResponse
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from auth_utils import get_current_user, get_profile, get_supabase, profile_has_premium
from rate_limit import enforce_rate_limit

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


class PromptBatchRequest(BaseModel):
    style_ids: list[str] = Field(default_factory=list, max_length=200)


def _current_profile(request: Request) -> tuple[object | None, dict]:
    user = get_current_user(request, required=False)
    profile = get_profile(user.id) if user else {}
    return user, profile


def _user_category_ids(user_id: str) -> set[str]:
    result = (
        get_supabase()
        .table("user_category_access")
        .select("category_id, status, expires_at")
        .eq("user_id", user_id)
        .eq("status", "active")
        .execute()
    )
    rows = result.data or []
    active_ids = set()
    now = datetime.now(timezone.utc)
    for row in rows:
        category_id = row.get("category_id")
        if not category_id:
            continue
        expires_at = row.get("expires_at")
        if expires_at:
            try:
                expires = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
                if expires <= now:
                    continue
            except ValueError:
                continue
        active_ids.add(category_id)
    return active_ids


def _has_style_access(style: dict, user, profile: dict, category_ids: set[str] | None = None) -> bool:
    if not style.get("is_premium"):
        return True
    if not user:
        return False
    if profile_has_premium(profile):
        return True
    category_ids = category_ids if category_ids is not None else _user_category_ids(user.id)
    return bool(style.get("category_id") in category_ids)


def _safe_filename(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value or "").strip("-._")
    return cleaned[:100] or fallback


def _image_extension(url: str, content_type: str) -> str:
    content_extensions = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    mime = (content_type or "").split(";", 1)[0].lower()
    if mime in content_extensions:
        return content_extensions[mime]
    suffix = urlparse(url).path.rsplit("/", 1)[-1].lower()
    for extension in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        if suffix.endswith(extension):
            return ".jpg" if extension == ".jpeg" else extension
    return ".jpg"


def _download_image(style: dict) -> tuple[str, bytes, str]:
    url = style.get("image_url") or ""
    parsed = urlparse(url)
    supabase_host = urlparse(os.getenv("SUPABASE_URL", "")).hostname
    extra_hosts = {host.strip().lower() for host in os.getenv("IMAGE_DOWNLOAD_HOSTS", "").split(",") if host.strip()}
    allowed_hosts = extra_hosts | ({supabase_host.lower()} if supabase_host else set())
    if parsed.scheme != "https" or not parsed.hostname or parsed.hostname.lower() not in allowed_hosts:
        raise ValueError("Image host is not allowed")
    response = requests.get(url, timeout=(8, 30), stream=True, allow_redirects=False)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if not content_type.lower().startswith("image/"):
        raise ValueError("Image URL did not return an image")
    data = bytearray()
    for chunk in response.iter_content(chunk_size=64 * 1024):
        data.extend(chunk)
        if len(data) > 15 * 1024 * 1024:
            raise ValueError("Image is larger than 15 MB")
    extension = _image_extension(url, content_type)
    name = _safe_filename(style.get("title") or "", style["id"])
    return style["id"], bytes(data), f"images/{name}-{style['id'][:8]}{extension}"


def _catalog_html(category_name: str, rows: list[dict]) -> str:
    cards = []
    for row in rows:
        image = html.escape(row.get("local_image") or "")
        normal = html.escape(row.get("normal_prompt") or "")
        json_prompt = html.escape(row.get("json_prompt") or "")
        image_markup = (
            f'<img src="{image}" alt="{html.escape(row["title"])}">'
            if image else '<div class="missing">Image unavailable</div>'
        )
        cards.append(f"""
        <article class="card">
          {image_markup}
          <div class="content">
            <h2>{html.escape(row["title"])}</h2>
            <h3>Normal prompt</h3><pre>{normal}</pre>
            <h3>JSON prompt</h3><pre>{json_prompt or "Not provided"}</pre>
          </div>
        </article>""")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(category_name)} Prompt Catalog</title>
<style>
body{{margin:0;background:#071426;color:#eaf2ff;font:15px Arial,sans-serif}}header{{padding:28px;max-width:1100px;margin:auto}}
main{{max-width:1100px;margin:auto;padding:0 28px 40px}}.card{{display:grid;grid-template-columns:300px 1fr;border:1px solid #24415f;border-radius:8px;overflow:hidden;margin:0 0 24px;background:#0d2035}}
img,.missing{{width:100%;height:300px;object-fit:cover;background:#102a45;display:flex;align-items:center;justify-content:center}}.content{{padding:20px}}h1,h2,h3{{margin-top:0}}h3{{color:#70b5ff;font-size:13px;margin:18px 0 6px}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#06111f;padding:14px;border-radius:6px;line-height:1.55;color:#dcecff}}@media(max-width:700px){{.card{{grid-template-columns:1fr}}}}
</style></head><body><header><h1>{html.escape(category_name)} Prompt Catalog</h1><p>{len(rows)} ready-to-use product advertising styles.</p></header><main>{''.join(cards)}</main></body></html>"""


@router.get("/access")
async def get_access_summary(request: Request):
    """Return a browser-safe summary of the caller's prompt access."""
    user, profile = _current_profile(request)
    if not user:
        return {"all_access": False, "category_ids": []}
    return {
        "all_access": profile_has_premium(profile),
        "category_ids": sorted(_user_category_ids(user.id)),
    }


@router.get("/categories/{category_slug}/catalog")
def get_category_catalog(category_slug: str, request: Request):
    """Return public category metadata without exposing full prompt text."""
    enforce_rate_limit(request, "category-catalog", limit=120, window_seconds=60)
    sb = get_supabase()
    category_result = (
        sb.table("categories")
        .select("id, name, slug, icon, description")
        .eq("slug", category_slug)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    categories = category_result.data or []
    if not categories:
        raise HTTPException(status_code=404, detail="Category not found")
    category = categories[0]
    styles_result = (
        sb.table("ad_styles")
        .select("id, category_id, title, image_url, tags, is_premium, description, view_count, created_at, prompt_preview")
        .eq("category_id", category["id"])
        .eq("is_active", True)
        .order("created_at", desc=True)
        .execute()
    )
    return {"category": category, "styles": styles_result.data or []}


@router.get("/categories/{category_slug}/download")
def download_category(category_slug: str, request: Request):
    """Build one offline ZIP containing the category images and prompt catalog."""
    enforce_rate_limit(request, "category-download", limit=3, window_seconds=300)
    sb = get_supabase()
    category_result = (
        sb.table("categories")
        .select("id, name, slug, is_active")
        .eq("slug", category_slug)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    categories = category_result.data or []
    if not categories:
        raise HTTPException(status_code=404, detail="Category not found")
    category = categories[0]

    styles_result = (
        sb.table("ad_styles")
        .select("id, category_id, title, image_url, is_premium, is_active, meta_prompt, normal_prompt, json_prompt")
        .eq("category_id", category["id"])
        .eq("is_active", True)
        .order("title")
        .execute()
    )
    styles = styles_result.data or []
    if not styles:
        raise HTTPException(status_code=404, detail="This category has no active styles")

    user, profile = _current_profile(request)
    category_ids = _user_category_ids(user.id) if user and not profile_has_premium(profile) else set()
    if any(not _has_style_access(style, user, profile, category_ids) for style in styles):
        if not user:
            raise HTTPException(status_code=401, detail="Login and category access are required to download this pack")
        raise HTTPException(status_code=403, detail="Purchase this category or All Access to download the complete pack")

    rows = [{
        "id": style["id"],
        "title": style.get("title") or "Untitled style",
        "image_url": style.get("image_url") or "",
        "normal_prompt": style.get("normal_prompt") or style.get("meta_prompt") or "",
        "json_prompt": style.get("json_prompt") or "",
        "local_image": "",
        "image_status": "not downloaded",
    } for style in styles]

    image_results = {}
    with ThreadPoolExecutor(max_workers=min(8, len(styles))) as executor:
        futures = {executor.submit(_download_image, style): style["id"] for style in styles}
        for future in as_completed(futures):
            style_id = futures[future]
            try:
                _, image_bytes, image_path = future.result()
                image_results[style_id] = (image_bytes, image_path, "downloaded")
            except Exception as exc:
                image_results[style_id] = (None, "", f"failed: {str(exc)[:120]}")

    archive = tempfile.SpooledTemporaryFile(max_size=50 * 1024 * 1024, mode="w+b")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for row in rows:
            image_bytes, image_path, status = image_results.get(row["id"], (None, "", "failed"))
            row["local_image"] = image_path
            row["image_status"] = status
            if image_bytes and image_path:
                bundle.writestr(image_path, image_bytes)

        csv_buffer = io.StringIO(newline="")
        writer = csv.DictWriter(csv_buffer, fieldnames=["id", "title", "image", "normal_prompt", "json_prompt", "category", "image_status"])
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "id": row["id"], "title": row["title"],
                "image": row["local_image"] or row["image_url"],
                "normal_prompt": row["normal_prompt"], "json_prompt": row["json_prompt"],
                "category": category["name"], "image_status": row["image_status"],
            })
        bundle.writestr("prompts.csv", "\ufeff".encode("utf-8") + csv_buffer.getvalue().encode("utf-8"))
        bundle.writestr("catalog.html", _catalog_html(category["name"], rows).encode("utf-8"))
        bundle.writestr("README.txt", (
            f"{category['name']} Prompt Pack\n\n"
            "Open catalog.html in any browser for the visual catalog.\n"
            "Open prompts.csv in Excel or Google Sheets for searchable prompt data.\n"
            "The images folder contains the source style references.\n"
            "Replace the input-product placeholders with your own product details before generation.\n"
        ).encode("utf-8"))

    archive.seek(0)
    filename = f"{_safe_filename(category['slug'], 'category')}-prompt-pack.zip"
    return StreamingResponse(
        archive,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        background=BackgroundTask(archive.close),
    )


@router.get("/{style_id}")
async def get_prompt(style_id: str, request: Request):
    """Return full prompt text only when the caller is allowed to see it."""
    enforce_rate_limit(request, "prompt-single", limit=120, window_seconds=60)
    sb = get_supabase()
    result = (
        sb.table("ad_styles")
        .select("id, category_id, title, is_premium, is_active, meta_prompt, normal_prompt, json_prompt")
        .eq("id", style_id)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Style not found")

    style = rows[0]
    user, profile = _current_profile(request)

    if not style.get("is_active", True) and not profile.get("is_admin"):
        raise HTTPException(status_code=404, detail="Style not found")

    if not _has_style_access(style, user, profile):
        if not user:
            raise HTTPException(status_code=401, detail="Login required")
        raise HTTPException(status_code=403, detail="Category access or All Access required")

    normal_prompt = style.get("normal_prompt") or style.get("meta_prompt") or ""
    json_prompt = style.get("json_prompt") or ""

    return {
        "id": style["id"],
        "title": style.get("title"),
        "prompt": normal_prompt,
        "normal_prompt": normal_prompt,
        "json_prompt": json_prompt,
    }


@router.post("/batch")
async def get_prompts_batch(payload: PromptBatchRequest, request: Request):
    """Return accessible prompts in one request for a smoother gallery."""
    enforce_rate_limit(request, "prompt-batch", limit=30, window_seconds=60)
    style_ids = []
    seen = set()
    for style_id in payload.style_ids:
        if style_id and style_id not in seen:
            style_ids.append(style_id)
            seen.add(style_id)

    if not style_ids:
        return {"prompts": {}}

    sb = get_supabase()
    result = (
        sb.table("ad_styles")
        .select("id, category_id, is_premium, is_active, meta_prompt, normal_prompt, json_prompt")
        .in_("id", style_ids)
        .execute()
    )

    user, profile = _current_profile(request)
    is_admin = bool(profile.get("is_admin"))
    category_ids = _user_category_ids(user.id) if user and not profile_has_premium(profile) else set()

    prompts = {}
    prompt_details = {}
    for style in result.data or []:
        if not style.get("is_active", True) and not is_admin:
            continue
        if not _has_style_access(style, user, profile, category_ids):
            continue
        normal_prompt = style.get("normal_prompt") or style.get("meta_prompt") or ""
        prompts[style["id"]] = normal_prompt
        prompt_details[style["id"]] = {
            "normal_prompt": normal_prompt,
            "json_prompt": style.get("json_prompt") or "",
        }

    return {"prompts": prompts, "prompt_details": prompt_details}
