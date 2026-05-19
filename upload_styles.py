"""
upload_styles.py — Abdalla Eissa for Design
=============================================
1. Creates 'style-images' bucket in Supabase Storage (if missing)
2. Seeds categories table (if empty)
3. Uploads all 11 images from /images folder
4. Inserts ad_styles rows with full meta prompts

Run from project root:
    pip install supabase
    python upload_styles.py
"""

import os, sys, time
from pathlib import Path
from supabase import create_client, Client

# ─── Config ────────────────────────────────────────────────
SUPABASE_URL = "https://ukjwbcrbnutxemwsebsc.supabase.co"
SERVICE_KEY  = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVrandiY3JibnV0eGVtd3NlYnNjIiwi"
    "***SERVICE_ROLE_PAYLOAD_REMOVED***"
    "***SERVICE_ROLE_SIG_REMOVED***"
)
BUCKET     = "style-images"
IMAGES_DIR = Path(__file__).parent / "images"

sb: Client = create_client(SUPABASE_URL, SERVICE_KEY)

# ─── Style definitions ─────────────────────────────────────
# Each entry maps to one image file.
# category_slug must match a slug in the categories table.

STYLES = [
    # ── 1 ──────────────────────────────────────────────────
    {
        "file": "WhatsApp Image 2026-05-18 at 8.35.37 PM.jpeg",
        "storage_name": "pastry-raspberry-dust-explosion.jpg",
        "category_slug": "pastry",
        "title": "Raspberry Dust Explosion — Croissant Close-Up",
        "description": "Dramatic close-up of a golden croissant covered in freeze-dried raspberry powder and pink glaze drizzles, surrounded by scattered fresh raspberries with powder particles frozen in mid-air against a dark stone surface.",
        "tags": ["explosion", "croissant", "raspberry", "close-up", "dark background"],
        "is_premium": False,
        "meta_prompt": """\
Create a premium commercial food advertisement photo of [YOUR PASTRY — e.g., croissant / macaron / cake slice] in the EXPLOSIVE INGREDIENT photography style.

SUBJECT: [YOUR PASTRY] photographed up close, generously dusted/coated with [YOUR KEY INGREDIENT — e.g., freeze-dried raspberry powder / matcha / crushed pistachios / cacao]. Add thin [COLOR] glaze lines drizzled diagonally across the product surface.

FLYING ELEMENTS: Scatter fresh [YOUR FRUIT or INGREDIENT — e.g., raspberries / strawberries / pistachios] randomly in mid-air at varying distances. Fine [COLOR] dust particles exploding upward around the subject — some sharp, some softly blurred.

BACKGROUND: Dark charcoal-grey or cool slate stone surface, matte and slightly textured. Background slightly blurred (f/2.8–f/4 depth of field).

LIGHTING: Strong directional side-light from the left — sharp highlight lines along each pastry layer, specular sparkle on glaze drips. Subtle rim light on the far edge of the product. No fill light (keep shadows deep).

COLOR PALETTE: Vivid [MAIN INGREDIENT COLOR] against dark grey — maximum contrast, rich and saturated. Glaze reflects [COMPLEMENTARY COLOR] highlights.

CAMERA ANGLE: Extreme low-angle hero shot, camera almost at surface level, product tilted 25–30° toward the viewer.

MOOD: Explosive, premium, artisan, editorial food magazine cover quality.

FORMAT: Vertical portrait 9:16 — optimized for Instagram Stories and Reels cover thumbnail.

POST-PROCESSING: Maximum sharpness on pastry texture, rich color grading, slight dark vignette on corners, micro-contrast boost.

⚙ Replace every [PLACEHOLDER] with your actual product, ingredient, and color details before generating.""",
    },

    # ── 2 ──────────────────────────────────────────────────
    {
        "file": "WhatsApp Image 2026-05-18 at 8.35.37 PM (1).jpeg",
        "storage_name": "bakery-artisan-flatlay-poster.jpg",
        "category_slug": "bakery",
        "title": "Artisan Bakery — Elegant Flat Lay Poster Ad",
        "description": "Sophisticated editorial-style bakery poster featuring multiple premium pastries on ceramic cake stands and plates, arranged on a warm beige surface with soft natural lighting and elegant serif typography.",
        "tags": ["flat lay", "bakery", "elegant", "warm tones", "poster", "editorial"],
        "is_premium": True,
        "meta_prompt": """\
Create a high-end editorial BAKERY POSTER advertisement in the warm artisan flat-lay style.

LAYOUT: Full-page vertical poster. Top third: large elegant serif headline text "[YOUR BAKERY NAME]" in dark brown on a warm beige background. Main body: styled flat-lay product photo.

PRODUCTS: Arrange 4–6 of [YOUR BAKED GOODS — e.g., choux puffs / mille-feuille / tarts / croissants] on different ceramic cake stands and plates of varying heights. Add supporting elements: a small bowl of [SAUCE or DIP], scattered [NUTS or GARNISH], a linen napkin folded casually to one side.

BACKGROUND: Warm beige or cream plaster/concrete surface. Even, soft shadows. No harsh lines.

LIGHTING: Soft diffused overhead natural light (window light from the left). Low contrast, no harsh shadows. Everything evenly lit and warm.

COLOR PALETTE: Warm caramels, creamy whites, sandy beige, touches of chocolate brown. Monochromatic warm neutrals throughout.

TYPOGRAPHY (text overlay):
• Large: "[YOUR BAKERY NAME]" — elegant serif, uppercase, dark brown
• Small caption rows at bottom: "[TAGLINE 1]" · "[TAGLINE 2]" · "[TAGLINE 3]"
• Add small label: "Estd. [YEAR]" near the main title

MOOD: Premium, artisan, warm, inviting, Parisian patisserie quality.

FORMAT: Portrait A3 poster ratio (1:√2) or 4:5 for Instagram feed.

POST-PROCESSING: Warm color grade (add slight golden-yellow tint to shadows), very gentle grain for film feel, soft overall contrast.

⚙ Replace every [PLACEHOLDER] with your actual bakery name, products, and taglines.""",
    },

    # ── 3 ──────────────────────────────────────────────────
    {
        "file": "WhatsApp Image 2026-05-18 at 8.35.37 PM (2).jpeg",
        "storage_name": "pastry-cream-whip-explosion-dark.jpg",
        "category_slug": "pastry",
        "title": "Cream Whip Explosion — Dark Dramatic Croissant",
        "description": "Spectacular action shot of a croissant bursting with whipped cream topping, surrounded by flying crumbs and milk splash on a rich dark chocolate-brown background.",
        "tags": ["explosion", "croissant", "cream", "dark background", "dramatic", "action"],
        "is_premium": False,
        "meta_prompt": """\
Create a dramatic high-speed ACTION EXPLOSION food advertisement photo of [YOUR PASTRY PRODUCT].

SUBJECT: [YOUR PASTRY — e.g., croissant / brioche / donut] mid-explosion, topped with a generous swirl of [YOUR TOPPING — e.g., whipped cream / soft-serve / mascarpone]. The pastry is frozen in a dynamic floating/spinning position.

EXPLOSION ELEMENTS: Chunks and flakes of [PASTRY MATERIAL — e.g., croissant flakes / cookie crumbles / puff pastry shards] flying outward in all directions. [LIQUID — e.g., cream / milk / caramel] splashing from below in a dynamic arc. Fine [POWDER — e.g., powdered sugar / cocoa / cinnamon] mist in the air.

BACKGROUND: Deep warm [DARK COLOR — e.g., chocolate brown / espresso / midnight blue] gradient from dark center to slightly lighter edges. No surface — product floats in mid-air.

LIGHTING: Single dramatic spotlight from directly above or slightly in front — extreme contrast. Hard light creates deep shadows between pastry layers, brilliant white highlights on cream topping. Backlight rim glow separates the product from background.

COLOR PALETTE: Rich warm [PASTRY GOLD/BROWN] against deep [BACKGROUND COLOR]. Cream white as contrast anchor. High contrast.

CAMERA ANGLE: Low-angle front shot, product at eye level, slight upward tilt showing the cream topping dramatically.

MOOD: High-energy, explosive, indulgent, premium fast-food/bakery advertising energy.

FORMAT: Vertical portrait 9:16, ideal for Instagram Stories, Reels, TikTok.

POST-PROCESSING: Very high sharpness and micro-contrast, dramatic tone curve (crushed blacks, bright highlights), warm color grade.

⚙ Replace every [PLACEHOLDER] with your actual product, topping, and color details.""",
    },

    # ── 4 ──────────────────────────────────────────────────
    {
        "file": "WhatsApp Image 2026-05-18 at 8.35.38 PM.jpeg",
        "storage_name": "pastry-chocolate-donuts-falling.jpg",
        "category_slug": "pastry",
        "title": "Chocolate Rain — Falling Donuts Dark Style",
        "description": "Moody close-up of chocolate-drizzled donuts caught mid-fall in a cascade, with chocolate powder particles and crumbs exploding outward against a deep chocolate-brown background.",
        "tags": ["donuts", "chocolate", "falling", "motion", "dark", "moody"],
        "is_premium": False,
        "meta_prompt": """\
Create a dramatic FALLING CASCADE food advertisement photo of [YOUR ROUND PASTRY — e.g., donuts / macarons / puff balls] in a dark chocolate moody style.

SUBJECT: 3–4 [YOUR PRODUCTS] caught mid-fall in a cascading stacked arrangement — top one slightly tilted, others below progressively more level. Each product is generously drizzled with [YOUR SAUCE — e.g., dark chocolate / caramel / white chocolate] in irregular diagonal streaks. Surface of products dusted with [YOUR TOPPING — e.g., cacao powder / cinnamon / crushed nuts].

FALLING PHYSICS: Products appear to be genuinely falling — natural motion blur on the top item, sharper on lower ones. Surrounding air: fine [COLOR] dust/powder particles exploding outward from impacts.

BACKGROUND: Deep [WARM DARK COLOR — e.g., chocolate brown / mahogany / dark mocha] gradient. Slightly lighter in the center behind the products. No surface visible.

LIGHTING: Strong dramatic backlight creating a warm glow around each product, combined with a soft front fill to show product texture detail. Sauce drizzles catch the light and appear glossy.

COLOR PALETTE: Deep [BACKGROUND WARM DARK] with [PASTRY GOLDEN BROWN] products and [SAUCE COLOR] drizzles. Monochromatic warm feel.

CAMERA ANGLE: Straight-on front view, slightly low angle. Products fill most of the frame.

MOOD: Intense, indulgent, moody chocolate advertising — high-end confectionery brand quality.

FORMAT: Vertical portrait 9:16.

POST-PROCESSING: Deep crushed blacks, rich warm mid-tones, high clarity on product textures, subtle background vignette.

⚙ Replace every [PLACEHOLDER] with your actual product, sauce, and color details.""",
    },

    # ── 5 ──────────────────────────────────────────────────
    {
        "file": "WhatsApp Image 2026-05-18 at 8.35.38 PM (1).jpeg",
        "storage_name": "pastry-pistachio-rain-croissant.jpg",
        "category_slug": "pastry",
        "title": "Golden Pistachio Rain — Showered Croissant",
        "description": "Stunning shot of a golden croissant on a stone plate being showered by a cascade of falling pistachio nuts and golden dust from above, against a dark textured concrete background.",
        "tags": ["pistachio", "croissant", "falling", "golden", "dramatic", "shower"],
        "is_premium": True,
        "meta_prompt": """\
Create a premium INGREDIENT SHOWER food advertisement photo of [YOUR PASTRY] being dramatically rained upon by [YOUR KEY INGREDIENT].

SUBJECT: [YOUR PASTRY — e.g., croissant / tart / cake] sitting on or near a [DARK STONE PLATE / WOODEN BOARD / SLATE], centered in frame, already generously topped with [YOUR INGREDIENT]. The pastry looks freshly baked, golden, and perfectly formed.

SHOWER EFFECT: A thick cascade of [YOUR INGREDIENT — e.g., pistachio nuts / almond slivers / sesame seeds / crushed nuts] falling from above in a beam/column, spreading outward near the top of frame. The shower illuminated by a strong backlight creating a glowing halo of [GOLDEN / GREEN / WHITE] particles. Some elements sharp, many softly blurred showing velocity.

SECONDARY PARTICLES: Fine [INGREDIENT DUST / POWDER] dispersed around the primary shower creating an atmospheric glow cloud above and around the product.

BACKGROUND: Dark cool-grey concrete or stone wall texture, slightly out of focus. Creates maximum contrast against the warm product and bright particle shower.

LIGHTING: Dramatic spotlight backlight from directly above — illuminates the shower of ingredients and creates a god-ray / beam effect. Soft front fill light reveals product texture without losing the drama.

COLOR PALETTE: Cool dark grey background, warm golden pastry, vibrant [INGREDIENT COLOR — e.g., green / gold / white] shower — tri-tone high contrast.

CAMERA ANGLE: Low-angle front shot, product at center, showing the shower coming from above filling the upper portion of the frame.

MOOD: Premium, gift-worthy, artisan, luxurious bakery advertising.

FORMAT: Vertical portrait 9:16.

POST-PROCESSING: Maximum particle sharpness at point of contact, gentle motion blur on falling elements, warm color grade on product, cool/neutral treatment on background.

⚙ Replace every [PLACEHOLDER] with your actual product, ingredient, and color details.""",
    },

    # ── 6 ──────────────────────────────────────────────────
    {
        "file": "WhatsApp Image 2026-05-18 at 8.35.38 PM (2).jpeg",
        "storage_name": "pastry-glazed-donuts-stack-dark.jpg",
        "category_slug": "pastry",
        "title": "Glazed Donut Tower — Dark Moody Spice Style",
        "description": "Atmospheric stacked tower of glazed cinnamon donuts caught mid-levitation with white glaze dripping, powdered sugar dust, and scattered spices (cinnamon sticks, star anise) on a dramatic dark background.",
        "tags": ["donuts", "glaze", "cinnamon", "moody", "dark", "stacked", "levitation"],
        "is_premium": False,
        "meta_prompt": """\
Create a dramatic LEVITATING TOWER food advertisement photo of stacked [YOUR ROUND PASTRIES — e.g., donuts / cinnamon rolls / bagels] with flowing glaze.

SUBJECT: A gravity-defying stack of 3–4 [YOUR PRODUCTS], arranged as a leaning tower. The top product slightly elevated/floating above the stack. Each product dusted with [YOUR DRY TOPPING — e.g., cinnamon sugar / powdered sugar / cocoa] and drizzled with [YOUR GLAZE — e.g., white vanilla glaze / cream cheese frosting / caramel] that drips naturally down the sides and pools slightly below.

ATMOSPHERE: Fine [TOPPING POWDER] erupts upward from a natural looking spill/impact at the base. Scattered [WHOLE SPICE ELEMENTS — e.g., cinnamon sticks / star anise / vanilla pods / almonds] arranged organically on the surface around the stack.

BACKGROUND: Very dark near-black, with a subtle gradient lighter directly behind the stack. Dark wooden or stone surface, barely visible.

LIGHTING: Rim light from behind the stack — separates the products from the dark background with a warm glow edge. Soft fill from front-below — just enough to show glaze shine and texture detail without lifting the moody atmosphere.

COLOR PALETTE: Near-black background, warm golden-brown pastry tones, brilliant white glaze as the key highlight.

CAMERA ANGLE: Slightly below eye level, front-facing, showing the full tower height. Slight worm's-eye perspective exaggerates the height of the stack.

MOOD: Indulgent, premium bakery, moody autumnal, late-night dessert atmosphere.

FORMAT: Vertical portrait 9:16.

POST-PROCESSING: Very deep blacks, warm mid-tones on product, high gloss on glaze, fine powder haze in air, slight haze/atmospheric depth.

⚙ Replace every [PLACEHOLDER] with your actual product, glaze, and spice details.""",
    },

    # ── 7 ──────────────────────────────────────────────────
    {
        "file": "WhatsApp Image 2026-05-18 at 8.35.38 PM (3).jpeg",
        "storage_name": "pastry-crumble-cream-croissant-floating.jpg",
        "category_slug": "pastry",
        "title": "Crumble & Cream Croissant — Warm Floating Drama",
        "description": "Highly detailed levitating croissant generously filled with vanilla cream and coated in golden crumble topping, with fine crumble dust particles exploding around it against a warm glowing dark background.",
        "tags": ["croissant", "crumble", "cream filling", "floating", "warm", "dramatic"],
        "is_premium": True,
        "meta_prompt": """\
Create a premium FLOATING FILLED PASTRY food advertisement in the warm dramatic product photography style.

SUBJECT: A single [YOUR FILLED PASTRY — e.g., croissant / cream puff / brioche roll] levitating in mid-air, slightly rotated to show the [CROSS-SECTION or FRONT FACE] with filling visible. The pastry is generously coated in [YOUR CRUMBLE/COATING — e.g., golden sugar crumble / streusel / crushed graham cracker / chopped nuts]. Visible thick [YOUR FILLING — e.g., vanilla cream / chocolate ganache / pistachio cream] at the opening or oozing slightly from a cut.

PARTICLES: Fine [CRUMBLE/TOPPING] particles and dust erupting downward from the base of the floating product, as if it just launched upward. A few larger pieces also airborne.

BACKGROUND: Deep warm [DARK COLOR — e.g., amber brown / cognac / burnt sienna] gradient — lighter in center behind product, darkening toward edges. No surface visible.

LIGHTING: Warm spotlight from slightly above and in front of the product — creates beautiful specular highlights on each crumble piece and pastry layer. Strong rim/back light outlines the product edge in warm gold. Under-light optional to show filling details.

COLOR PALETTE: Warm golden caramel tones throughout — pastry, crumble, background all in the same warm family. Cream filling as the white contrast anchor.

CAMERA ANGLE: Slightly below eye level, front-and-slightly-side view, product angled ~20° to show depth and layers.

MOOD: Indulgent, warm, premium artisan patisserie, harvest-season cozy luxury.

FORMAT: Vertical portrait 9:16.

POST-PROCESSING: Maximum crumble texture detail, warm color grade, crushed blacks in corners, glowing warm center.

⚙ Replace every [PLACEHOLDER] with your actual product, filling, and topping details.""",
    },

    # ── 8 ──────────────────────────────────────────────────
    {
        "file": "WhatsApp Image 2026-05-18 at 8.35.38 PM (4).jpeg",
        "storage_name": "bakery-triple-sauce-drip-croissant-stack.jpg",
        "category_slug": "bakery",
        "title": "Triple Drip Croissant Tower — Warm Bokeh Bakery",
        "description": "Irresistible stack of three fresh croissants on a wooden board with dark chocolate and white caramel sauces being poured from above in elegant drips, with a warm blurred bakery interior in the background.",
        "tags": ["croissant", "chocolate", "caramel", "drip", "stack", "bokeh", "warm"],
        "is_premium": False,
        "meta_prompt": """\
Create a warm premium SAUCE DRIP food advertisement photo of stacked [YOUR PASTRY] with dual-color sauce pour.

SUBJECT: A photogenic stack/pile of 3–4 [YOUR PASTRIES — e.g., croissants / pain au chocolat / brioche buns] placed on a [RUSTIC WOODEN BOARD / STONE PLATE / MARBLE SLAB]. Multiple sauces being poured from just above frame — [SAUCE 1 — e.g., dark chocolate sauce] and [SAUCE 2 — e.g., white caramel / white chocolate / condensed milk] falling simultaneously in elegant thin streams, meeting and dripping down the sides of the top pastry. Sauce cascades naturally between and around the stacked pieces. A few small [CHOCOLATE CHIP / NUT / GARNISH] pieces scatter on the board.

SAUCE PHYSICS: Sauces captured mid-pour — the streams are sharp at top transitioning to gentle drips at the surface. Sauce pooling slightly on top pastry and dripping off edges.

BACKGROUND: Beautifully blurred warm bakery interior — visible shelving with bread/pastries in soft focus. Warm window light from behind. Very shallow depth of field — the stacked pastries are the only sharp element.

LIGHTING: Strong warm natural window light from behind/above the scene — creates a golden glow halo around the stack and illuminates the transparent sauce streams. Soft reflection fill from the wooden board surface.

COLOR PALETTE: Warm golden pastry, dark chocolate brown, cream/ivory white sauce, blurred warm amber background — all cohesively warm.

CAMERA ANGLE: Eye-level or slightly above, front-facing, slightly to one side to show depth.

MOOD: Inviting, warm, artisan bakery atmosphere, weekend morning luxury.

FORMAT: Square 1:1 or 4:5 for Instagram feed — also works as 9:16 crop for Stories.

POST-PROCESSING: Warm golden color grade, creamy bokeh background, rich sauce highlight, natural film-like texture.

⚙ Replace every [PLACEHOLDER] with your actual product, sauce types, and surface details.""",
    },

    # ── 9 ──────────────────────────────────────────────────
    {
        "file": "WhatsApp Image 2026-05-18 at 8.35.39 PM.jpeg",
        "storage_name": "bakery-dark-dramatic-falling-croissants.jpg",
        "category_slug": "bakery",
        "title": "Dark Explosive Croissants — Cinnamon & Coffee Style",
        "description": "Cinematic dark food photo of two croissants caught in a dramatic falling moment with cinnamon-coffee powder exploding around them, fresh herbs on the dark surface, and cinnamon sticks as props against a near-black background.",
        "tags": ["croissant", "dark", "dramatic", "falling", "cinnamon", "coffee", "cinematic"],
        "is_premium": False,
        "meta_prompt": """\
Create a cinematic DARK DRAMATIC food advertisement of [YOUR PASTRY] in the dark explosive falling photography style.

SUBJECT: 2–3 [YOUR PASTRIES — e.g., croissants / pain au chocolat / bagels] in dynamic falling positions at different heights and angles — one above the other, slightly rotated to show their three-dimensionality. Each pastry freshly golden-baked with visible texture detail.

EXPLOSION: Rich [COLOR — e.g., cinnamon-brown / cocoa / espresso] powder erupting between and below the falling pastries — cloud-like explosion frozen in motion. Fine particles form trails showing the path of fall.

SURFACE DETAILS: On the dark surface at the bottom: scattered [WHOLE SPICES — e.g., cinnamon sticks / coffee beans / cardamom pods], small [FRESH HERB SPRIGS — e.g., mint / rosemary / thyme], a light scatter of [POWDER — e.g., cinnamon / coffee grounds] already settled.

BACKGROUND: Near-black — deep dark [COLOR — e.g., charcoal / slate / dark forest]. Slightly graduated — darkest at corners, marginally lighter directly behind products. No identifiable surface for the main field.

LIGHTING: Minimal and dramatic — a single narrow spotlight or hard side-light revealing texture on the pastry. Strong rim light separating products from dark background. The powder cloud illuminated from within by a subtle backlight, creating depth.

COLOR PALETTE: Near-black background, warm golden pastry, rich brown powder, accent color from the herbs or spice props.

CAMERA ANGLE: Low-angle front view, products filling the vertical frame, falling toward the viewer.

MOOD: Cinematic, bold, artisan bakery brand — premium advertising editorial. Think high-fashion but for food.

FORMAT: Vertical portrait 9:16.

POST-PROCESSING: Maximum blacks (no crushed shadows on product), brilliant golden rim lights, atmospheric powder haze, ultra-high clarity on pastry texture.

⚙ Replace every [PLACEHOLDER] with your actual product, spice, and prop details.""",
    },

    # ── 10 ─────────────────────────────────────────────────
    {
        "file": "WhatsApp Image 2026-05-18 at 8.35.39 PM (1).jpeg",
        "storage_name": "pastry-chocolate-almond-milk-splash.jpg",
        "category_slug": "pastry",
        "title": "Chocolate Almond Milk Splash Croissant",
        "description": "Rich close-up of a croissant submerged in a dynamic milk splash, dusted with cocoa powder and surrounded by dark chocolate chunks and whole almonds in a warm chocolate-brown environment.",
        "tags": ["croissant", "chocolate", "almond", "milk splash", "cocoa", "premium"],
        "is_premium": True,
        "meta_prompt": """\
Create a decadent LIQUID SPLASH food advertisement photo of [YOUR PASTRY] in a premium chocolate and milk splash setting.

SUBJECT: A [YOUR PASTRY — e.g., croissant / pain au chocolat / Danish] positioned at the center of a frozen dynamic MILK or CREAM SPLASH. The liquid swirls around and partially engulfs the base of the product in a perfect action-frozen arc. The pastry top is generously dusted with [YOUR POWDER — e.g., cocoa powder / cinnamon / powdered milk]. Additional garnish: [YOUR CHUNKY INGREDIENT — e.g., dark chocolate chunks / almond halves / hazelnut pieces] scattered at the base of the splash and in the air.

LIQUID PHYSICS: The splash is frozen at peak action — liquid rises on either side of the product in beautiful arcing wings, with fine droplets orbiting in the air. Splash base shows surface tension details.

BACKGROUND: Deep warm [DARK TONE — e.g., chocolate brown / toffee / cognac] gradient — consistent with the liquid and product tones.

LIGHTING: Strong single-source key light from the front-above — creates brilliant specular highlights on every liquid droplet, turning them into tiny stars. Rim light separates the product from background with warm edge glow.

COLOR PALETTE: Rich chocolate brown tones throughout with cream/white milk as contrast. [GARNISH COLOR — e.g., almond beige / dark chocolate near-black] as accent elements.

CAMERA ANGLE: Straight-on front angle, slightly below the splash apex to maximize the dramatic wing effect.

MOOD: Indulgent, decadent, luxury chocolatier / premium pastry brand. Super Bowl ad level quality.

FORMAT: Vertical portrait 9:16 or Square 1:1.

POST-PROCESSING: Maximum liquid drop sharpness and specular highlights, deep warm blacks, high contrast, fine powder haze above the product.

⚙ Replace every [PLACEHOLDER] with your actual product, liquid, and garnish details.""",
    },

    # ── 11 ─────────────────────────────────────────────────
    {
        "file": "WhatsApp Image 2026-05-18 at 8.35.39 PM (2).jpeg",
        "storage_name": "pastry-cinnamon-rolls-floating-golden.jpg",
        "category_slug": "pastry",
        "title": "Floating Cinnamon Roll Tower — Warm Golden",
        "description": "Gorgeous stack of three perfectly glazed cinnamon rolls levitating in a warm golden atmosphere with cinnamon sticks flying around them, white cream frosting dripping beautifully, and cinnamon sugar dust in the air.",
        "tags": ["cinnamon roll", "glaze", "floating", "warm", "golden", "frosting"],
        "is_premium": False,
        "meta_prompt": """\
Create a warm luxurious LEVITATING STACK food advertisement of [YOUR SPIRAL/ROUND PASTRY — e.g., cinnamon rolls / Danish swirls / babka slices] in the warm golden floating style.

SUBJECT: A perfect stack of 3 [YOUR PRODUCTS], arranged as a slightly off-balance gravity-defying tower — the pieces visibly separated with small gaps between them, as if magnetically hovering. Each piece is generously frosted/glazed with [YOUR FROSTING — e.g., cream cheese frosting / white vanilla glaze / royal icing] that drips in perfect slow drip patterns down the sides. The spiral center of each roll is clearly visible and beautifully caramelized.

FLYING ELEMENTS: 4–6 [SPICE STICKS or PROPS — e.g., cinnamon sticks / vanilla pods / rosemary sprigs] floating around the stack at different angles and distances, as if orbiting the tower. Fine [SPICE POWDER — e.g., cinnamon dust / nutmeg] erupting gently upward from the top of the stack.

BACKGROUND: Warm golden-amber gradient — bright warm center directly behind the stack fading to rich caramel amber at edges. No visible surface — pure gradient.

LIGHTING: Soft warm studio light from above and slightly in front. Even, flattering light that shows frosting detail and pastry texture. Warm glow fill from below bounces off the gradient background.

COLOR PALETTE: Golden caramel pastry, brilliant white frosting, warm amber background, rich brown cinnamon props. All warm tones — cohesive, appetizing palette.

CAMERA ANGLE: Straight front angle at product eye-level, showing the full stack height. Slightly elevated to show the frosting on the top roll.

MOOD: Cozy, warm, indulgent bakery — weekend morning comfort luxury. Social media viral food content aesthetic.

FORMAT: Vertical portrait 9:16.

POST-PROCESSING: Warm orange-gold color grade, frosting is bright white with creamy shadow tones, slight soft glow around the stack, rich deep amber in the background corners.

⚙ Replace every [PLACEHOLDER] with your actual product and frosting/spice details.""",
    },
]

