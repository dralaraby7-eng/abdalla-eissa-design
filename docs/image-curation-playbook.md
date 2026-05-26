# Image Curation Playbook

Goal: keep only 30 highly attractive styles per category, with images strong
enough that users want the meta prompt.

## Recommended Low-Cost Pipeline

1. Run the database hardening/visibility migration.

   ```powershell
   python run_sql.py supabase/security_hardening.sql
   ```

   If the RPC helper is not available in Supabase, paste
   `supabase/security_hardening.sql` into the Supabase SQL Editor.

2. Preview candidates without changing the database.

   ```powershell
   python curate_distinguished_images.py --source pexels --per-cat 30 --oversample 240 --dry-run
   ```

3. Curate one category first and inspect it in the app.

   ```powershell
   python curate_distinguished_images.py --source pexels --category beauty --per-cat 30 --hide-existing
   ```

4. If the category looks good, run all categories.

   ```powershell
   python curate_distinguished_images.py --source pexels --per-cat 30 --hide-existing
   ```

5. If Pexels results are not good enough, run `--source multi` after adding
   Pixabay and/or Unsplash keys to `.env`.

   ```powershell
   python curate_distinguished_images.py --source multi --per-cat 30 --oversample 300 --hide-existing
   ```

## Source Strategy

Use Pexels first. It is free, allows 200 requests/hour and 20,000/month by
default, and the visual quality is usually better than Pixabay for advertising
style images.

Use Unsplash only as an enhancer. Its demo API limit is 50 requests/hour, but
the photography is often stronger. It is good for luxury, real estate, fashion,
coffee, automotive, and beauty.

Use Pixabay as backup volume. It has many assets and popularity signals, but
many results are generic, so it should be filtered rather than trusted directly.

## Quality Rules

The script does not search only for objects like "burger" or "phone". It searches
for visual styles such as "dramatic product advertising", "editorial campaign",
"luxury still life", "splash commercial photography", and "hero shot".

It over-collects candidates, scores them, then inserts only the best 30. Old
styles are hidden with `is_active=false`, not deleted, so they can be restored.

## Premium Split

Default:

- First 5 images per category: free preview content.
- Remaining 25 images per category: premium.

This gives users enough quality to trust the product, while keeping most value
behind Premium.

## Cost Control

The expensive step is generating meta prompts from images. The script ranks
first and generates prompts only for the final selected images.

For 12 categories x 30 images = 360 prompt generations. Gemini free tier may be
enough for this if paced slowly. OpenRouter is the fallback if Gemini hits quota.
