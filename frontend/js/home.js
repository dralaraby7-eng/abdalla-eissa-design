// Home page — load and render categories
let homeCategories = [];
let categorySearch = '';

document.addEventListener('DOMContentLoaded', async () => {
  await initAuth();
  await loadHomeData();

  document.getElementById('categorySearch')?.addEventListener('input', e => {
    categorySearch = e.target.value.toLowerCase();
    renderCategories();
  });

  // Show upgrade banner to non-premium users
  if (!isPremium()) {
    const banner = document.getElementById('upgradeSection');
    if (banner) banner.style.display = 'block';
  }

  // Hamburger
  const hamburger = document.getElementById('hamburger');
  const mobileNav = document.getElementById('mobileNav');
  hamburger?.addEventListener('click', () => mobileNav?.classList.toggle('open'));
});

async function loadHomeData() {
  try {
    const response = await fetch(`${API_URL}/api/prompts/home`);
    const data = await response.json();
    if (!response.ok || !Array.isArray(data.categories)) throw new Error(data.detail || 'Home catalog failed');
    homeCategories = data.categories;
    document.getElementById('statCategories').textContent = homeCategories.length;
    document.getElementById('statStyles').textContent = `${homeCategories.reduce((sum, cat) => sum + (cat.style_count || 0), 0)}+`;
    renderCategories();
    await loadFeaturedStyles(data.featured_styles || []);
  } catch (error) {
    await loadCategories();
    await loadFeaturedStyles();
  }
}

async function loadCategories() {
  const grid = document.getElementById('categoriesGrid');
  if (!grid) return;

  const { data: categories, error } = await sb
    .from('categories')
    .select('id, name, slug, icon, description')
    .eq('is_active', true)
    .order('display_order');

  if (error || !categories?.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
      <i class="fa-solid fa-folder-open"></i>
      <h3>No categories yet</h3>
      <p>Check back soon — new categories are being added.</p>
    </div>`;
    return;
  }

  const counts = await Promise.all(categories.map(async cat => {
    const { count } = await sb
      .from('ad_styles')
      .select('id', { count: 'exact', head: true })
      .eq('category_id', cat.id)
      .eq('is_active', true);
    return { id: cat.id, count: count || 0 };
  }));
  const countsById = Object.fromEntries(counts.map(item => [item.id, item.count]));
  homeCategories = categories.map(cat => ({ ...cat, style_count: countsById[cat.id] || 0 }));

  // Update stats
  document.getElementById('statCategories').textContent = homeCategories.length;
  document.getElementById('statStyles').textContent = `${homeCategories.reduce((sum, cat) => sum + cat.style_count, 0)}+`;

  renderCategories();
}

function renderCategories() {
  const grid = document.getElementById('categoriesGrid');
  if (!grid) return;

  const filtered = homeCategories.filter(cat =>
    !categorySearch ||
    cat.name.toLowerCase().includes(categorySearch) ||
    (cat.description || '').toLowerCase().includes(categorySearch)
  );

  if (!filtered.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
      <i class="fa-solid fa-magnifying-glass"></i>
      <h3>No categories found</h3>
      <p>Try a broader search term.</p>
    </div>`;
    return;
  }

  grid.innerHTML = filtered.map(cat => `
    <a href="category.html?slug=${encodeURIComponent(cat.slug)}" class="category-card">
      <span class="category-icon">${escapeHtml(cat.icon || '🎨')}</span>
      <span class="category-name">${escapeHtml(cat.name)}</span>
      <span class="category-desc">${escapeHtml(cat.description || '')}</span>
      <span class="category-count">${cat.style_count} styles</span>
    </a>
  `).join('');
}

async function loadFeaturedStyles(providedStyles = null) {
  const grid = document.getElementById('featuredStylesGrid');
  if (!grid) return;

  let styles = providedStyles;
  let error = null;
  if (!styles) {
    const result = await sb
      .from('ad_styles')
      .select('id, category_id, title, image_url, is_premium, prompt_preview, created_at')
      .eq('is_active', true)
      .order('created_at', { ascending: false })
      .limit(8);
    styles = result.data;
    error = result.error;
  }

  if (error || !styles?.length) {
    grid.innerHTML = '';
    return;
  }

  const categoriesById = Object.fromEntries(homeCategories.map(cat => [cat.id, cat]));

  grid.innerHTML = styles.map(style => {
    const cat = categoriesById[style.category_id] || {};
    const seed = style.id.slice(0, 8);
    return `
      <a class="latest-card" href="category.html?slug=${encodeURIComponent(cat.slug || '')}">
        <img
          src="${escapeHtml(style.image_url)}"
          alt="${escapeHtml(style.title)}"
          loading="lazy"
          onerror="this.onerror=null;this.src='https://picsum.photos/seed/${seed}/400/400'"
        >
        <div class="latest-card-body">
          <span>${escapeHtml(cat.name || 'Category')}</span>
          <strong>${escapeHtml(style.title)}</strong>
          <p>${escapeHtml(style.prompt_preview || '')}</p>
        </div>
      </a>`;
  }).join('');
}
