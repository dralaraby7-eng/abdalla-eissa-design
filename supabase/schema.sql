-- ============================================================
-- Abdalla Eissa for Design - Supabase Schema
-- Run this in your Supabase SQL Editor
-- ============================================================

-- Categories
create table public.categories (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  slug text unique not null,
  icon text default '🎨',
  description text,
  cover_image_url text,
  display_order integer default 0,
  is_active boolean default true,
  created_at timestamptz default now()
);

-- Ad Styles
create table public.ad_styles (
  id uuid default gen_random_uuid() primary key,
  category_id uuid references public.categories(id) on delete cascade,
  title text not null,
  image_url text not null,
  meta_prompt text not null,
  normal_prompt text,
  json_prompt text,
  prompt_preview text,
  description text,
  tags text[] default '{}',
  is_premium boolean default false,
  is_active boolean default true,
  view_count integer default 0,
  created_at timestamptz default now()
);

-- User Profiles (extends Supabase auth.users)
create table public.profiles (
  id uuid references auth.users(id) on delete cascade primary key,
  email text,
  full_name text,
  plan_type text default 'free' check (plan_type in ('free', 'premium')),
  subscription_expires_at timestamptz,
  paymob_order_id text,
  is_admin boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Prompt Views (track free tier usage)
create table public.prompt_views (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) on delete cascade,
  style_id uuid references public.ad_styles(id) on delete cascade,
  created_at timestamptz default now(),
  unique(user_id, style_id)
);

-- Payment Orders (server-side Paymob verification)
create table public.payment_orders (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) on delete cascade not null,
  email text not null,
  paymob_order_id text unique not null,
  merchant_order_id text unique not null,
  amount_cents integer not null,
  currency text not null default 'EGP',
  status text not null default 'pending' check (status in ('pending', 'paid', 'failed')),
  transaction_id text,
  billing text default 'all_access_lifetime_egp',
  access_scope text not null default 'all' check (access_scope in ('all', 'category')),
  category_id uuid references public.categories(id) on delete set null,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Per-category access. Use this for selling Bakery only, Beauty only, etc.
create table public.user_category_access (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) on delete cascade not null,
  category_id uuid references public.categories(id) on delete cascade not null,
  source text default 'admin' check (source in ('admin', 'paymob', 'import')),
  status text not null default 'active' check (status in ('active', 'revoked')),
  expires_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(user_id, category_id)
);

-- ============================================================
-- Row Level Security
-- ============================================================

alter table public.categories enable row level security;
alter table public.ad_styles enable row level security;
alter table public.profiles enable row level security;
alter table public.prompt_views enable row level security;
alter table public.payment_orders enable row level security;
alter table public.user_category_access enable row level security;

-- Admin helper avoids recursive RLS policies on profiles.
create or replace function public.is_admin_user()
returns boolean
language sql
security definer
stable
set search_path = public
as $$
  select coalesce(
    (select is_admin from public.profiles where id = auth.uid() limit 1),
    false
  );
$$;

grant execute on function public.is_admin_user() to anon, authenticated;

-- Categories: public read
create policy "categories_public_read" on public.categories
  for select using (is_active = true);
create policy "categories_admin_all" on public.categories
  for all using (public.is_admin_user());

-- Ad styles: public metadata read only. Column grants below hide full prompts.
create policy "styles_public_read" on public.ad_styles
  for select using (is_active = true);
create policy "styles_admin_all" on public.ad_styles
  for all using (public.is_admin_user());

-- Profiles: own read/update
create policy "profiles_own_read" on public.profiles
  for select using (auth.uid() = id);
create policy "profiles_own_update" on public.profiles
  for update using (auth.uid() = id)
  with check (auth.uid() = id);
create policy "profiles_insert" on public.profiles
  for insert with check (auth.uid() = id);
create policy "profiles_admin_read_all" on public.profiles
  for select using (public.is_admin_user());

-- Prompt views: own
create policy "prompt_views_own" on public.prompt_views
  for all using (auth.uid() = user_id);

-- Payment orders: backend service role only
create policy "payment_orders_no_client_access" on public.payment_orders
  for all using (false) with check (false);

-- Category access: users may read their own access; writes go through backend service role/admin API.
create policy "category_access_own_read" on public.user_category_access
  for select using (auth.uid() = user_id);
create policy "category_access_admin_all" on public.user_category_access
  for all using (public.is_admin_user());

