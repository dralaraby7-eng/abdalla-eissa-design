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
  description text,
  tags text[] default '{}',
  is_premium boolean default false,
  view_count integer default 0,
  created_at timestamptz default now()
);

-- User Profiles (extends Supabase auth.users)
create table public.profiles (
  id uuid references auth.users(id) on delete cascade primary key,
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

-- ============================================================
-- Row Level Security
-- ============================================================

alter table public.categories enable row level security;
alter table public.ad_styles enable row level security;
alter table public.profiles enable row level security;
alter table public.prompt_views enable row level security;

-- Categories: public read
create policy "categories_public_read" on public.categories
  for select using (is_active = true);
create policy "categories_admin_all" on public.categories
  for all using (
    exists (select 1 from public.profiles where id = auth.uid() and is_admin = true)
  );

-- Ad styles: public read
create policy "styles_public_read" on public.ad_styles
  for select using (true);
create policy "styles_admin_all" on public.ad_styles
  for all using (
    exists (select 1 from public.profiles where id = auth.uid() and is_admin = true)
  );

-- Profiles: own read/update
create policy "profiles_own_read" on public.profiles
  for select using (auth.uid() = id);
create policy "profiles_own_update" on public.profiles
  for update using (auth.uid() = id);
create policy "profiles_insert" on public.profiles
  for insert with check (auth.uid() = id);
create policy "profiles_admin_read_all" on public.profiles
  for select using (
    exists (select 1 from public.profiles p where p.id = auth.uid() and p.is_admin = true)
  );

-- Prompt views: own
create policy "prompt_views_own" on public.prompt_views
  for all using (auth.uid() = user_id);

-- ============================================================
-- Auto-create profile on signup
-- ============================================================
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, full_name)
  values (new.id, new.raw_user_meta_data->>'full_name');
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

-- ============================================================
-- Supabase Storage Buckets (run these too)
-- ============================================================
-- insert into storage.buckets (id, name, public) values ('style-images', 'style-images', true);
-- insert into storage.buckets (id, name, public) values ('category-covers', 'category-covers', true);
-- create policy "public_read_style_images" on storage.objects for select using (bucket_id = 'style-images');
-- create policy "admin_upload_style_images" on storage.objects for insert using (bucket_id = 'style-images' and auth.role() = 'authenticated');

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
