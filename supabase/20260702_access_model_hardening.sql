-- One-category standard accounts, prompt integrity, and query hardening.

-- Keep only the newest active category if legacy data contains duplicates.
with ranked_access as (
  select id, row_number() over (partition by user_id order by created_at desc, id desc) as position
  from public.user_category_access
  where status = 'active'
)
update public.user_category_access access
set status = 'revoked', updated_at = now()
from ranked_access ranked
where access.id = ranked.id and ranked.position > 1;

create unique index if not exists user_category_access_one_active_per_user
  on public.user_category_access (user_id)
  where status = 'active';

create index if not exists ad_styles_category_id_idx on public.ad_styles (category_id);
create index if not exists payment_orders_user_id_idx on public.payment_orders (user_id);
create index if not exists payment_orders_category_id_idx on public.payment_orders (category_id);
create index if not exists prompt_views_style_id_idx on public.prompt_views (style_id);
create index if not exists user_category_access_category_id_idx on public.user_category_access (category_id);

alter table public.ad_styles alter column json_prompt set not null;

-- RLS limits rows, while column privileges prevent users from changing plan/admin fields.
revoke update on table public.profiles from anon, authenticated;
grant update (full_name) on table public.profiles to authenticated;

alter function public.increment_view_count(uuid) set search_path = public;
alter function public.set_prompt_preview() set search_path = public;

revoke execute on function public.handle_new_user() from public, anon, authenticated;
revoke execute on function public.set_prompt_preview() from public, anon, authenticated;
revoke execute on function public.increment_view_count(uuid) from public, anon, authenticated;
grant execute on function public.increment_view_count(uuid) to service_role;

revoke execute on function public.ensure_profile() from public, anon;
grant execute on function public.ensure_profile() to authenticated;

revoke execute on function public.is_admin_user() from public;
revoke execute on function public.is_admin_user() from anon, authenticated;
grant execute on function public.is_admin_user() to service_role;

revoke execute on function public.rls_auto_enable() from public, anon, authenticated;

drop policy if exists "profiles_own_read" on public.profiles;
drop policy if exists "profiles_admin_read_all" on public.profiles;
create policy "profiles_own_read" on public.profiles
  for select using ((select auth.uid()) = id);

drop policy if exists "profiles_own_update" on public.profiles;
create policy "profiles_own_update" on public.profiles
  for update using ((select auth.uid()) = id)
  with check ((select auth.uid()) = id);

drop policy if exists "profiles_insert" on public.profiles;

drop policy if exists "category_access_own_read" on public.user_category_access;
drop policy if exists "category_access_admin_all" on public.user_category_access;
create policy "category_access_own_read" on public.user_category_access
  for select using ((select auth.uid()) = user_id);

drop policy if exists "prompt_views_own" on public.prompt_views;
create policy "prompt_views_own" on public.prompt_views
  for all using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "styles_admin_insert" on public.ad_styles;
drop policy if exists "styles_admin_all" on public.ad_styles;
drop policy if exists "categories_admin_all" on public.categories;
