# Abdalla Eissa for Design

AI-powered ad design template platform. Browse ad style galleries by category, click a style to get a ready-to-use AI meta prompt, and generate your own branded ad using any AI image model.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5 / CSS3 / Vanilla JavaScript |
| Database + Auth + Storage | Supabase (PostgreSQL + Auth + Storage) |
| Backend API | Python FastAPI |
| Payments | Paymob |
| Deploy | Vercel (frontend) + Render (backend) |

---

## Project Structure

```
App 1/
├── supabase/
│   └── schema.sql          ← Run this first in Supabase SQL Editor
├── frontend/
│   ├── index.html          ← Home: category grid
│   ├── category.html       ← Style gallery for a category
│   ├── prompt.html         ← Full prompt viewer
│   ├── auth.html           ← Login / Sign Up
│   ├── pricing.html        ← Plans & payment
│   ├── dashboard.html      ← User account
│   ├── admin.html          ← Admin panel (admin users only)
│   ├── css/main.css
│   └── js/
│       ├── config.js       ← Supabase URL/key (edit this)
│       ├── auth.js         ← Auth state management
│       ├── home.js
│       ├── category.js
│       ├── prompt.js
│       └── admin.js
└── backend/
    ├── main.py             ← FastAPI entry point
    ├── routes/payments.py  ← Paymob integration
    ├── requirements.txt
    └── .env.example        ← Copy to .env and fill values
```

---

## Setup

### 1. Supabase Project

1. Go to [supabase.com](https://supabase.com) → New project
2. Open **SQL Editor** → paste contents of `supabase/schema.sql` → Run
   - This schema is security-first: browser clients can only read public prompt previews, while full prompts are returned by the FastAPI backend after access checks.
   - If you already created the database from an older version, run `supabase/fix_rls.sql`, `supabase/fix_missing_profiles.sql`, then `supabase/security_hardening.sql`.
3. Go to **Project Settings → API** → copy your:
   - `Project URL`
   - `anon public` key  
   - `service_role` key (backend only — never in frontend)

### 2. Frontend Config

Edit `frontend/js/config.js`:

```js
const SUPABASE_URL  = 'https://YOUR_PROJECT_ID.supabase.co';
const SUPABASE_ANON = 'YOUR_ANON_PUBLIC_KEY';
const API_URL       = 'https://your-backend.onrender.com';  // or localhost:8000
```

### 3. Backend

```bash
cd backend
cp .env.example .env
# Fill in .env with your Supabase + Paymob credentials

pip install -r requirements.txt
python main.py
# API runs on http://localhost:8000
```

### 4. Make yourself Admin

After signing up with your email, run this in Supabase SQL Editor:

```sql
UPDATE public.profiles
SET is_admin = true
WHERE id = (SELECT id FROM auth.users WHERE email = 'your@email.com');
```

Then log in and navigate to `admin.html` to manage categories and styles.

### 5. Add Ad Styles

1. In the Admin panel → **Upload images** to Supabase Storage (bucket: `style-images`)
2. Copy the public URL of each uploaded image
3. In Admin → **Add Style** → paste the URL, write the meta prompt, choose category

### 6. Curate Distinguished Images

Use `curate_distinguished_images.py` to replace generic/random images with a
stronger 30-image catalog per category. Start with a dry run:

```bash
python curate_distinguished_images.py --source pexels --per-cat 30 --oversample 240 --dry-run
```

Then test one category before replacing all visible styles:

```bash
python curate_distinguished_images.py --source pexels --category beauty --per-cat 30 --hide-existing
python curate_distinguished_images.py --source pexels --per-cat 30 --hide-existing
```

Full process: `docs/image-curation-playbook.md`.

---

## Paymob Setup

1. Create account at [paymob.com](https://paymob.com)
2. Get your API key from **Settings → Account Info**
3. Create a **Card Payments** integration → note the Integration ID
4. Create an iframe → note the iFrame ID
5. Set the webhook URL to: `https://your-backend.onrender.com/api/payments/webhook`
6. Fill in your `.env` file with these values

---

## Deploy

### Frontend (Vercel)
```bash
# From root directory
npx vercel --root frontend
```
Or drag the `frontend/` folder to [vercel.com](https://vercel.com).

### Backend (Render)
1. Push to GitHub
2. New Web Service on [render.com](https://render.com)
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add all `.env` values as Environment Variables in Render dashboard

---

## Access Model

| Feature | Free | Category Pack | All Access |
|---|---|---|
| Browse categories | ✅ | ✅ | ✅ |
| View style images | ✅ | ✅ | ✅ |
| Prompt preview (140 chars) | ✅ | ✅ | ✅ |
| Copy full prompts in selected category | ❌ | ✅ | ✅ |
| Copy full prompts in all categories | ❌ | ❌ | ✅ |
| Premium-only styles | ❌ | Selected category | All categories |

Backend access checks are enforced in `/api/prompts/*`. The frontend lock UI is only a visual hint; it is not the security boundary.

### Category Delivery Pack

Users with access to every style in a category can download one ZIP from the
category page. It contains the source images, `prompts.csv`, an offline visual
`catalog.html`, and a short `README.txt`. Image downloads are restricted to the
configured Supabase host plus optional `IMAGE_DOWNLOAD_HOSTS` entries.

In production, Render must include the exact Vercel site URL in its CORS
allowlist. The application also includes the canonical production URL as a
fallback so prompt requests are not broken by a stale Render environment value.

---

## Local Development

Open `frontend/index.html` directly in a browser, or use VS Code Live Server extension (recommended — right-click `index.html` → Open with Live Server).
