import base64
import hashlib
import html
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import requests
from fastapi import APIRouter, HTTPException, Query, Request
from starlette.responses import Response
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from auth_utils import get_current_user, get_profile, get_supabase, profile_has_premium
from rate_limit import enforce_rate_limit

router = APIRouter(prefix="/api/prompts", tags=["prompts"])
FREE_TEASER_LIMIT = 5


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
    if not user:
        return False
    if profile_has_premium(profile):
        return True
    category_ids = category_ids if category_ids is not None else _user_category_ids(user.id)
    return bool(style.get("category_id") in category_ids)


def _safe_filename(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value or "").strip("-._")
    return cleaned[:100] or fallback


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
    content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
    if content_type not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
        raise ValueError("Image format is not allowed")
    data = bytearray()
    for chunk in response.iter_content(chunk_size=64 * 1024):
        data.extend(chunk)
        if len(data) > 15 * 1024 * 1024:
            raise ValueError("Image is larger than 15 MB")
    return style["id"], bytes(data), content_type


def _catalog_html(category_name: str, rows: list[dict]) -> tuple[str, str]:
    script = """(() => {
  const search = document.getElementById('search');
  const cards = Array.from(document.querySelectorAll('.card'));
  const visibleCount = document.getElementById('visible-count');
  search.addEventListener('input', () => {
    const query = search.value.trim().toLowerCase();
    let visible = 0;
    cards.forEach(card => {
      const match = !query || card.textContent.toLowerCase().includes(query);
      card.hidden = !match;
      if (match) visible += 1;
    });
    visibleCount.textContent = String(visible);
  });
  document.addEventListener('click', async event => {
    const button = event.target.closest('[data-copy]');
    if (!button) return;
    const field = document.getElementById(button.dataset.copy);
    if (!field) return;
    let copied = false;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(field.value);
        copied = true;
      }
    } catch (_) {}
    if (!copied) {
      field.focus();
      field.select();
      field.setSelectionRange(0, field.value.length);
      copied = document.execCommand('copy');
    }
    const original = button.textContent;
    button.textContent = copied ? 'Copied' : 'Select and copy';
    setTimeout(() => { button.textContent = original; }, 1600);
  });
})();"""
    script_hash = base64.b64encode(hashlib.sha256(script.encode("utf-8")).digest()).decode("ascii")
    csp = (
        "default-src 'none'; img-src data:; style-src 'unsafe-inline'; "
        f"script-src 'sha256-{script_hash}'; connect-src 'none'; object-src 'none'; "
        "frame-src 'none'; form-action 'none'; base-uri 'none'"
    )

    cards = []
    for index, row in enumerate(rows, start=1):
        title = html.escape(row["title"])
        normal = html.escape(row.get("normal_prompt") or "")
        json_prompt = html.escape(row.get("json_prompt") or "Not provided")
        image_markup = (
            f'<img loading="lazy" src="{row["image_data_uri"]}" alt="{title}">'
            if row.get("image_data_uri") else '<div class="missing">Image unavailable</div>'
        )
        cards.append(f"""
    <article class="card">
      <div class="visual">{image_markup}<span class="number">{index:03d}</span></div>
      <div class="content">
        <h2>{title}</h2>
        <section class="prompt-section">
          <div class="prompt-heading"><h3>Normal prompt</h3><button type="button" data-copy="normal-{index}">Copy Normal</button></div>
          <textarea id="normal-{index}" readonly spellcheck="false">{normal}</textarea>
        </section>
        <section class="prompt-section">
          <div class="prompt-heading"><h3>JSON prompt</h3><button type="button" data-copy="json-{index}">Copy JSON</button></div>
          <textarea id="json-{index}" readonly spellcheck="false">{json_prompt}</textarea>
        </section>
      </div>
    </article>""")

    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp}"><meta name="referrer" content="no-referrer">
