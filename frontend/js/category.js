// Category gallery page
let allStyles = [];
let currentFilter = 'all';
let searchQuery = '';

document.addEventListener('DOMContentLoaded', async () => {
  await initAuth();

  const slug = getParam('slug');
  if (!slug) { window.location.href = 'index.html'; return; }

  await loadCategory(slug);

  // Search
  document.getElementById('searchInput')?.addEventListener('input', e => {
    searchQuery = e.target.value.toLowerCase();
    renderStyles();
  });

  // Filter buttons
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.filter;
      renderStyles();
    });
  });

  // Hamburger
  document.getElementById('hamburger')?.addEventListener('click', () =>
    document.getElementById('mobileNav')?.classList.toggle('open')
  );
});

async function loadCategory(slug) {
  // Load category info
  const { data: cat, error: catErr } = await sb
    .from('categories')
    .select('*')
    .eq('slug', slug)
    .eq('is_active', true)
    .single();

  if (catErr || !cat) {
    window.location.href = 'index.html';
    return;
  }

  document.title = `${cat.name} | Abdalla Eissa for Design`;
  document.getElementById('breadcrumbCategory').textContent = cat.name;
  document.getElementById('catIcon').textContent = cat.icon || '🎨';
  document.getElementById('catName').textContent = cat.name;
  document.getElementById('catDesc').textContent = cat.description || '';

  // Load styles
  const { data: styles, error: stylesErr } = await sb
    .from('ad_styles')
    .select('id, title, image_url, tags, is_premium, description')
    .eq('category_id', cat.id)
    .order('created_at', { ascending: false });

  if (stylesErr || !styles) {
    document.getElementById('stylesGrid').innerHTML = `<div class="empty-state" style="grid-column:1/-1">
      <i class="fa-solid fa-image"></i><h3>No styles yet</h3><p>New styles will be added soon.</p>
    </div>`;
    return;
  }

  allStyles = styles;
  renderStyles();

  // Show upgrade banner to non-premium users if there are premium styles
  const hasPremium = styles.some(s => s.is_premium);
  if (!isPremium() && hasPremium) {
    document.getElementById('upgradeBanner').style.display = 'block';
  }
}

function renderStyles() {
  const grid = document.getElementById('stylesGrid');
  if (!grid) return;

  let filtered = allStyles.filter(style => {
    const matchSearch = !searchQuery ||
      style.title.toLowerCase().includes(searchQuery) ||
      (style.tags || []).some(t => t.toLowerCase().includes(searchQuery));
    const matchFilter =
      currentFilter === 'all' ||
      (currentFilter === 'free' && !style.is_premium) ||
      (currentFilter === 'premium' && style.is_premium);
    return matchSearch && matchFilter;
  });

  if (!filtered.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
      <i class="fa-solid fa-magnifying-glass"></i>
      <h3>No styles found</h3>
      <p>Try a different search or filter.</p>
    </div>`;
    return;
  }

  grid.innerHTML = filtered.map(style => {
    const isPrem = style.is_premium;
    const userHasAccess = isPremium() || !isPrem;

    return `
    <a href="prompt.html?id=${style.id}" class="style-card">
      <div style="overflow:hidden;">
        <img
          class="style-card-img"
          src="${escapeHtml(style.image_url)}"
          alt="${escapeHtml(style.title)}"
          loading="lazy"
          onerror="this.src='https://picsum.photos/400/400?random=${style.id.slice(0,6)}'"
        >
      </div>
      <div class="style-card-body">
        <div class="style-card-title">${escapeHtml(style.title)}</div>
        <div class="style-card-tags">
          ${(style.tags || []).slice(0,3).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
        </div>
      </div>
      ${isPrem ? '<div class="style-card-premium-badge"><i class="fa-solid fa-crown"></i> Premium</div>' : ''}
      ${isPrem && !userHasAccess ? '<div class="style-card-lock"><i class="fa-solid fa-lock"></i></div>' : ''}
    </a>`;
  }).join('');
}