# ─── Categories seed data ──────────────────────────────────
CATEGORIES_SEED = [
    {"name": "Food & Restaurants",  "slug": "food",        "icon": "🍕", "description": "Restaurant menus, food delivery, and dining ads",       "display_order": 1},
    {"name": "Pastry & Desserts",   "slug": "pastry",      "icon": "🥐", "description": "Bakery, cakes, sweets and dessert ads",                  "display_order": 2},
    {"name": "Fashion & Clothing",  "slug": "fashion",     "icon": "👗", "description": "Clothing, accessories, and style ads",                   "display_order": 3},
    {"name": "Tools & Hardware",    "slug": "tools",       "icon": "🔧", "description": "Hardware stores, tools, and equipment ads",              "display_order": 4},
    {"name": "Bakery Products",     "slug": "bakery",      "icon": "🍞", "description": "Fresh bread, baked goods, and bakery promotions",        "display_order": 5},
    {"name": "Mobiles & Tablets",   "slug": "mobiles",     "icon": "📱", "description": "Smartphones, tablets, and tech gadgets",                 "display_order": 6},
    {"name": "Beauty & Cosmetics",  "slug": "beauty",      "icon": "💄", "description": "Makeup, skincare, and beauty products",                  "display_order": 7},
    {"name": "Real Estate",         "slug": "realestate",  "icon": "🏠", "description": "Property listings, rentals, and real estate",            "display_order": 8},
    {"name": "Automotive",          "slug": "automotive",  "icon": "🚗", "description": "Cars, vehicles, and auto service ads",                   "display_order": 9},
    {"name": "Health & Pharmacy",   "slug": "health",      "icon": "💊", "description": "Pharmacies, health products, and wellness",              "display_order": 10},
    {"name": "Cafés & Coffee",      "slug": "cafes",       "icon": "☕", "description": "Coffee shops, cafés, and beverage brands",               "display_order": 11},
    {"name": "Electronics",         "slug": "electronics", "icon": "🖥️", "description": "Electronics, gaming, and tech products",                 "display_order": 12},
]

