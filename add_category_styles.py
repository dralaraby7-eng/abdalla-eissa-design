"""
add_category_styles.py — Add ad styles for all categories
Run: python add_category_styles.py
"""
from supabase import create_client

SUPABASE_URL = "https://ukjwbcrbnutxemwsebsc.supabase.co"
SERVICE_KEY  = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVrandiY3JibnV0eGVtd3NlYnNjIiwi"
    "***SERVICE_ROLE_PAYLOAD_REMOVED***"
    "***SERVICE_ROLE_SIG_REMOVED***"
)

sb = create_client(SUPABASE_URL, SERVICE_KEY)

# ─── Unsplash CDN image URLs by category ──────────────────────
# Format: https://images.unsplash.com/photo-{ID}?w=600&h=600&fit=crop&q=80

STYLES = [

    # ══════════════════════════════════════════════════════════
    # FOOD & RESTAURANTS
    # ══════════════════════════════════════════════════════════
    {
        "category_slug": "food",
        "title": "Vibrant Food Bowl — Overhead Hero Shot",
        "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&h=600&fit=crop&q=80",
        "description": "Colorful overhead flat-lay of a healthy food bowl with vibrant vegetables, grains, and sauce on a clean white surface with soft natural daylight.",
        "tags": ["overhead", "food bowl", "colorful", "healthy", "flat lay"],
        "is_premium": False,
        "meta_prompt": """\
Create a stunning OVERHEAD HERO SHOT food advertisement for [YOUR RESTAURANT or FOOD BRAND].

SUBJECT: A beautifully composed [YOUR DISH — e.g., grain bowl / salad / pasta] photographed directly from above, centered in the frame. The dish should be visually rich with [YOUR KEY INGREDIENTS — e.g., grilled chicken / avocado / roasted vegetables / sauce] arranged in distinct segments rather than mixed together — Instagram-worthy presentation.

ACCOMPANYING ELEMENTS (arranged around the main dish):
• Small bowl of [SAUCE or DIP]
• [GARNISH — e.g., fresh herbs / lemon wedge / chili flakes]
• [CUTLERY — e.g., elegant fork and knife / chopsticks / spoon]
• A few [LOOSE INGREDIENTS — e.g., cherry tomatoes / seeds / nuts] scattered naturally

SURFACE: Clean [WHITE / LIGHT GREY / NATURAL WOOD] flat surface, matte texture.

LIGHTING: Soft even overhead natural window light — no harsh shadows, everything evenly illuminated. Near-shadowless.

COLOR PALETTE: Focus on the natural vibrant colors of [YOUR MAIN INGREDIENTS] — make them pop against the neutral surface.

CAMERA: Direct overhead 90° top-down. Full dish fills 70% of the frame.

MOOD: Fresh, healthy, appetizing, premium restaurant quality.

FORMAT: Square 1:1 for Instagram feed, or 4:5 portrait for Stories.

POST-PROCESSING: Slight saturation boost on food colors, light and airy editing style, minimal shadows.

⚙ Replace every [PLACEHOLDER] with your actual dish, ingredients, and brand details.""",
    },
    {
        "category_slug": "food",
        "title": "Restaurant Burger — Low-Angle Dramatic Ad",
        "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&h=600&fit=crop&q=80",
        "description": "Epic low-angle hero shot of a towering gourmet burger with all layers visible, sauce dripping down the sides, against a dark moody restaurant background.",
        "tags": ["burger", "low angle", "dramatic", "restaurant", "hero shot"],
        "is_premium": False,
        "meta_prompt": """\
Create an EPIC LOW-ANGLE HERO food advertisement photo of [YOUR MAIN DISH — e.g., burger / sandwich / pizza slice].

SUBJECT: [YOUR DISH] at the center of frame, photographed from a low dramatic angle that emphasizes height and layers. Every layer of [YOUR DISH — e.g., toasted bun / melted cheese / patty / fresh lettuce / tomato / special sauce] is clearly visible in cross-section. [YOUR SAUCE] drips naturally down the sides.

CONSTRUCTION: [YOUR DISH] appears tall and generously stacked. Ingredients are fresh and premium — slight gloss on [GLOSSY ELEMENTS — e.g., sauces / pickles / lettuce], textured surface on [TEXTURED ELEMENTS — e.g., bun / patty / crispy coating].

SUPPORTING PROPS: [YOUR SIDE DISH — e.g., golden fries / onion rings / coleslaw] beside the main dish. A small container of [YOUR DIP SAUCE] nearby.

BACKGROUND: [Dark moody restaurant interior / Warm bokeh lights / Dark wooden table] — blurred shallow depth of field background. The background suggests premium dining ambiance.

LIGHTING: Dramatic side-and-back lighting highlighting textures and creating appetizing shadows. Specular highlight on the sauce drip — make it look irresistible.

COLOR PALETTE: Warm golden-brown tones of the [BREAD/CRUST], rich red/green freshness of [VEGETABLES], contrasting sauce color [YOUR SAUCE COLOR].

MOOD: Bold, indulgent, premium fast-casual or restaurant-quality advertising.

FORMAT: Vertical portrait 4:5 or 9:16.

⚙ Replace every [PLACEHOLDER] with your actual dish, ingredients, and restaurant style.""",
    },
    {
        "category_slug": "food",
        "title": "Fine Dining Plate — Minimalist Luxury",
        "image_url": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=600&h=600&fit=crop&q=80",
        "description": "Elegant minimalist fine dining presentation on a white plate with artistic sauce swipe, microgreens garnish, and precise composition on a dark linen tablecloth.",
        "tags": ["fine dining", "minimalist", "luxury", "elegant", "restaurant"],
        "is_premium": True,
        "meta_prompt": """\
Create a FINE DINING MINIMALIST food advertisement photo for [YOUR UPSCALE RESTAURANT].

SUBJECT: A single artfully plated [YOUR DISH — e.g., pan-seared salmon / beef tenderloin / duck confit / risotto] on a large clean [WHITE / DARK / STONE] plate. The plating follows fine dining principles:
• [YOUR PROTEIN or MAIN] positioned at 2 o'clock in the plate
• An elegant [SAUCE — e.g., reduction / coulis / emulsion] swiped or dotted artistically across the plate
• 3–5 small [GARNISH ELEMENTS — e.g., microgreens / edible flowers / compressed vegetables / foam] placed with precision
• Negative space — at least 40% of the plate surface is empty

TABLE SETTING: The plate sits on [DARK LINEN / SLATE / MARBLE] surface. Out-of-focus glimpse of elegant cutlery (silver knife and fork), a crystal wine glass, and folded linen napkin.

BACKGROUND: Dark, sophisticated — blurred restaurant interior with soft ambient lighting suggesting luxury.

LIGHTING: Directional side-light with a warm soft key. Creates gentle shadows emphasizing the 3D structure of the plated food. Specular highlights on the sauce and any glazed elements.

DEPTH OF FIELD: Extremely shallow — only the center of the main element is in perfect focus, outer elements softly blurred.

MOOD: Michelin-star elegance, refinement, culinary artistry. Think food photography for a luxury restaurant's Instagram.

FORMAT: Square 1:1 or landscape 4:3.

POST-PROCESSING: Desaturated cool-tone background, warm highlights on the food, very gentle overall treatment. Timeless, not trendy.

⚙ Replace every [PLACEHOLDER] with your actual dish, sauce, garnish, and restaurant style.""",
    },

    # ══════════════════════════════════════════════════════════
    # FASHION & CLOTHING
    # ══════════════════════════════════════════════════════════
    {
        "category_slug": "fashion",
        "title": "Clothing Flat Lay — Bold Color Pop",
        "image_url": "https://images.unsplash.com/photo-1483985988355-763728e1cdc6?w=600&h=600&fit=crop&q=80",
        "description": "Vibrant flat-lay fashion editorial with colorful clothing items neatly arranged on a pastel background with accessories, creating a bold Instagram-ready clothing ad.",
        "tags": ["flat lay", "colorful", "clothing", "fashion", "editorial"],
        "is_premium": False,
        "meta_prompt": """\
Create a vibrant FASHION FLAT LAY advertisement for [YOUR CLOTHING BRAND / COLLECTION].

SUBJECT: A curated flat-lay composition of [YOUR CLOTHING ITEMS — e.g., dress / shirt / jacket + matching pants] neatly arranged on a [BACKGROUND COLOR — e.g., pastel pink / clean white / dusty sage] surface. The main garment is opened and spread flat, showing its design and fabric clearly.

CLOTHING ARRANGEMENT:
• Main item: [YOUR HERO PIECE] centered and fully visible
• Supporting items: 2–3 complementary [ACCESSORIES — e.g., shoes / bag / belt / sunglasses / scarf] arranged around the main piece
• Small touches: [PROPS — e.g., flowers / dried botanicals / jewelry pieces] for styling context

LABELS & TAGS: If your brand has swing tags or labels, they should be subtly visible but not distracting.

SURFACE: Clean matte [BACKGROUND COLOR] surface — completely flat, no creases or distractions.

LIGHTING: Soft even studio light from directly above. No shadows. Maximum clarity on fabric texture and pattern details.

COMPOSITION: Items arranged in either a symmetrical grid OR a casual-but-intentional scattered layout. Leave subtle negative space for text overlay.

MOOD: Modern fashion brand aesthetic — clean, aspirational, editorial.

TEXT SPACE: Leave a corner or side area for brand name and price text overlay (do not generate text — just leave space).

FORMAT: Square 1:1 for Instagram / Square product listing.

POST-PROCESSING: Clean bright editing, true-to-life fabric colors, minimal grain.

⚙ Replace every [PLACEHOLDER] with your actual clothing items, colors, and brand style.""",
    },
    {
        "category_slug": "fashion",
        "title": "Lifestyle Fashion Portrait — Outdoor Golden Hour",
        "image_url": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&h=600&fit=crop&q=80",
        "description": "Confident lifestyle fashion portrait of a model wearing the featured outfit in an outdoor urban setting during golden hour, with natural warm tones and shallow depth of field.",
        "tags": ["portrait", "lifestyle", "golden hour", "outdoor", "model", "fashion"],
        "is_premium": True,
        "meta_prompt": """\
Create a LIFESTYLE FASHION PORTRAIT advertisement for [YOUR CLOTHING BRAND].

SUBJECT: A confident [GENDER — e.g., woman / man / model] wearing [YOUR OUTFIT — e.g., flowy midi dress / tailored suit / casual streetwear look — describe the key pieces]. The model is posed naturally in a [POSE — e.g., walking mid-stride / leaning against wall / looking over shoulder] — candid and authentic, not overly staged.

LOCATION: [YOUR SETTING — e.g., urban street / beachside promenade / park / rooftop / cafe entrance] — blurred in the background.

LIGHTING: Warm [GOLDEN HOUR / AFTERNOON / OVERCAST SOFT] natural light. The light falls on the model from [direction — e.g., from the side / from behind for a rim-lit glow]. Skin and fabric textures are beautifully rendered.

DEPTH OF FIELD: Shallow — the model is sharp, the background location is softly blurred with creamy bokeh.

COLOR PALETTE: The outfit colors [YOUR KEY COLORS] are the focal point. The background is a complementary but desaturated tone.

BODY LANGUAGE: Confident, aspirational, authentic — the model looks like they genuinely chose to wear this, not like they're modeling.

MOOD: Premium lifestyle brand — modern, aspirational, relatable.

FORMAT: Portrait 4:5 or 2:3 for Instagram and magazine ads.

POST-PROCESSING: Cinematic color grade with warm golden tones, soft skin texture, sharp fabric detail.

BRANDING SPACE: Upper third or lower quarter can accommodate brand name overlay.

⚙ Replace every [PLACEHOLDER] with your actual outfit details, model direction, and brand aesthetic.""",
    },

    # ══════════════════════════════════════════════════════════
    # CAFÉS & COFFEE
    # ══════════════════════════════════════════════════════════
    {
        "category_slug": "cafes",
        "title": "Latte Art Close-Up — Café Mood Shot",
        "image_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=600&h=600&fit=crop&q=80",
        "description": "Intimate close-up of a perfectly crafted latte with intricate rosette art, on a wooden café table with soft bokeh background and warm natural light.",
        "tags": ["latte", "coffee art", "close-up", "warm", "café", "cozy"],
        "is_premium": False,
        "meta_prompt": """\
Create a warm CAFÉ ATMOSPHERE coffee advertisement photo for [YOUR CAFÉ / COFFEE BRAND].

SUBJECT: A beautifully crafted [YOUR COFFEE DRINK — e.g., flat white / latte / cappuccino / cold brew] in a [YOUR CUP — e.g., white ceramic cup / branded glass / clear cup / takeaway cup with logo]. If it's a hot drink with milk: elegant [LATTE ART — e.g., rosette / tulip / heart] on the surface.

TABLE SETTING: The cup sits on a [WOODEN / MARBLE / CONCRETE] café table. A [SMALL PLATE / SAUCER] underneath. Optional: [SMALL PASTRY — e.g., biscotti / macaroon / small cake slice] beside the cup. A [NAPKIN] folded neatly nearby.

BACKGROUND: Blurred warm café interior — [SOFT BOKEH LIGHTS / BOOKSHELVES / PLANTS / WINDOWS]. The background should convey a warm, inviting café atmosphere.

LIGHTING: Warm soft natural [WINDOW LIGHT] from the side — golden morning light quality. Creates a gentle shadow on the table and highlights the steam (if hot drink).

STEAM: If the drink is hot, subtle atmospheric steam rising from the surface adds warmth and freshness.

COLOR PALETTE: Warm caramels, creamy whites, rich coffee browns — all warm and inviting.

MOOD: Cozy café escape, slow morning, artisan coffee culture.

FORMAT: Square 1:1 or slightly portrait 4:5.

POST-PROCESSING: Warm tones, slightly raised shadows, rich coffee color, soft overall vibe.

⚙ Replace every [PLACEHOLDER] with your actual coffee drink, cup style, and café atmosphere.""",
    },
    {
        "category_slug": "cafes",
        "title": "Iced Coffee Splash — Refreshing Summer Ad",
        "image_url": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=600&h=600&fit=crop&q=80",
        "description": "Dynamic refreshing iced coffee advertisement with ice cubes splashing into a tall glass, coffee and milk creating a beautiful swirl, on a bright airy background.",
        "tags": ["iced coffee", "splash", "summer", "refreshing", "dynamic"],
        "is_premium": True,
        "meta_prompt": """\
Create a refreshing ICED COFFEE SPLASH advertisement photo for [YOUR CAFÉ / COFFEE BRAND].

SUBJECT: A tall [YOUR ICED DRINK — e.g., iced latte / cold brew / iced caramel macchiato / frappuccino] in a [YOUR GLASS — e.g., tall clear glass / branded cup with straw]. The drink is in motion — [OPTION A: ice cubes splashing into the glass / OPTION B: cream or milk being poured in a dramatic swirl / OPTION C: the glass surrounded by ice and condensation droplets].

LIQUID DYNAMICS:
[If pouring]: A stream of [CREAM / MILK / ESPRESSO] being poured from above, caught mid-pour as it swirls through the iced drink — dark and light swirling together beautifully.
[If splashing]: Ice cubes caught in mid-air splash, water droplets orbiting the glass.

ICE DETAIL: Large clear ice cubes inside the glass with sharp bubble details. Condensation droplets on the glass exterior.

BACKGROUND: Clean [WHITE / LIGHT PASTEL / BRIGHT SUMMERY] — bright and airy, very different from the dark hot coffee aesthetic.

LIGHTING: Bright, clean studio light — slightly backlit to create translucency in the ice and liquid. Crisp and refreshing feeling.

COLOR PALETTE: Cool blues and whites from ice and light, contrasting with the rich [COFFEE BROWN / AMBER] of the drink. If [CARAMEL / SYRUP] is involved, add golden drips.

MOOD: Refreshing, summery, light, energizing — the opposite of heavy/cozy hot coffee.

FORMAT: Vertical portrait 9:16 or square 1:1.

POST-PROCESSING: Cool, bright, high-key editing — whites are bright, colors are clean.

⚙ Replace every [PLACEHOLDER] with your actual iced drink name, glass style, and brand colors.""",
    },

    # ══════════════════════════════════════════════════════════
    # BEAUTY & COSMETICS
    # ══════════════════════════════════════════════════════════
    {
        "category_slug": "beauty",
        "title": "Skincare Product Lineup — Clean Beauty Aesthetic",
        "image_url": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=600&h=600&fit=crop&q=80",
        "description": "Elegant minimalist skincare product lineup on a marble surface with soft petals and natural light, conveying clean beauty and premium skincare brand identity.",
        "tags": ["skincare", "clean beauty", "minimalist", "marble", "premium"],
        "is_premium": False,
        "meta_prompt": """\
Create a CLEAN BEAUTY PRODUCT LINEUP advertisement photo for [YOUR BEAUTY / SKINCARE BRAND].

SUBJECT: A curated lineup of [NUMBER — e.g., 3–5] [YOUR PRODUCTS — e.g., serum / moisturizer / toner / eye cream / cleanser] bottles and jars arranged in an aesthetically pleasing composition. Products are your actual branded packaging (describe: [YOUR BOTTLE SHAPE AND COLOR]).

ARRANGEMENT: Products arranged in a slight arc or stepped height composition — tallest in the back, shortest in front. Natural, not perfectly rigid.

SURFACE: Clean [WHITE MARBLE / LIGHT STONE / FROSTED GLASS] surface with soft natural reflections.

DECORATIVE ELEMENTS: Subtle organic elements — [OPTION: white flower petals scattered / dried botanicals / a single green leaf / rose quartz crystal] — placed sparingly to add life without distraction.

BACKGROUND: Clean light [WHITE / OFF-WHITE / VERY PALE PASTEL] — completely seamless, no horizon line.

LIGHTING: Soft diffused natural studio light from [THE LEFT OR ABOVE]. Gentle shadows behind products give depth. Products are evenly lit showing packaging labels clearly.

COLOR PALETTE: Determined by your brand colors [YOUR BRAND PALETTE]. Background is always neutral to let the products lead.

MOOD: Clean, premium, clinical beauty, aspirational skincare ritual.

FORMAT: Square 1:1 for product listing, 4:5 for Instagram feed.

POST-PROCESSING: Very clean, bright, true-to-packaging colors. Minimal editing — let the products speak.

⚙ Replace every [PLACEHOLDER] with your actual product names, bottle descriptions, and brand colors.""",
    },
    {
        "category_slug": "beauty",
        "title": "Makeup Glam Portrait — Beauty Campaign Shot",
        "image_url": "https://images.unsplash.com/photo-1596755389378-c31d21fd1273?w=600&h=600&fit=crop&q=80",
        "description": "Striking beauty campaign portrait featuring flawless makeup with bold eye look and perfect skin, dramatic studio lighting, and luxury cosmetic brand aesthetic.",
        "tags": ["makeup", "portrait", "beauty campaign", "glam", "editorial", "cosmetics"],
        "is_premium": True,
        "meta_prompt": """\
Create a BEAUTY CAMPAIGN PORTRAIT advertisement for [YOUR COSMETICS / MAKEUP BRAND].

SUBJECT: A close-up or mid-shot portrait of a [GENDER — woman / person] with flawless professional makeup. Focus on showcasing [YOUR HERO PRODUCT TYPE — e.g., bold eye shadow / perfect skin / statement lip color / defined brows].

MAKEUP DETAILS:
• Skin: [FINISH — e.g., dewy glow / matte perfection / luminous satin] with perfectly even tone
• Eyes: [YOUR EYE LOOK — e.g., smoky eye / cut crease / natural enhancement / dramatic liner]
• Lips: [YOUR LIP COLOR — e.g., rich red / nude / coral / bold plum]
• Overall: [FEEL — e.g., day-time natural / editorial bold / evening glam / no-makeup makeup]

LIGHTING: [YOUR CHOSEN STYLE — e.g., beauty dish front light for bright even skin / dramatic Rembrandt side light for editorial / soft window light for natural beauty].

BACKGROUND: [CLEAN STUDIO — e.g., pure white / warm cream / deep black / color matching your brand].

CROP: Close enough to see all makeup details clearly — ideally from shoulders up.

COLOR PALETTE: Led by [YOUR BRAND'S KEY COLORS / PRODUCT COLORS USED IN THE LOOK].

MOOD: [YOUR BRAND VOICE — e.g., empowering and bold / clean and minimal / luxurious and editorial].

FORMAT: Portrait 4:5 or 2:3 for beauty campaign.

POST-PROCESSING: Perfect skin retouching (natural, not plastic), vivid true-to-life product colors, professional beauty retouching standard.

⚙ Replace every [PLACEHOLDER] with your actual product, makeup look, and brand aesthetic.""",
    },

    # ══════════════════════════════════════════════════════════
    # MOBILES & TABLETS
    # ══════════════════════════════════════════════════════════
    {
        "category_slug": "mobiles",
        "title": "Smartphone Hero — Floating Device Ad",
        "image_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&h=600&fit=crop&q=80",
        "description": "Premium tech advertisement featuring a smartphone floating at a dynamic angle with a glowing screen displaying the device's key feature, against a gradient dark background.",
        "tags": ["smartphone", "tech", "floating", "premium", "device", "screen"],
        "is_premium": False,
        "meta_prompt": """\
Create a premium FLOATING TECH DEVICE advertisement photo for [YOUR PHONE / TABLET BRAND AND MODEL].

SUBJECT: [YOUR DEVICE — e.g., smartphone / tablet / smartwatch] floating at a dynamic angle (approximately 15°–25° tilt) against the background. The screen displays [YOUR SCREEN CONTENT — e.g., your brand's UI / a key feature screen / a beautiful wallpaper / the product's main app]. The device frame is [YOUR DEVICE COLOR — e.g., midnight black / silver / space grey / rose gold].

DEVICE PRESENTATION:
• Front face showing the screen clearly (most of the shot)
• Subtle 3/4 angle showing slight thickness/side of device
• Perfect reflection of the screen light on the device's polished frame

GLOW EFFECT: The device screen emits a soft [COLOR — matching your UI colors] ambient glow onto the background, creating an atmospheric light halo around the floating device.

BACKGROUND: Deep [DARK GRADIENT — e.g., near-black / deep navy / very dark grey] that transitions from darker at edges to slightly lighter directly behind the device.

LIGHTING: The screen itself is the primary light source. Optional: a subtle rim light from behind one edge of the device to separate it from the dark background.

SHADOW: Soft, diffused shadow below the floating device — not a hard drop shadow.

MOOD: Premium tech launch, flagship device, cutting-edge innovation.

FORMAT: Vertical portrait 9:16 or square 1:1.

POST-PROCESSING: Deep rich blacks, vivid screen colors, subtle chromatic aberration on screen edges, clean and minimal.

⚙ Replace every [PLACEHOLDER] with your actual device model, color, screen content, and brand.""",
    },
    {
        "category_slug": "mobiles",
        "title": "Phone In-Hand Lifestyle — Real Usage Shot",
        "image_url": "https://images.unsplash.com/photo-1512054502232-10a0a035d672?w=600&h=600&fit=crop&q=80",
        "description": "Authentic in-hand lifestyle shot of a smartphone being used in a real-life context, with the screen showing the app UI clearly and a natural blurred environment in the background.",
        "tags": ["in-hand", "lifestyle", "app UI", "real usage", "smartphone"],
        "is_premium": True,
        "meta_prompt": """\
Create an AUTHENTIC IN-HAND LIFESTYLE advertisement showing [YOUR PHONE / APP / SERVICE] being used naturally.

SUBJECT: A human hand (well-manicured / natural — your preference) holding [YOUR SMARTPHONE MODEL] in a natural grip. The screen clearly shows [YOUR APP SCREEN / KEY FEATURE / PRODUCT OFFERING — describe what's on screen: layout, colors, content]. The person appears genuinely engaged with the content — not posing, just using.

ENVIRONMENT: [YOUR CHOSEN SETTING — e.g., sitting at a café table / walking in a bright urban street / relaxing on a couch / at a desk in a bright office]. The environment is blurred but clearly recognizable.

DEPTH OF FIELD: Very shallow — the phone screen is the sharpest point in the frame. The hand is slightly less sharp, the background is beautifully blurred.

LIGHTING: [ENVIRONMENT-APPROPRIATE — e.g., warm window light for café / clean daylight for outdoor / soft indoor ambient]. The phone screen brightness is balanced with the environment — not overexposed.

HAND AND POSTURE: Natural grip. The angle shows the phone screen straight-on from a slight above angle (common when someone is using their phone standing or sitting).

MOOD: [YOUR BRAND VOICE — e.g., modern professional / youth lifestyle / premium / everyday convenience].

FORMAT: Portrait 9:16 or 4:5.

POST-PROCESSING: Natural color grade matching the environment, screen is well-exposed and readable, shallow depth of field.

⚙ Replace every [PLACEHOLDER] with your actual phone model, app/screen content, environment, and lifestyle context.""",
    },

    # ══════════════════════════════════════════════════════════
    # REAL ESTATE
    # ══════════════════════════════════════════════════════════
    {
        "category_slug": "realestate",
        "title": "Luxury Home Exterior — Golden Hour Property Ad",
        "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=600&h=600&fit=crop&q=80",
        "description": "Premium real estate advertisement featuring a luxury home exterior during golden hour with perfect landscaping, glowing interior lights, and sophisticated architectural details.",
        "tags": ["exterior", "luxury home", "golden hour", "real estate", "architecture"],
        "is_premium": False,
        "meta_prompt": """\
Create a premium REAL ESTATE EXTERIOR advertisement photo for [YOUR PROPERTY / DEVELOPMENT NAME].

SUBJECT: The exterior façade of [YOUR PROPERTY TYPE — e.g., luxury villa / modern house / upscale apartment building / gated compound]. The architectural style is [YOUR STYLE — e.g., contemporary / Mediterranean / modern minimalist / classic]. Show the full front face of the property.

GOLDEN HOUR TIMING: Photographed at the "golden hour" — approximately 30 minutes after sunset (blue hour) OR 30 minutes before sunset. Interior lights are ON and glowing warmly through windows, creating a welcoming amber light that contrasts beautifully with the cool blue sky.

LANDSCAPING: Immaculate front garden / approach / grounds. [YOUR LANDSCAPING — e.g., manicured lawn / palm trees / stone pathway / water feature / flower borders] perfectly maintained.

SKY: [Golden-hour sky / Deep blue twilight / Perfect sunset gradients] — dramatic and aspirational. Not overcast.

FOREGROUND: A clean approach — [driveway / stone path / lawn edge] leads the eye toward the property.

LIGHTING: The warm interior glow from windows creates the hero lighting. Optional: subtle landscape lighting on plants/trees.

MOOD: Premium, aspirational, "dream home" quality — the kind of photo that makes someone stop scrolling.

FORMAT: Landscape 16:9 for property listings, or 4:5 for Instagram.

POST-PROCESSING: Balanced exposure between interior glow and exterior sky, enhanced sky colors, rich greens in landscaping.

⚙ Replace every [PLACEHOLDER] with your actual property description, architectural style, and key selling points.""",
    },
    {
        "category_slug": "realestate",
        "title": "Modern Interior — Luxury Living Space Ad",
        "image_url": "https://images.unsplash.com/photo-1555041469-149851472733?w=600&h=600&fit=crop&q=80",
        "description": "Magazine-quality interior design photograph of a luxury living room with designer furniture, floor-to-ceiling windows, and sophisticated décor that sells the lifestyle.",
        "tags": ["interior design", "luxury", "living room", "modern", "lifestyle"],
        "is_premium": True,
        "meta_prompt": """\
Create a LUXURY INTERIOR DESIGN advertisement photo for [YOUR PROPERTY / INTERIOR DESIGN COMPANY].

SUBJECT: A beautifully staged [YOUR ROOM TYPE — e.g., living room / master bedroom / kitchen / dining area / penthouse suite] interior. The space is designed in [YOUR STYLE — e.g., contemporary minimal / warm Scandinavian / rich maximalist / coastal luxury].

KEY DESIGN ELEMENTS TO SHOWCASE:
• [FURNITURE — e.g., designer sofa / statement dining table / king bed with linen]
• [ARCHITECTURAL FEATURE — e.g., floor-to-ceiling windows / exposed concrete / coffered ceiling / fireplace]
• [MATERIALS — e.g., marble / natural wood / polished concrete / luxury tile]
• [DECOR TOUCHES — e.g., art pieces / indoor plants / designer lighting / decorative objects]

STAGING: The space is lived-in but perfectly styled — [LIFE DETAILS — e.g., open coffee table book / bowl of fruit / throw blanket / candles lit]. Not sterile, but aspirational.

VIEWPOINT: [WIDE ANGLE from a corner showing the full room depth] OR [a close-up vignette of the most beautiful detail]. Choose based on the room's strongest feature.

LIGHTING: [NATURAL DAYLIGHT from large windows creating long shadows] OR [EVENING AMBIANCE with warm pendant lights and candlelight]. Both create different moods.

MOOD: "I want to live here" — premium, sophisticated, aspirational.

FORMAT: Landscape 16:9 or square 1:1 for property marketing.

POST-PROCESSING: Accurate color rendering of materials, slightly lifted shadows to show detail, architectural photography standard.

⚙ Replace every [PLACEHOLDER] with your actual room, design style, and property selling points.""",
    },

    # ══════════════════════════════════════════════════════════
    # AUTOMOTIVE
    # ══════════════════════════════════════════════════════════
    {
        "category_slug": "automotive",
        "title": "Sports Car Reveal — Dramatic Studio Shot",
        "image_url": "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=600&h=600&fit=crop&q=80",
        "description": "High-impact automotive advertisement featuring a sports car in a dark dramatic studio environment with light painting, creating a premium car brand reveal aesthetic.",
        "tags": ["sports car", "studio", "dramatic", "dark", "automotive", "luxury"],
        "is_premium": False,
        "meta_prompt": """\
Create a dramatic AUTOMOTIVE REVEAL advertisement photo for [YOUR CAR BRAND / MODEL].

SUBJECT: [YOUR CAR — describe make, model, color]. The car is the absolute hero of the image — every reflective surface, every line, every design detail is captured perfectly.

PERSPECTIVE: [3/4 FRONT VIEW] — the most flattering angle for most cars. The car is positioned slightly off-center at approximately 30° to the camera.

STUDIO ENVIRONMENT: A completely dark studio — the car floats in darkness. The ONLY light source is [OPTION A: dramatic single-source hard light creating bold highlights and deep shadows that trace the car's design lines / OPTION B: multiple colored accent lights in your brand colors / OPTION C: a wide soft-box creating an even full-car reveal with perfect ground reflection].

GROUND: Highly polished [BLACK / DARK GREY] studio floor creates a perfect mirror reflection of the vehicle underneath.

LIGHT DESIGN: Strategic light strips highlight the car's key design elements — the hood line, door creases, wheel arches, and headlight signature. The headlights or taillights are ON, creating a lit-up signature.

COLOR PALETTE: The car color [YOUR CAR COLOR] is the hero color. Everything else is dark to make it pop.

MOOD: Premium launch event, automotive magazine, flagship model reveal.

FORMAT: Landscape 16:9 or 3:2 for automotive advertising.

POST-PROCESSING: Deep true blacks, brilliant specular reflections on car body, enhanced color depth, automotive-grade retouching.

⚙ Replace every [PLACEHOLDER] with your actual car make, model, color, and lighting concept.""",
    },
    {
        "category_slug": "automotive",
        "title": "Car On Road — Dynamic Motion Shot",
        "image_url": "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=600&h=600&fit=crop&q=80",
        "description": "Exciting motion-blur car advertisement taken alongside a moving vehicle, showing speed and agility with a blurred landscape background conveying freedom and performance.",
        "tags": ["motion blur", "driving", "speed", "outdoor", "dynamic", "performance"],
        "is_premium": True,
        "meta_prompt": """\
Create a DYNAMIC MOTION SHOT automotive advertisement for [YOUR CAR BRAND / MODEL].

TECHNIQUE: Pan shot — camera tracks alongside the moving car at the same speed, resulting in a SHARP car against a horizontally motion-blurred background. This technique is the gold standard for communicating speed and performance.

SUBJECT: [YOUR CAR] traveling at speed on [YOUR ROAD — e.g., mountain road / coastal highway / racetrack / urban boulevard]. The car is perfectly sharp — every design detail crisp. The wheels show rotational blur (spinning wheel effect using composite technique).

BACKGROUND: Strong horizontal motion blur — [YOUR LANDSCAPE — e.g., mountain trees / coastal cliffs / city lights / open countryside] stretched into pure motion lines. The faster the implied speed, the longer the blur streaks.

ANGLE: Low to the ground, camera level with the car's midpoint. Slightly below the car horizon to give it a powerful, imposing stance.

LIGHTING: [OPTION A: Overcast outdoor diffused light — perfect for showing paint color accurately / OPTION B: Golden hour light raking across the car body — dramatic and aspirational].

ENVIRONMENT: The road and landscape should suggest the car's character — [sports car → mountain pass / SUV → open road / luxury sedan → city boulevard].

MOOD: Freedom, performance, engineering excellence.

FORMAT: Wide landscape 16:9 or 3:2.

POST-PROCESSING: Sharpen car details maximally, enhance motion blur in background, lift car color saturation, add subtle road dust/gravel spray if appropriate.

⚙ Replace every [PLACEHOLDER] with your actual car model, road type, and performance story.""",
    },

    # ══════════════════════════════════════════════════════════
    # HEALTH & PHARMACY
    # ══════════════════════════════════════════════════════════
    {
        "category_slug": "health",
        "title": "Supplement Product — Clean Health Ad",
        "image_url": "https://images.unsplash.com/photo-1584308666744-22e136e9e7b3?w=600&h=600&fit=crop&q=80",
        "description": "Clean professional health product advertisement showing supplement bottles and capsules with fresh natural ingredients, conveying trust, quality, and natural wellness.",
        "tags": ["supplements", "health", "clean", "natural", "wellness", "pharmacy"],
        "is_premium": False,
        "meta_prompt": """\
Create a HEALTH PRODUCT ADVERTISEMENT photo for [YOUR SUPPLEMENT / HEALTH PRODUCT BRAND].

SUBJECT: [YOUR PRODUCT — e.g., supplement bottle / vitamin jar / capsule blister pack / health drink] as the hero, positioned center-left. One or two matching products from the same line positioned in the background, slightly out of focus.

PRODUCT CONTEXT: Around the main product, include natural ingredients that communicate its benefits:
[YOUR INGREDIENTS — e.g., for Omega-3: fish / flaxseeds / walnuts; for Vitamin C: oranges / lemons; for Magnesium: dark chocolate / nuts; for Collagen: berries / bone broth elements].

SURFACE: Clean [WHITE / LIGHT STONE / NATURAL WOOD] surface. The surface feels hygienic and premium.

BACKGROUND: Clean white or off-white — seamless gradient. No background distractions.

LIGHTING: Soft even studio light from above-left. Products are well-lit with labels clearly readable. Ingredients cast soft natural shadows showing authenticity.

COMPOSITION: Product label is fully visible and readable at the center of the frame.

MOOD: Trust, clinical quality, natural wellness, premium health supplement.

SECONDARY TEXT SPACE: Leave space beside or below the product for:
• "[KEY BENEFIT — e.g., Supports Immunity]"
• "[NUMBER — e.g., 60 Capsules / 30 Servings]"
• The brand name

FORMAT: Square 1:1 or portrait 4:5.

POST-PROCESSING: Clean, bright, true colors — especially important for label accuracy. Slight shadow to give 3D depth to the bottle.

⚙ Replace every [PLACEHOLDER] with your actual product name, ingredients, health benefits, and brand details.""",
    },
    {
        "category_slug": "health",
        "title": "Wellness Lifestyle — Active Health Ad",
        "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=600&h=600&fit=crop&q=80",
        "description": "Energetic wellness lifestyle advertisement featuring an active person in a bright natural setting, conveying vitality, health, and the active lifestyle your brand supports.",
        "tags": ["wellness", "active", "lifestyle", "healthy", "energy", "fitness"],
        "is_premium": True,
        "meta_prompt": """\
Create a WELLNESS LIFESTYLE advertisement photo connecting [YOUR HEALTH PRODUCT / BRAND] to an active, healthy life.

CONCEPT: Instead of showing just the product, show the RESULT — a person living their best, healthiest life, made possible by [YOUR PRODUCT'S KEY BENEFIT — e.g., more energy / better sleep / stronger immunity / joint health].

SUBJECT: A [GENDER / AGE GROUP — e.g., woman 30s / man 40s / young person] in [ACTIVITY — e.g., morning run in a park / yoga on a rooftop / cycling through a city / gardening / hiking a trail]. They are energetic, smiling, and clearly in peak health.

PRODUCT PLACEMENT: [SUBTLE OPTION: The product appears in the corner of the image — perhaps in their hand / bag / beside them as they rest / NONE: just the lifestyle image, product shown in text overlay].

ENVIRONMENT: [YOUR CHOSEN SETTING — e.g., bright green park / sunny beach / urban rooftop at sunrise / forest trail]. The environment is clean, natural, aspirational.

LIGHTING: Bright, natural, energetic — [MORNING LIGHT / GOLDEN HOUR / CLEAR MIDDAY SUN]. High-key and positive.

MOOD: Vitality, energy, healthy living, life in motion.

COLORS: Fresh, natural, energetic — [GREENS / BLUES / YELLOWS / WHITES]. Bright and optimistic.

FORMAT: Horizontal 16:9 (wide banner ad) or portrait 4:5.

POST-PROCESSING: Bright, high-energy editing. Vivid but natural colors. Clean skin, clear eyes.

SPACE FOR TEXT: Leave the upper area or one side clear for:
• "[YOUR BRAND TAGLINE]"
• "[PRODUCT BENEFIT CLAIM]"
• Product image

⚙ Replace every [PLACEHOLDER] with your actual product, health claim, target audience, and brand message.""",
    },

    # ══════════════════════════════════════════════════════════
    # ELECTRONICS
    # ══════════════════════════════════════════════════════════
    {
        "category_slug": "electronics",
        "title": "Laptop Hero — Clean Tech Product Shot",
        "image_url": "https://images.unsplash.com/photo-1498049794561-7780e7231661?w=600&h=600&fit=crop&q=80",
        "description": "Premium laptop advertisement with an open device showing a vibrant screen display, positioned on a clean minimal desk setup with modern accessories and soft ambient lighting.",
        "tags": ["laptop", "tech", "minimal", "clean", "product shot", "screen"],
        "is_premium": False,
        "meta_prompt": """\
Create a clean premium TECH PRODUCT ADVERTISEMENT photo for [YOUR LAPTOP / COMPUTER / TECH DEVICE BRAND].

SUBJECT: [YOUR DEVICE — e.g., laptop / desktop / monitor / keyboard] positioned as the hero. If it's a laptop: lid open at approximately 110° angle, screen displaying [YOUR SCREEN CONTENT — e.g., your branded wallpaper / software UI / a design in progress / your website / video content].

DEVICE DETAILS: The device color is [YOUR COLOR — e.g., space grey / silver / midnight / rose gold]. Show the device at a [45° ANGLE / STRAIGHT ON / 3/4 VIEW] — whichever shows its design language best.

DESK SETUP: The device sits on a clean [WHITE / LIGHT WOOD / DARK MINIMAL] desk surface. Minimal accessories: [YOUR SUPPORTING ITEMS — e.g., wireless mouse / notebook / coffee cup / small plant / AirPods case]. Each accessory is intentionally placed, not cluttered.

BACKGROUND: Clean [WHITE WALL / CONCRETE WALL / DARK MINIMAL ROOM]. No distractions.

LIGHTING: [OPTION A: Clean even studio light — best for product clarity / OPTION B: Natural window side-light creating atmospheric shadows — best for lifestyle feel].

MOOD: Productivity, innovation, premium tech, modern professional.

FORMAT: Landscape 16:9 or square 1:1.

POST-PROCESSING: Clean, accurate product colors, sharp device details, screen is visible and color-accurate.

⚙ Replace every [PLACEHOLDER] with your actual device model, color, screen content, and desk setup.""",
    },
    {
        "category_slug": "electronics",
        "title": "Gaming Setup — Neon RGB Atmosphere",
        "image_url": "https://images.unsplash.com/photo-1555255707-c07966088b7b?w=600&h=600&fit=crop&q=80",
        "description": "Immersive gaming setup advertisement with RGB lighting, dual monitors, mechanical keyboard, and gaming chair creating an exciting high-performance gaming environment ad.",
        "tags": ["gaming", "RGB", "setup", "neon", "atmosphere", "electronics"],
        "is_premium": True,
        "meta_prompt": """\
Create a PREMIUM GAMING SETUP advertisement for [YOUR GAMING BRAND / PRODUCT].

SUBJECT: A high-performance gaming setup featuring [YOUR PRODUCT — e.g., gaming monitor / keyboard / mouse / headset / PC case] as the hero. The setup includes:
• [YOUR MAIN PRODUCT] prominently positioned
• [YOUR MONITORS — e.g., dual curved monitors / ultrawide / 144Hz display] showing a game or branded screen
• [YOUR PERIPHERALS — e.g., mechanical keyboard / gaming mouse / headset] in matching brand aesthetic
• [YOUR CHAIR — e.g., ergonomic gaming chair / racing seat] partially visible if space allows

RGB LIGHTING: The entire setup is illuminated by [YOUR RGB COLOR SCHEME — e.g., electric blue / neon purple / aggressive red / cool white]. RGB flows across:
• Case/tower side panel (if PC)
• Keyboard per-key RGB in [YOUR PATTERN]
• Monitor ambient backlight
• Desk underglow / LED strips

ENVIRONMENT: Dark room with dramatic RGB ambient light. The room itself is dark — the setup glows. Background: dark wall or blurred dark room.

LIGHTING: Near-darkness except for RGB glow. The screen provides front-fill light. Accent LED strips provide colored ambient.

MOOD: High performance, next-level gaming, premium eSports aesthetic.

FORMAT: Landscape 16:9 or wide 21:9.

POST-PROCESSING: Enhance RGB glow and light bleed, deep true blacks, vivid neon colors, high contrast.

⚙ Replace every [PLACEHOLDER] with your actual products, RGB color scheme, and gaming aesthetic.""",
    },

    # ══════════════════════════════════════════════════════════
    # TOOLS & HARDWARE
    # ══════════════════════════════════════════════════════════
    {
        "category_slug": "tools",
        "title": "Power Tools Flat Lay — Industrial Style Ad",
        "image_url": "https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=600&h=600&fit=crop&q=80",
        "description": "Professional flat-lay advertisement of premium power tools and hand tools arranged on a dark industrial surface, with dramatic sidelighting that emphasizes quality craftsmanship.",
        "tags": ["power tools", "flat lay", "industrial", "professional", "hardware"],
        "is_premium": False,
        "meta_prompt": """\
Create a professional TOOLS FLAT LAY advertisement for [YOUR TOOL BRAND / HARDWARE STORE].

SUBJECT: A curated flat-lay arrangement of [YOUR TOOLS — e.g., power drill / circular saw / impact driver / tool set] on a [SURFACE — e.g., dark steel / weathered wood / concrete floor / metal workbench]. Arrange tools in a systematic, intentional composition — not random.

ARRANGEMENT OPTIONS:
• [OPTION A: GRID LAYOUT] — tools aligned in rows and columns, perfectly parallel
• [OPTION B: RADIAL LAYOUT] — tools arranged radiating outward from a center point
• [OPTION C: SCATTERED PROFESSIONAL] — tools laid out as if being used, but artfully so

PROPS: Include supporting elements relevant to the trade: [YOUR PROPS — e.g., measuring tape / safety goggles / work gloves / metal shavings / wood pieces / nails and screws in small piles]. These add authenticity.

LIGHTING: Dramatic raking side-light from one side — creates long shadows and highlights every surface texture and material quality of the tools.

SURFACE: Dark, textured — [AGED CONCRETE / DARK METAL / ROUGH WOOD]. The darkness makes the tools pop and communicates industrial strength.

COLOR PALETTE: [YOUR BRAND COLORS — e.g., DeWalt yellow-black / Bosch blue / Milwaukee red-black] as the dominant color against the dark surface.

MOOD: Professional, durable, trustworthy craftsmanship.

FORMAT: Square 1:1 or landscape for tool catalog pages.

POST-PROCESSING: High sharpness on tool details, enhanced brand color vibrancy, dramatic shadow/highlight contrast.

⚙ Replace every [PLACEHOLDER] with your actual tools, brand colors, and professional context.""",
    },
    {
        "category_slug": "tools",
        "title": "Craftsman In Action — Workshop Lifestyle Ad",
        "image_url": "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=600&h=600&fit=crop&q=80",
        "description": "Authentic workshop lifestyle advertisement showing a skilled craftsman using professional tools with dramatic industrial lighting, sawdust in the air, and genuine craftsmanship quality.",
        "tags": ["craftsman", "workshop", "lifestyle", "action", "industrial", "authentic"],
        "is_premium": True,
        "meta_prompt": """\
Create an AUTHENTIC CRAFTSMAN IN ACTION advertisement for [YOUR TOOL BRAND / TRADE BUSINESS].

SUBJECT: A [PROFESSIONAL — e.g., carpenter / woodworker / electrician / plumber / mechanic] actively using [YOUR TOOL — e.g., electric drill / power saw / grinder / wrench] in their workspace. The focus is on the TOOL in action and the skilled hands operating it — the craftsman's face may be partially out of frame or turned, keeping the tool as the hero.

ACTION MOMENT: Capture a genuine work moment — [OPTION A: Drilling/cutting in progress with sawdust/sparks flying / OPTION B: Close-up of hands tightening a joint with the tool / OPTION C: Tool held at the moment before applying it to the material].

PARTICLES: If cutting/grinding/drilling — particles [sawdust / metal sparks / dust] frozen in mid-air add authenticity and dynamism.

WORKSPACE: [YOUR TRADE ENVIRONMENT — e.g., woodshop with workshop equipment in background / garage workshop / construction site / engine bay]. The background is blurred but clearly recognizable as a professional environment.

LIGHTING: Dramatic industrial lighting — [HARD WORKSHOP LIGHT / WINDOW LIGHT / SPOTLIGHT ON WORKING AREA]. Strong shadows show the physical nature of the work.

MOOD: Skill, durability, trust, professional-grade quality — this tool is built for real work.

FORMAT: Landscape 16:9 or horizontal 4:3.

POST-PROCESSING: Gritty, authentic processing — not overly polished. Enhance tool brand colors, sharp tool-metal details.

⚙ Replace every [PLACEHOLDER] with your actual trade, specific tool, and professional context.""",
    },
]