-- ============================================================
-- Auto-create profile on signup
-- ============================================================
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, full_name)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1))
  )
  on conflict (id) do update set
    email = coalesce(excluded.email, public.profiles.email),
    full_name = coalesce(excluded.full_name, public.profiles.full_name);
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Update view count when style is viewed
create or replace function public.increment_view_count(style_id uuid)
returns void as $$
  update public.ad_styles set view_count = view_count + 1 where id = style_id;
$$ language sql security definer;

create or replace function public.set_prompt_preview()
returns trigger
language plpgsql
as $$
begin
  new.meta_prompt := coalesce(nullif(new.meta_prompt, ''), nullif(new.normal_prompt, ''), '');
  new.normal_prompt := coalesce(nullif(new.normal_prompt, ''), new.meta_prompt);
  new.prompt_preview := left(coalesce(new.normal_prompt, new.meta_prompt, ''), 140);
  return new;
end;
$$;

create trigger set_prompt_preview_before_write
  before insert or update of meta_prompt, normal_prompt on public.ad_styles
  for each row execute function public.set_prompt_preview();

-- Self-healing profile RPC used by the frontend after login.
create or replace function public.ensure_profile()
returns public.profiles
language plpgsql
security definer
set search_path = public
as $$
declare
  result public.profiles;
begin
  insert into public.profiles (id, email, full_name, plan_type)
  select
    auth.uid(),
    u.email,
    coalesce(u.raw_user_meta_data->>'full_name', split_part(u.email, '@', 1)),
    'free'
  from auth.users u
  where u.id = auth.uid()
  on conflict (id) do update set
    email = coalesce(excluded.email, public.profiles.email)
  returning * into result;

  return result;
end;
$$;

grant execute on function public.ensure_profile() to authenticated;

-- Browser clients must never read full prompt bodies directly from Supabase.
revoke select on public.ad_styles from anon, authenticated;
grant select (
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
) on public.ad_styles to anon, authenticated;

-- Browser clients may update only safe profile fields.
revoke insert, delete on public.profiles from anon, authenticated;
revoke update on public.profiles from anon, authenticated;
grant update (full_name) on public.profiles to authenticated;

-- Category access and payment writes go through the backend service-role API.
revoke insert, update, delete on public.user_category_access from anon, authenticated;
grant select on public.user_category_access to authenticated;
grant all on public.profiles to service_role;
grant all on public.categories to service_role;
grant all on public.ad_styles to service_role;
grant all on public.payment_orders to service_role;
grant all on public.user_category_access to service_role;

-- ============================================================
-- Supabase Storage Buckets (run these too)
-- ============================================================
-- insert into storage.buckets (id, name, public) values ('style-images', 'style-images', true);
-- insert into storage.buckets (id, name, public) values ('category-covers', 'category-covers', true);
-- create policy "public_read_style_images" on storage.objects for select using (bucket_id = 'style-images');
-- create policy "admin_upload_style_images" on storage.objects for insert with check (bucket_id = 'style-images' and public.is_admin_user());

-- ============================================================
-- Seed Data - Sample Categories
-- ============================================================
insert into public.categories (name, slug, icon, description, display_order) values
  ('Food & Restaurants',  'food',        '🍕', 'Restaurant menus, food delivery, and dining ads',         1),
  ('Pastry & Desserts',   'pastry',      '🥐', 'Bakery, cakes, sweets and dessert ads',                   2),
  ('Fashion & Clothing',  'fashion',     '👗', 'Clothing, accessories, and style ads',                    3),
  ('Tools & Hardware',    'tools',       '🔧', 'Hardware stores, tools, and equipment ads',               4),
  ('Bakery Products',     'bakery',      '🍞', 'Fresh bread, baked goods, and bakery promotions',         5),
  ('Mobiles & Tablets',   'mobiles',     '📱', 'Smartphones, tablets, and tech gadgets',                  6),
  ('Beauty & Cosmetics',  'beauty',      '💄', 'Makeup, skincare, and beauty products',                   7),
  ('Real Estate',         'realestate',  '🏠', 'Property listings, rentals, and real estate',             8),
  ('Automotive',          'automotive',  '🚗', 'Cars, vehicles, and auto service ads',                    9),
  ('Health & Pharmacy',   'health',      '💊', 'Pharmacies, health products, and wellness',              10),
  ('Cafés & Coffee',      'cafes',       '☕', 'Coffee shops, cafés, and beverage brands',               11),
  ('Electronics',         'electronics', '🖥️', 'Electronics, gaming, and tech products',                 12);