<title>{html.escape(category_name)} Interactive Prompt Catalog</title>
<style>
:root{{--bg:#06111f;--panel:#0d2035;--panel2:#08182a;--line:#24415f;--text:#eaf2ff;--muted:#9bb0c7;--accent:#4da3ff;--success:#28c76f}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:15px Arial,sans-serif;line-height:1.5}}
header{{position:sticky;top:0;z-index:2;background:#071426;border-bottom:1px solid var(--line)}}.header-inner{{max-width:1180px;margin:auto;padding:22px 28px}}
h1{{font-size:26px;margin:0 0 6px}}header p{{margin:0;color:var(--muted)}}.toolbar{{display:flex;align-items:center;gap:14px;margin-top:16px}}
input{{width:100%;max-width:560px;background:var(--panel2);border:1px solid var(--line);border-radius:7px;padding:12px 14px;color:var(--text);font-size:15px}}
.counter{{color:var(--muted);white-space:nowrap}}main{{max-width:1180px;margin:auto;padding:28px}}
.card{{display:grid;grid-template-columns:minmax(280px,36%) 1fr;border:1px solid var(--line);border-radius:8px;overflow:hidden;margin:0 0 26px;background:var(--panel)}}
.visual{{position:relative;background:var(--panel2);min-height:360px}}img,.missing{{width:100%;height:100%;min-height:360px;object-fit:contain;display:flex;align-items:center;justify-content:center;color:var(--muted)}}
.number{{position:absolute;top:12px;left:12px;background:#06111fe6;border:1px solid var(--line);border-radius:5px;padding:5px 8px;font-size:12px}}
.content{{padding:22px;min-width:0}}h2{{margin:0 0 20px;font-size:21px}}.prompt-section{{margin-top:18px}}.prompt-heading{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:7px}}
h3{{margin:0;color:#80bdff;font-size:13px;text-transform:uppercase}}button{{border:1px solid #3478bc;border-radius:6px;background:#123b67;color:#fff;padding:8px 12px;font-weight:700;cursor:pointer}}button:hover{{background:#19528d}}
textarea{{display:block;width:100%;min-height:150px;resize:vertical;background:#05101d;border:1px solid #1d3a57;border-radius:6px;padding:13px;color:#dcecff;font:13px/1.55 Consolas,monospace}}
.security{{margin-top:12px;color:var(--muted);font-size:12px}}[hidden]{{display:none!important}}
@media(max-width:760px){{.header-inner,main{{padding:18px}}.card{{grid-template-columns:1fr}}.visual,img,.missing{{min-height:280px;max-height:440px}}.toolbar{{align-items:stretch;flex-direction:column}}input{{max-width:none}}}}
</style></head><body>
<header><div class="header-inner"><h1>{html.escape(category_name)} Interactive Prompt Catalog</h1>
<p>Each reference image is paired with copy-ready Normal and JSON prompts.</p>
<div class="toolbar"><input id="search" type="search" placeholder="Search styles or prompt text" autocomplete="off"><span class="counter"><span id="visible-count">{len(rows)}</span> of {len(rows)} styles</span></div>
<div class="security">Offline file: no external connections, forms, frames, or remote scripts are allowed.</div></div></header>
<main>{''.join(cards)}</main><script>{script}</script></body></html>"""
    return document, csp


def _catalog_pdf(category_name: str, rows: list[dict]) -> bytes:
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    output = BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title=f"{category_name} Prompt Catalog",
        author="Abdalla Eissa for Design",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("CatalogTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=27, textColor=colors.HexColor("#102A43"), alignment=TA_CENTER, spaceAfter=10)
    subtitle_style = ParagraphStyle("CatalogSubtitle", parent=styles["BodyText"], fontSize=10, leading=14, textColor=colors.HexColor("#486581"), alignment=TA_CENTER)
    item_title = ParagraphStyle("ItemTitle", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=colors.HexColor("#102A43"), spaceAfter=8)
    label_style = ParagraphStyle("Label", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.HexColor("#1473E6"), spaceBefore=4, spaceAfter=4)
    prompt_style = ParagraphStyle("Prompt", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.2, leading=9.6, textColor=colors.HexColor("#243B53"), wordWrap="CJK")
    json_style = ParagraphStyle("JsonPrompt", parent=prompt_style, fontName="Courier", fontSize=6.4, leading=8.2, backColor=colors.HexColor("#F0F4F8"), borderPadding=7)

    def safe_paragraph(value: str) -> str:
        return html.escape(value or "").replace("\n", "<br/>")

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#829AB1"))
        canvas.setFont("Helvetica", 7)
        canvas.drawString(14 * mm, 9 * mm, "Abdalla Eissa for Design - selectable copy-ready prompts")
        canvas.drawRightString(A4[0] - 14 * mm, 9 * mm, f"Page {document.page}")
        canvas.restoreState()

    story = [
        Spacer(1, 20 * mm),
        Paragraph(html.escape(category_name), title_style),
        Paragraph(f"{len(rows)} reference images paired with Normal and JSON prompts", subtitle_style),
        Spacer(1, 8 * mm),
        Paragraph("How to use: choose a reference image, copy its Normal prompt, attach your own product image, then replace the input placeholders.", subtitle_style),
    ]

    for index, row in enumerate(rows, start=1):
        story.append(PageBreak())
        image_flowable = Paragraph("Image unavailable", subtitle_style)
        if row.get("image_bytes"):
            image_buffer = BytesIO(row["image_bytes"])
            reader = ImageReader(image_buffer)
            width, height = reader.getSize()
            scale = min((62 * mm) / width, (62 * mm) / height)
            image_buffer.seek(0)
            image_flowable = Image(image_buffer, width=width * scale, height=height * scale)

        normal_flowables = [
            Paragraph(f"{index:03d} - {html.escape(row['title'])}", item_title),
            Paragraph("NORMAL / META PROMPT", label_style),
            Paragraph(safe_paragraph(row.get("normal_prompt") or "Not provided"), prompt_style),
        ]
        hero = Table([[image_flowable, normal_flowables]], colWidths=[68 * mm, 105 * mm], hAlign="LEFT")
        hero.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#BCCCDC")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9E2EC")),
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#F0F4F8")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.extend([
            hero,
            Spacer(1, 5 * mm),
            Paragraph("JSON PROMPT", label_style),
            Paragraph(safe_paragraph(row.get("json_prompt") or "Not provided"), json_style),
        ])

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()


@router.get("/access")
async def get_access_summary(request: Request):
    """Return a browser-safe summary of the caller's prompt access."""
    user, profile = _current_profile(request)
    if not user:
        return {"all_access": False, "category_ids": [], "categories": []}
    category_ids = sorted(_user_category_ids(user.id))
    categories = []
    if category_ids:
        result = (
            get_supabase().table("categories")
            .select("id, name, slug")
            .in_("id", category_ids)
            .execute()
        )
        categories = result.data or []
    return {
        "all_access": profile_has_premium(profile),
        "category_ids": category_ids,
        "categories": categories,
    }


@router.get("/home")
def get_home_catalog(request: Request):
    """Return category counts and recent teaser styles in one request."""
    enforce_rate_limit(request, "home-catalog", limit=120, window_seconds=60)
    sb = get_supabase()
    categories_result = (
        sb.table("categories")
        .select("id, name, slug, icon, description, display_order")
        .eq("is_active", True)
        .order("display_order")
        .execute()
    )
    styles_result = (
        sb.table("ad_styles")
        .select("id, category_id, title, image_url, prompt_preview, created_at")
        .eq("is_active", True)
        .order("created_at", desc=True)
        .execute()
    )
    styles = styles_result.data or []
    counts = {}
    for style in styles:
        category_id = style.get("category_id")
        counts[category_id] = counts.get(category_id, 0) + 1
    categories = [
        {**category, "style_count": counts.get(category["id"], 0)}
        for category in categories_result.data or []
    ]
    return {"categories": categories, "featured_styles": styles[:8]}


@router.get("/categories/{category_slug}/catalog")
def get_category_catalog(category_slug: str, request: Request):
    """Return five teasers or the complete entitled category catalog."""
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
    user, profile = _current_profile(request)
    category_ids = _user_category_ids(user.id) if user and not profile_has_premium(profile) else set()
    has_access = bool(user and (profile_has_premium(profile) or category["id"] in category_ids))
    styles_result = (
        sb.table("ad_styles")
        .select("id, category_id, title, image_url, tags, is_premium, description, view_count, created_at, prompt_preview")
        .eq("category_id", category["id"])
        .eq("is_active", True)
        .order("created_at", desc=True)
        .execute()
    )
    all_styles = styles_result.data or []
    styles = all_styles if has_access else all_styles[:FREE_TEASER_LIMIT]
    return {
        "category": category,
        "styles": styles,
        "total_styles": len(all_styles),
        "has_access": has_access,
        "is_teaser": not has_access,
        "teaser_limit": FREE_TEASER_LIMIT,
    }


@router.get("/categories/{category_slug}/download")
def download_category(
    category_slug: str,
    request: Request,
    delivery_format: str = Query("pdf", alias="format", pattern="^(pdf|html)$"),
):
    """Build an entitled PDF or self-contained interactive HTML catalog."""
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
        "normal_prompt": style.get("normal_prompt") or style.get("meta_prompt") or "",
        "json_prompt": style.get("json_prompt") or "",
        "image_data_uri": "",
        "image_bytes": b"",
    } for style in styles]

    image_results = {}
    with ThreadPoolExecutor(max_workers=min(8, len(styles))) as executor:
        futures = {executor.submit(_download_image, style): style["id"] for style in styles}
        for future in as_completed(futures):
            style_id = futures[future]
            try:
                _, image_bytes, content_type = future.result()
                image_results[style_id] = (image_bytes, content_type)
            except Exception:
                image_results[style_id] = (None, "")

    for row in rows:
        image_bytes, content_type = image_results.get(row["id"], (None, ""))
        if image_bytes and content_type:
            row["image_bytes"] = image_bytes
            encoded = base64.b64encode(image_bytes).decode("ascii")
            row["image_data_uri"] = f"data:{content_type};base64,{encoded}"

    if delivery_format == "pdf":
        catalog_pdf = _catalog_pdf(category["name"], rows)
        filename = f"{_safe_filename(category['slug'], 'category')}-prompt-catalog.pdf"
        return Response(
            content=catalog_pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "private, no-store",
            },
        )

    catalog, csp = _catalog_html(category["name"], rows)
    filename = f"{_safe_filename(category['slug'], 'category')}-interactive-catalog.html"
    return Response(
        content=catalog.encode("utf-8"),
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Security-Policy": csp,
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "Cache-Control": "private, no-store",
        },
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