# ─── Helpers ───────────────────────────────────────────────

def get_category_map():
    res = sb.table("categories").select("id, slug").execute()
    return {r["slug"]: r["id"] for r in (res.data or [])}

def style_exists(title: str) -> bool:
    res = sb.table("ad_styles").select("id").eq("title", title).execute()
    return bool(res.data)

# ─── Main ──────────────────────────────────────────────────

def main():
    print("\n🎨 Adding styles for all categories\n" + "─" * 45)

    cat_map = get_category_map()
    if not cat_map:
        print("❌ No categories found — run upload_styles.py first")
        return

    ok = skipped = failed = 0

    for style in STYLES:
        title = style["title"]
        slug = style["category_slug"]

        if style_exists(title):
            print(f"  ℹ️  Already exists: {title}")
            skipped += 1
            continue

        cat_id = cat_map.get(slug)
        if not cat_id:
            print(f"  ❌ Category '{slug}' not in DB: {title}")
            failed += 1
            continue

        try:
            sb.table("ad_styles").insert({
                "category_id": cat_id,
                "title":       title,
                "image_url":   style["image_url"],
                "meta_prompt": style["meta_prompt"],
                "description": style["description"],
                "tags":        style["tags"],
                "is_premium":  style["is_premium"],
            }).execute()
            print(f"  ✅ Added: {title}")
            ok += 1
        except Exception as e:
            print(f"  ❌ Failed: {title} → {e}")
            failed += 1

    print("\n" + "─" * 45)
    print(f"Done!  ✅ {ok} added  |  ℹ️ {skipped} skipped  |  ❌ {failed} failed\n")


if __name__ == "__main__":
    main()
