// Home page — load and render categories
document.addEventListener('DOMContentLoaded', async () => {
  await initAuth();
  await loadCategories();

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

  // Update stats
  document.getElementById('statCategories').textContent = categories.length;

  grid.innerHTML = categories.map(cat => `
    <a href="category.html?slug=${cat.slug}" class="category-card">
      <span class="category-icon">${cat.icon || '🎨'}</span>
      <span class="category-name">${escapeHtml(cat.name)}</span>
      <span class="category-desc">${escapeHtml(cat.description || '')}</span>
    </a>
  `).join('');
}
