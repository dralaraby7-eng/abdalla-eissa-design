-- Add email column to profiles and update the new-user trigger
-- Run this in: Supabase Dashboard → SQL Editor → Run

ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS email text;

-- Back-fill emails for existing users from auth.users
UPDATE public.profiles p
SET email = u.email
FROM auth.users u
WHERE p.id = u.id AND p.email IS NULL;

-- Update trigger so future sign-ups also save email
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name, email)
  VALUES (
    new.id,
    new.raw_user_meta_data->>'full_name',
    new.email
  )
  ON CONFLICT (id) DO UPDATE SET
    full_name = COALESCE(EXCLUDED.full_name, profiles.full_name),
    email     = COALESCE(EXCLUDED.email,     profiles.email);
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
