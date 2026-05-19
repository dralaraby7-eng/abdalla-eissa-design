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

## Free vs Premium

| Feature | Free | Premium |
|---|---|---|
| Browse categories | ✅ | ✅ |
| View style images | ✅ | ✅ |
| Prompt preview (140 chars) | ✅ | ✅ |
| Copy full prompt | ❌ | ✅ |
| Premium-only styles | ❌ | ✅ |
| New styles weekly | ❌ | ✅ |

---

## Local Development

Open `frontend/index.html` directly in a browser, or use VS Code Live Server extension (recommended — right-click `index.html` → Open with Live Server).