# ─── Helpers ───────────────────────────────────────────────

def ensure_bucket():
    try:
        sb.storage.create_bucket(BUCKET, options={"public": True})
        print(f"  ✅ Created storage bucket '{BUCKET}'")
    except Exception as e:
        msg = str(e)
        if "already exists" in msg.lower() or "duplicate" in msg.lower() or "409" in msg:
            print(f"  ℹ️  Bucket '{BUCKET}' already exists — OK")
        else:
            print(f"  ⚠️  Bucket creation note: {msg}")


def seed_categories():
    res = sb.table("categories").select("slug").execute()
    existing = {r["slug"] for r in (res.data or [])}
    to_insert = [c for c in CATEGORIES_SEED if c["slug"] not in existing]
    if not to_insert:
        print(f"  ℹ️  Categories already seeded ({len(existing)} found)")
        return
    sb.table("categories").insert(to_insert).execute()
    print(f"  ✅ Seeded {len(to_insert)} categories")


def get_category_map():
    res = sb.table("categories").select("id, slug").execute()
    return {r["slug"]: r["id"] for r in (res.data or [])}


def upload_image(filepath: Path, storage_name: str) -> str:
    """Upload to Supabase Storage, return public URL. Skips if already uploaded."""
    storage_path = f"pastry/{storage_name}"
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{storage_path}"

    # Try uploading; if file already exists Supabase returns 400 "already exists"
    try:
        with open(filepath, "rb") as f:
            data = f.read()
        sb.storage.from_(BUCKET).upload(
            path=storage_path,
            file=data,
            file_options={"content-type": "image/jpeg", "upsert": "true"},
        )
        print(f"  ⬆️  Uploaded → {storage_name}")
    except Exception as e:
        msg = str(e)
        if "already exists" in msg.lower() or "duplicate" in msg.lower():
            print(f"  ℹ️  Already in storage → {storage_name}")
        else:
            print(f"  ⚠️  Upload issue ({msg}) — using URL anyway")

    return public_url


