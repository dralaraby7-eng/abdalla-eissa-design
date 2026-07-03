import base64
import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


BACKEND = Path(__file__).resolve().parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from auth_utils import profile_has_premium
from routes.prompts import _catalog_html, _catalog_pdf, _has_style_access, _safe_filename


class AccessTests(unittest.TestCase):
    def setUp(self):
        self.style = {"category_id": "bakery", "is_premium": False}
        self.user = SimpleNamespace(id="user-1")

    def test_anonymous_user_never_receives_full_prompt(self):
        self.assertFalse(_has_style_access(self.style, None, {}, set()))

    def test_legacy_free_flag_does_not_bypass_category_access(self):
        self.assertFalse(_has_style_access(self.style, self.user, {"plan_type": "free"}, set()))

    def test_category_entitlement_grants_prompt_access(self):
        self.assertTrue(_has_style_access(self.style, self.user, {"plan_type": "free"}, {"bakery"}))

    def test_premium_grants_all_access(self):
        profile = {"plan_type": "premium", "subscription_expires_at": None}
        self.assertTrue(profile_has_premium(profile))
        self.assertTrue(_has_style_access(self.style, self.user, profile, set()))


class CatalogSecurityTests(unittest.TestCase):
    def test_catalog_is_self_contained_and_escapes_prompt_html(self):
        rows = [{
            "title": "Style <script>alert(1)</script>",
            "normal_prompt": "Use <img src=x onerror=alert(1)>",
            "json_prompt": '{"product":"<script>"}',
            "image_data_uri": "data:image/png;base64," + base64.b64encode(b"safe-image").decode("ascii"),
        }]
        document, csp = _catalog_html("Bakery", rows)

        self.assertIn("connect-src 'none'", csp)
        self.assertIn("object-src 'none'", csp)
        self.assertNotIn("<script>alert(1)</script>", document)
        self.assertNotIn("<img src=x", document)
        self.assertEqual(set(re.findall(r'data-copy="([^"]+)"', document)), set(re.findall(r'<textarea id="([^"]+)"', document)))
        self.assertNotRegex(document, r'<script\s+src=')

    def test_download_filename_is_sanitized(self):
        self.assertEqual(_safe_filename("../Bakery Products!", "category"), "Bakery-Products")

    def test_pdf_contains_selectable_prompt_document(self):
        png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
        result = _catalog_pdf("Bakery", [{
            "title": "Style 001",
            "normal_prompt": "Use [INPUT_PRODUCT] as the hero product.",
            "json_prompt": '{"product":"INPUT_PRODUCT"}',
            "image_bytes": png,
        }])
        self.assertTrue(result.startswith(b"%PDF-"))
        self.assertGreater(len(result), 1000)


if __name__ == "__main__":
    unittest.main()
