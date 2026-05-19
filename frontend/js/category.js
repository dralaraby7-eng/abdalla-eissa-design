// Category gallery page
let allStyles = [];
let currentFilter = 'all';
let searchQuery = '';

document.addEventListener('DOMContentLoaded', async () => {
  await initAuth();

  const slug = getParam('slug');
  if (!slug) { window.location.href = 'index.html'; return; }

  await loadCategory(slug);

  document.getElementById('searchInput')?.addEventListener('input', e => {
    searchQuery = e.target.value.toLowerCase();
    renderStyles();
  });

  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.filter;
      renderStyles();
    });
  });

  document.getElementById('hamburger')?.addEventListener('click', () =>
    document.getElementById('mobileNav')?.classList.toggle('open')
  );

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') svClose();
  });
});

async function loadCategory(slug) {
  const { data: cat, error: catErr } = await sb
    .from('categories')
    .select('*')
    .eq('slug', slug)
    .eq('is_active', true)
    .single();

  if (catErr || !cat) { window.location.href = 'index.html'; return; }

  document.title = `${cat.name} | Abdalla Eissa for Design`;
  document.getElementById('breadcrumbCategory').textContent = cat.name;
  document.getElementById('catIcon').textContent = cat.icon || '🎨';
  document.getElementById('catName').textContent = cat.name;
  document.getElementById('catDesc').textContent = cat.description || '';

  const { data: styles, error: stylesErr } = await sb
    .from('ad_styles')
    .select('id, title, image_url, tags, is_premium, description, view_count, created_at')
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
    const seed = style.id.slice(0, 8);

    return `
    <div class="style-card" onclick="svOpen('${style.id}')" role="button" tabindex="0"
         onkeydown="if(event.key==='Enter'||event.key===' ')svOpen('${style.id}')">
      <div style="overflow:hidden;">
        <img
          class="style-card-img"
          src="${escapeHtml(style.image_url)}"
          alt="${escapeHtml(style.title)}"
          loading="lazy"
          onerror="this.onerror=null;this.src='https://picsum.photos/seed/${seed}/400/400'"
        >
      </div>
      <div class="style-card-body">
        <div class="style-card-title">${escapeHtml(style.title)}</div>
        <div class="style-card-tags">
          ${(style.tags || []).slice(0, 3).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
        </div>
      </div>
      ${isPrem ? '<div class="style-card-premium-badge"><i class="fa-solid fa-crown"></i> Premium</div>' : ''}
      ${isPrem && !userHasAccess ? '<div class="style-card-lock"><i class="fa-solid fa-lock"></i></div>' : ''}
    </div>`;
  }).join('');
}

// ── Style Viewer Modal ────────────────────────────────────────

async function svOpen(id) {
  const overlay = document.getElementById('svOverlay');
  const inner = document.getElementById('svInner');

  inner.innerHTML = '<div class="loading-overlay"><div class="spinner"></div></div>';
  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';

  const { data: style, error } = await sb
    .from('ad_styles')
    .select('*')
    .eq('id', id)
    .single();

  if (error || !style) {
    inner.innerHTML = `<div class="empty-state" style="padding:4rem;grid-column:1/-1;">
      <i class="fa-solid fa-triangle-exclamation"></i>
      <h3>Could not load style</h3>
    </div>`;
    return;
  }

  sb.rpc('increment_view_count', { style_id: id }).catch(() => {});

  const userCan = isPremium() || isAdmin() || !style.is_premium;
  const promptText = style.meta_prompt || '';
  const preview = promptText.slice(0, FREE_PREVIEW_CHARS);
  const hasMore = promptText.length > FREE_PREVIEW_CHARS;
  const seed = id.slice(0, 8);

  inner.innerHTML = `
    <div class="sv-image-col">
      <img
        src="${escapeHtml(style.image_url)}"
        alt="${escapeHtml(style.title)}"
        onerror="this.onerror=null;this.src='https://picsum.photos/seed/${seed}/600/600'"
      >
      <div class="sv-tags">
        ${(style.tags || []).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
        ${style.is_premium
          ? '<span class="badge-premium"><i class="fa-solid fa-crown"></i> Premium</span>'
          : '<span class="badge-free">Free</span>'}
      </div>
    </div>

    <div class="sv-content-col">
      <h2 class="sv-title">${escapeHtml(style.title)}</h2>
      <div class="sv-meta">
        <span><i class="fa-regular fa-eye"></i> ${style.view_count || 0} views</span>
        <span><i class="fa-regular fa-clock"></i> ${timeAgo(style.created_at)}</span>
        ${style.is_premium ? '<span style="color:#f59e0b;"><i class="fa-solid fa-crown"></i> Premium</span>' : ''}
      </div>

      ${style.description
        ? `<p class="sv-desc">${escapeHtml(style.description)}</p>`
        : ''}

      <div class="prompt-block">
        <div class="prompt-block-label"><i class="fa-solid fa-wand-magic-sparkles"></i> AI Meta Prompt</div>

        ${userCan
          ? promptText
            ? `<div class="prompt-text" id="svPromptText">${escapeHtml(promptText)}</div>
               <button class="btn btn-primary btn-sm prompt-copy-btn" onclick="svCopyPrompt()">
                 <i class="fa-regular fa-copy"></i> Copy Prompt
               </button>`
            : `<div style="color:var(--text-muted);font-size:0.85rem;padding:1rem 0;">No prompt added yet for this style.</div>`
          : `<div class="prompt-text blurred">${escapeHtml(preview)}${hasMore ? '…' : ''}</div>
             <div class="prompt-locked-overlay">
               <p><i class="fa-solid fa-lock"></i> Upgrade to access the full prompt</p>
               <a href="pricing.html" class="btn btn-primary">
                 <i class="fa-solid fa-crown"></i> Unlock with Premium
               </a>
               ${!currentUser
                 ? `<a href="auth.html?tab=signup&back=${encodeURIComponent(window.location.href)}" class="btn btn-outline btn-sm">Sign up free to preview</a>`
                 : ''
               }
             </div>`
        }
      </div>

      <div class="how-to-use">
        <h3><i class="fa-solid fa-circle-info"></i> How to use this prompt</h3>
        <ol>
          <li>Copy the prompt using the <strong>Copy Prompt</strong> button above.</li>
          <li>Open your AI image tool (Midjourney, DALL-E, Stable Diffusion, etc.).</li>
          <li>Paste the prompt and <strong>attach your product or reference image</strong>.</li>
          <li>Replace every <code style="color:var(--blue-300);">[PLACEHOLDER]</code> with your actual details.</li>
          <li>Generate and download your ad image.</li>
        </ol>
      </div>
    </div>
  `;
}

function svCopyPrompt() {
  const text = document.getElementById('svPromptText')?.textContent;
  if (text) copyToClipboard(text);
}

function svClose() {
  document.getElementById('svOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

function svCloseBg(e) {
  if (e.target === document.getElementById('svOverlay')) svClose();
}
