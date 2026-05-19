-- ============================================================
-- fix_rls.sql — Run this in Supabase SQL Editor
-- Fixes the recursive admin policy and grants RPC access
-- ============================================================

-- 1. Security-definer function to check admin without recursion
-- ─────────────────────────────────────────────────────────────
create or replace function public.is_admin_user()
returns boolean
language sql
security definer          -- bypasses RLS, runs as function owner
stable
set search_path = public
as $$
  select coalesce(
    (select is_admin from public.profiles where id = auth.uid() limit 1),
    false
  );
$$;

-- Grant to both roles so it works for all requests
grant execute on function public.is_admin_user() to anon, authenticated;


-- 2. Replace recursive policies with function-based ones
-- ─────────────────────────────────────────────────────────────

-- Profiles
drop policy if exists "profiles_admin_read_all" on public.profiles;
create policy "profiles_admin_read_all" on public.profiles
  for select using (public.is_admin_user());

-- Categories
drop policy if exists "categories_admin_all" on public.categories;
create policy "categories_admin_all" on public.categories
  for all using (public.is_admin_user());

-- Ad Styles
drop policy if exists "styles_admin_all" on public.ad_styles;
create policy "styles_admin_all" on public.ad_styles
  for all using (public.is_admin_user());


-- 3. Allow anon/authenticated to call view count RPC
-- ─────────────────────────────────────────────────────────────
grant execute on function public.increment_view_count(uuid) to anon, authenticated;


-- 4. Allow authenticated users to update their own profile
-- ─────────────────────────────────────────────────────────────
drop policy if exists "profiles_own_update" on public.profiles;
create policy "profiles_own_update" on public.profiles
  for update using (auth.uid() = id)
  with check (auth.uid() = id);


-- Done! Verify with:
-- select polname, polcmd from pg_policies where tablename in ('profiles','categories','ad_styles');