def style_already_exists(title: str) -> bool:
    res = sb.table("ad_styles").select("id").eq("title", title).execute()
    return bool(res.data)


# ─── Main ──────────────────────────────────────────────────

def main():
    print("\n🎨 Abdalla Eissa for Design — Style Uploader\n" + "─" * 45)

    print("\n[1/4] Ensuring storage bucket …")
    ensure_bucket()

    print("\n[2/4] Seeding categories …")
    seed_categories()

    print("\n[3/4] Building category map …")
    cat_map = get_category_map()
    if not cat_map:
        print("  ❌ No categories found — did the DB schema run?")
        sys.exit(1)
    print(f"  ✅ {len(cat_map)} categories loaded")

    print("\n[4/4] Uploading images & inserting styles …\n")
    ok = 0
    skipped = 0
    failed = 0

    for style in STYLES:
        filepath = IMAGES_DIR / style["file"]
        print(f"► {style['title']}")

        if not filepath.exists():
            print(f"  ❌ Image not found: {filepath}\n")
            failed += 1
            continue

        if style_already_exists(style["title"]):
            print(f"  ℹ️  Already in database — skipped\n")
            skipped += 1
            continue

        cat_id = cat_map.get(style["category_slug"])
        if not cat_id:
            print(f"  ❌ Category slug '{style['category_slug']}' not in DB\n")
            failed += 1
            continue

        try:
            image_url = upload_image(filepath, style["storage_name"])
            sb.table("ad_styles").insert({
                "category_id":  cat_id,
                "title":        style["title"],
                "image_url":    image_url,
                "meta_prompt":  style["meta_prompt"],
                "description":  style["description"],
                "tags":         style["tags"],
                "is_premium":   style["is_premium"],
            }).execute()
            print(f"  ✅ Inserted into ad_styles\n")
            ok += 1
            time.sleep(0.3)   # gentle rate-limiting
        except Exception as e:
            print(f"  ❌ DB insert failed: {e}\n")
            failed += 1

    print("─" * 45)
    print(f"Done!  ✅ {ok} added  |  ℹ️ {skipped} skipped  |  ❌ {failed} failed\n")


if __name__ == "__main__":
    main()
