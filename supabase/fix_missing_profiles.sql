-- ============================================================
-- fix_missing_profiles.sql — Run in Supabase SQL Editor
--
-- Problem: some users exist in auth.users but have no row in
-- public.profiles, so the frontend treats them as anonymous after
-- login. This happens when the on_auth_user_created trigger was
-- never (re)created after schema migrations, or when a previous
-- version of the trigger raised an exception silently.
--
-- This migration is idempotent — safe to run as many times as you like.
-- ============================================================

-- 1. Make sure email column exists
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS email text;

-- 2. Back-fill missing profile rows for every auth.users row
INSERT INTO public.profiles (id, full_name, email, plan_type)
SELECT
  u.id,
  COALESCE(u.raw_user_meta_data->>'full_name', split_part(u.email, '@', 1)),
  u.email,
  'free'
FROM auth.users u
LEFT JOIN public.profiles p ON p.id = u.id
WHERE p.id IS NULL;

-- 3. Back-fill emails for existing profiles missing them
UPDATE public.profiles p
SET email = u.email
FROM auth.users u
WHERE p.id = u.id AND p.email IS NULL;

-- 4. Recreate the trigger function with EXCEPTION handling so a
--    failure here can't ever block a signup.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name, email, plan_type)
  VALUES (
    new.id,
    COALESCE(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)),
    new.email,
    'free'
  )
  ON CONFLICT (id) DO UPDATE SET
    full_name = COALESCE(EXCLUDED.full_name, public.profiles.full_name),
    email     = COALESCE(EXCLUDED.email,     public.profiles.email);
  RETURN new;
EXCEPTION
  WHEN OTHERS THEN
    RAISE WARNING 'handle_new_user failed for %: %', new.id, SQLERRM;
    RETURN new;
END;
$$;

-- 5. Drop + recreate the trigger to make sure it's actually wired up
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 6. Self-healing RPC the frontend can call on every login.
--    If the profile row is missing (trigger never fired, or fired
--    before email column existed, etc.), this creates it now.
CREATE OR REPLACE FUNCTION public.ensure_profile()
RETURNS public.profiles
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  result public.profiles;
BEGIN
  INSERT INTO public.profiles (id, full_name, email, plan_type)
  SELECT
    auth.uid(),
    COALESCE(u.raw_user_meta_data->>'full_name', split_part(u.email, '@', 1)),
    u.email,
    'free'
  FROM auth.users u
  WHERE u.id = auth.uid()
  ON CONFLICT (id) DO UPDATE SET
    email = COALESCE(EXCLUDED.email, public.profiles.email)
  RETURNING * INTO result;

  RETURN result;
END;
$$;

GRANT EXECUTE ON FUNCTION public.ensure_profile() TO authenticated;

-- 7. Verify — show counts before/after. Should be equal.
SELECT
  (SELECT count(*) FROM auth.users)        AS auth_users,
  (SELECT count(*) FROM public.profiles)   AS profiles,
  (SELECT count(*) FROM public.profiles WHERE email IS NULL) AS profiles_missing_email;
