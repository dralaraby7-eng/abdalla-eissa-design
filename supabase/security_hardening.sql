-- ============================================================
-- security_hardening.sql
-- Run this after the existing schema/fix scripts.
--
-- Goals:
-- - Stop browser clients from changing admin/premium profile fields.
-- - Stop browser clients from reading full premium prompts directly.
-- - Record Paymob orders so webhooks can verify payment details before
--   granting premium.
-- ============================================================

-- Public-safe prompt preview. Keep the full prompt in meta_prompt for the
-- backend service-role API only.
ALTER TABLE public.ad_styles
  ADD COLUMN IF NOT EXISTS prompt_preview text;

ALTER TABLE public.ad_styles
  ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true;

UPDATE public.ad_styles
SET prompt_preview = left(meta_prompt, 140)
WHERE prompt_preview IS NULL AND meta_prompt IS NOT NULL;

CREATE OR REPLACE FUNCTION public.set_prompt_preview()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.prompt_preview := left(COALESCE(NEW.meta_prompt, ''), 140);
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS set_prompt_preview_before_write ON public.ad_styles;
CREATE TRIGGER set_prompt_preview_before_write
  BEFORE INSERT OR UPDATE OF meta_prompt ON public.ad_styles
  FOR EACH ROW EXECUTE FUNCTION public.set_prompt_preview();

-- Pending/paid payment records. The backend writes this with the service key.
CREATE TABLE IF NOT EXISTS public.payment_orders (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  email text NOT NULL,
  paymob_order_id text UNIQUE NOT NULL,
  merchant_order_id text UNIQUE NOT NULL,
  amount_cents integer NOT NULL,
  currency text NOT NULL DEFAULT 'EGP',
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'failed')),
  transaction_id text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE public.payment_orders ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "payment_orders_no_client_access" ON public.payment_orders;
CREATE POLICY "payment_orders_no_client_access" ON public.payment_orders
  FOR ALL USING (false) WITH CHECK (false);

-- Client profile updates may only touch non-sensitive profile fields.
REVOKE INSERT, DELETE ON public.profiles FROM anon, authenticated;
REVOKE UPDATE ON public.profiles FROM anon, authenticated;
GRANT UPDATE (full_name) ON public.profiles TO authenticated;

DROP POLICY IF EXISTS "profiles_own_update" ON public.profiles;
CREATE POLICY "profiles_own_update" ON public.profiles
  FOR UPDATE USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Browser clients can read public style metadata, but not meta_prompt.
REVOKE SELECT ON public.ad_styles FROM anon, authenticated;
GRANT SELECT (
  id,
  category_id,
  title,
  image_url,
  prompt_preview,
  description,
  tags,
  is_premium,
  is_active,
  view_count,
  created_at
) ON public.ad_styles TO anon, authenticated;

DROP POLICY IF EXISTS "styles_public_read" ON public.ad_styles;
CREATE POLICY "styles_public_read" ON public.ad_styles
  FOR SELECT USING (is_active = true);

DROP POLICY IF EXISTS "styles_admin_all" ON public.ad_styles;
CREATE POLICY "styles_admin_all" ON public.ad_styles
  FOR ALL USING (public.is_admin_user());

DROP POLICY IF EXISTS "styles_admin_insert" ON public.ad_styles;
CREATE POLICY "styles_admin_insert" ON public.ad_styles
  FOR INSERT WITH CHECK (public.is_admin_user());

-- Admin/category/style writes now go through the backend service-role API.
REVOKE INSERT, UPDATE, DELETE ON public.categories FROM anon, authenticated;
REVOKE INSERT, UPDATE, DELETE ON public.ad_styles FROM anon, authenticated;

-- View count writes are allowed for signed-in users only.
REVOKE EXECUTE ON FUNCTION public.increment_view_count(uuid) FROM anon;
GRANT EXECUTE ON FUNCTION public.increment_view_count(uuid) TO authenticated;

-- Keep category reads public.
GRANT SELECT ON public.categories TO anon, authenticated;

-- Service role keeps full access for backend routes and scripts.
GRANT ALL ON public.profiles TO service_role;
GRANT ALL ON public.categories TO service_role;
GRANT ALL ON public.ad_styles TO service_role;
GRANT ALL ON public.payment_orders TO service_role;
