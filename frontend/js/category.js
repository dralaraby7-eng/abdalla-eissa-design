// Category gallery page
let allStyles = [];
let currentFilter = 'all';
let searchQuery = '';
let currentSort = 'newest';
let currentView = localStorage.getItem('styleViewMode') || 'grid';
let currentStyleId = null;
let currentCategorySlug = '';
let currentCategoryName = '';
let currentCatalogHasAccess = false;
let currentCatalogIsTeaser = true;
let currentTotalStyles = 0;
const promptCache = new Map();

document.addEventListener('DOMContentLoaded', async () => {
  await initAuth();

  const slug = getParam('slug');
  if (!slug) { window.location.href = 'index.html'; return; }

  await loadCategory(slug);

  document.getElementById('searchInput')?.addEventListener('input', e => {
    searchQuery = e.target.value.toLowerCase();
    renderStyles();
  });

  document.getElementById('sortSelect')?.addEventListener('change', e => {
    currentSort = e.target.value;
    renderStyles();
  });

  document.querySelectorAll('.view-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.view === currentView);
    btn.addEventListener('click', () => {
      currentView = btn.dataset.view || 'grid';
      localStorage.setItem('styleViewMode', currentView);
      document.querySelectorAll('.view-btn').forEach(b => b.classList.toggle('active', b === btn));
      renderStyles();
    });
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
  currentCategorySlug = slug;
  const grid = document.getElementById('stylesGrid');
  const downloadButton = document.getElementById('downloadCategoryBtn');
  const htmlDownloadButton = document.getElementById('downloadHtmlBtn');
  if (downloadButton) {
    downloadButton.disabled = true;
    downloadButton.innerHTML = '<span class="spinner"></span> <span>Loading category...</span>';
  }
  if (htmlDownloadButton) htmlDownloadButton.disabled = true;

  let catalog;
  try {
    catalog = await withTimeout(fetchCatalogFromApi(slug), 45000);
  } catch (apiError) {
    try {
      catalog = await withTimeout(fetchTeaserFromSupabase(slug), 20000);
    } catch (fallbackError) {
    if (grid) {
      grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
        <i class="fa-solid fa-triangle-exclamation"></i>
        <h3>Category could not load</h3>
        <p>Check your connection, then try again.</p>
        <button class="btn btn-primary" type="button" onclick="loadCategory(currentCategorySlug)">
          <i class="fa-solid fa-rotate-right"></i> Try again
        </button>
      </div>`;
    }
    if (downloadButton) {
      downloadButton.innerHTML = '<i class="fa-solid fa-file-arrow-down"></i> <span>Download unavailable</span>';
    }
    showToast('Could not load this category. Please try again.', 'error');
    return;
    }
  }

  const cat = catalog.category;
  const styles = catalog.styles;
  currentCategorySlug = cat.slug || slug;
  currentCategoryName = cat.name || 'Category';
  currentCatalogHasAccess = !!catalog.has_access;
  currentCatalogIsTeaser = !!catalog.is_teaser;
  currentTotalStyles = Number(catalog.total_styles) || styles.length;

  document.title = `${cat.name} | Abdalla Eissa for Design`;
  document.getElementById('breadcrumbCategory').textContent = cat.name;
  document.getElementById('catIcon').textContent = cat.icon || '🎨';
  document.getElementById('catName').textContent = cat.name;
  document.getElementById('catDesc').textContent = cat.description || '';

  if (!Array.isArray(styles)) {
    document.getElementById('stylesGrid').innerHTML = `<div class="empty-state" style="grid-column:1/-1">
      <i class="fa-solid fa-image"></i><h3>No styles yet</h3><p>New styles will be added soon.</p>
    </div>`;
    return;
  }

  allStyles = styles;
  configureCategoryDownload();
  renderStyles();
  hydratePromptCache(styles);

  if (currentCatalogIsTeaser) {
    const banner = document.getElementById('upgradeBanner');
    banner.style.display = 'block';
    const link = banner.querySelector('a');
    if (link) link.href = `pricing.html?category_slug=${encodeURIComponent(currentCategorySlug)}`;
  }
}

function withTimeout(promise, milliseconds) {
  return Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error('Request timed out')), milliseconds))
  ]);
}

async function fetchCatalogFromApi(slug) {
  const response = await fetch(`${API_URL}/api/prompts/categories/${encodeURIComponent(slug)}/catalog`, {
    headers: await getAuthHeaders()
  });
  const data = await response.json();
  if (!response.ok || !data.category || !Array.isArray(data.styles)) {
    throw new Error(data.detail || 'Catalog API failed');
  }
  return data;
}

async function fetchTeaserFromSupabase(slug) {
  const { data: category, error: categoryError } = await sb
    .from('categories')
    .select('id, name, slug, icon, description')
    .eq('slug', slug)
    .eq('is_active', true)
    .single();
  if (categoryError || !category) throw categoryError || new Error('Category not found');

  const { data: styles, error: stylesError, count } = await sb
    .from('ad_styles')
    .select('id, category_id, title, image_url, tags, is_premium, description, view_count, created_at, prompt_preview', { count: 'exact' })
    .eq('category_id', category.id)
    .eq('is_active', true)
    .order('created_at', { ascending: false })
    .limit(5);
  if (stylesError || !styles) throw stylesError || new Error('Styles could not load');
  return { category, styles, total_styles: count || styles.length, has_access: false, is_teaser: true, teaser_limit: 5 };
}

function configureCategoryDownload() {
  const pdfButton = document.getElementById('downloadCategoryBtn');
  const htmlButton = document.getElementById('downloadHtmlBtn');
  if (!pdfButton || !htmlButton) return;
  const locked = !currentCatalogHasAccess;
  [pdfButton, htmlButton].forEach(button => {
    button.disabled = false;
    button.dataset.locked = locked ? 'true' : 'false';
  });
  pdfButton.title = locked
    ? 'Unlock this category to download the PDF catalog'
    : `Download the printable ${currentCategoryName} PDF catalog`;
  htmlButton.title = locked
    ? 'Unlock this category to download the interactive catalog'
    : `Download the offline ${currentCategoryName} image and prompt catalog`;
  pdfButton.innerHTML = locked
    ? '<i class="fa-solid fa-lock"></i> <span>Unlock PDF Catalog</span>'
    : '<i class="fa-solid fa-file-pdf"></i> <span>Download PDF Catalog</span>';
  htmlButton.innerHTML = locked
    ? '<i class="fa-solid fa-lock"></i> <span>Unlock Interactive Catalog</span>'
    : '<i class="fa-solid fa-window-restore"></i> <span>Interactive HTML</span>';
  pdfButton.onclick = () => downloadCategoryPackage('pdf');
  htmlButton.onclick = () => downloadCategoryPackage('html');
}

async function downloadCategoryPackage(format = 'pdf') {
  const button = document.getElementById(format === 'html' ? 'downloadHtmlBtn' : 'downloadCategoryBtn');
  if (!button || button.disabled) return;
  if (button.dataset.locked === 'true') {
    window.location.href = `pricing.html?category_slug=${encodeURIComponent(currentCategorySlug)}`;
    return;
  }

  const originalHtml = button.innerHTML;
  button.disabled = true;
  button.innerHTML = `<span class="spinner"></span> <span>Building ${format.toUpperCase()} catalog...</span>`;
  try {
    const response = await fetch(`${API_URL}/api/prompts/categories/${encodeURIComponent(currentCategorySlug)}/download?format=${encodeURIComponent(format)}`, {
      headers: await getAuthHeaders()
    });
    if (!response.ok) {
      let message = 'Could not build the interactive catalog';
      try {
        const data = await response.json();
        message = data.detail || message;
      } catch (e) { /* non-JSON server error */ }
      throw new Error(message);
    }
    const blob = await response.blob();
    const disposition = response.headers.get('content-disposition') || '';
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const filename = match?.[1] || `${currentCategorySlug}-prompt-catalog.${format === 'html' ? 'html' : 'pdf'}`;
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    showToast(`${format.toUpperCase()} catalog downloaded successfully.`, 'success');
  } catch (error) {
    showToast(error.message || 'Could not download the interactive catalog.', 'error');
  } finally {
    button.disabled = false;
    button.innerHTML = originalHtml;
  }
}

function renderStyles() {
  const grid = document.getElementById('stylesGrid');
  if (!grid) return;

  let filtered = allStyles.filter(style => {
    const matchSearch = !searchQuery ||
      style.title.toLowerCase().includes(searchQuery) ||
      (style.description || '').toLowerCase().includes(searchQuery) ||
      (style.prompt_preview || '').toLowerCase().includes(searchQuery) ||
      (style.tags || []).some(t => t.toLowerCase().includes(searchQuery));
    const matchFilter =
      currentFilter === 'all' ||
      (currentFilter === 'free' && !style.is_premium) ||
      (currentFilter === 'premium' && style.is_premium);
    return matchSearch && matchFilter;
  });

  filtered = sortStyles(filtered);
  grid.classList.toggle('styles-list', currentView === 'list');
  const count = document.getElementById('resultsCount');
  if (count) {
    count.textContent = currentCatalogIsTeaser
      ? `${filtered.length} teaser styles of ${currentTotalStyles}`
      : `${filtered.length} style${filtered.length === 1 ? '' : 's'}`;
  }

  if (!filtered.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
      <i class="fa-solid fa-magnifying-glass"></i>
      <h3>No styles found</h3>
      <p>Try a different search or filter.</p>
    </div>`;
    return;
  }

  grid.innerHTML = filtered.map(style => {
    const userHasAccess = canAccessStyle(style);
    const seed = style.id.slice(0, 8);
    const promptReady = promptCache.has(style.id);
    const desc = style.description || style.prompt_preview || '';

    return `
    <div class="style-card" onclick="svOpen('${style.id}')" role="button" tabindex="0"
         onmouseenter="svPrefetchPrompt('${style.id}')"
         onfocus="svPrefetchPrompt('${style.id}')"
         ontouchstart="svPrefetchPrompt('${style.id}')"
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
        <div class="style-card-title-row">
          <div class="style-card-title">${escapeHtml(style.title)}</div>
          <span class="style-card-status ${promptReady ? 'ready' : ''}">${promptReady ? 'Ready' : 'Preview'}</span>
        </div>
        ${desc ? `<p class="style-card-desc">${escapeHtml(desc)}</p>` : ''}
        <div class="style-card-tags">
          ${(style.tags || []).slice(0, 3).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
        </div>
        <div class="style-card-actions">
          <button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); ${userHasAccess ? `quickCopyPrompt('${style.id}')` : `svOpen('${style.id}')`}">
            <i class="fa-regular ${userHasAccess ? 'fa-copy' : 'fa-eye'}"></i> ${userHasAccess ? (promptReady ? 'Copy Meta' : 'Open') : 'Preview'}
          </button>
          <span><i class="fa-regular fa-eye"></i> ${style.view_count || 0}</span>
        </div>
      </div>
      ${!userHasAccess ? '<div class="style-card-premium-badge"><i class="fa-solid fa-eye"></i> Teaser</div>' : ''}
      ${!userHasAccess ? '<div class="style-card-lock"><i class="fa-solid fa-lock"></i></div>' : ''}
    </div>`;
  }).join('');
}

function sortStyles(styles) {
  return [...styles].sort((a, b) => {
    if (currentSort === 'popular') return (b.view_count || 0) - (a.view_count || 0);
    if (currentSort === 'title') return String(a.title || '').localeCompare(String(b.title || ''));
    return new Date(b.created_at || 0) - new Date(a.created_at || 0);
  });
}

function visibleStyles() {
  const filtered = allStyles.filter(style => {
    const matchSearch = !searchQuery ||
      style.title.toLowerCase().includes(searchQuery) ||
      (style.description || '').toLowerCase().includes(searchQuery) ||
      (style.prompt_preview || '').toLowerCase().includes(searchQuery) ||
      (style.tags || []).some(t => t.toLowerCase().includes(searchQuery));
    const matchFilter =
      currentFilter === 'all' ||
      (currentFilter === 'free' && !style.is_premium) ||
      (currentFilter === 'premium' && style.is_premium);
    return matchSearch && matchFilter;
  });
  return sortStyles(filtered);
}

async function hydratePromptCache(styles) {
  const accessible = styles.filter(style => {
    const userCan = (typeof canAccessStyle === 'function' && canAccessStyle(style));
    return userCan && !promptCache.has(style.id);
  });
  if (!accessible.length) return;

  for (let i = 0; i < accessible.length; i += 80) {
    const batch = accessible.slice(i, i + 80);
    try {
      const res = await fetch(`${API_URL}/api/prompts/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(await getAuthHeaders())
        },
        body: JSON.stringify({ style_ids: batch.map(style => style.id) })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Could not prefetch prompts');
      Object.entries(data.prompt_details || {}).forEach(([id, details]) => {
        promptCache.set(id, {
          normal_prompt: details.normal_prompt || '',
          json_prompt: details.json_prompt || ''
        });
      });
      renderStyles();
    } catch (err) {
      console.warn('Prompt prefetch failed:', err);
      return;
    }
  }
}

// ── Style Viewer Modal ────────────────────────────────────────

async function svOpen(id) {
  const overlay = document.getElementById('svOverlay');
  const inner = document.getElementById('svInner');
  if (!overlay || !inner) return;

  const style = allStyles.find(s => s.id === id);
  currentStyleId = id;
  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';

  if (!style) {
    inner.innerHTML = `<div style="padding:3rem;text-align:center;color:var(--text-muted);">
      <i class="fa-solid fa-triangle-exclamation" style="font-size:2rem;color:#f59e0b;"></i>
      <p style="margin-top:1rem;">Style not found. Try refreshing the page.</p>
    </div>`;
    return;
  }

  const userCan = (typeof canAccessStyle === 'function' && canAccessStyle(style));
  const preview = style.prompt_preview || '';
  const hasMore = !!preview;
  const seed = id.slice(0, 8);
  const loggedIn = typeof currentUser !== 'undefined' && currentUser;
  const hasCachedPrompt = promptCache.has(id);
  const cachedDetails = promptCache.get(id) || { normal_prompt: '', json_prompt: '' };
  const cachedPrompt = cachedDetails.normal_prompt || '';

  try {
    const activeStyles = visibleStyles();
    const index = activeStyles.findIndex(s => s.id === id);
    const canGoPrev = index > 0;
    const canGoNext = index >= 0 && index < activeStyles.length - 1;
    inner.innerHTML = `
    <div class="sv-image-col">
      <img
        src="${escapeHtml(style.image_url)}"
        alt="${escapeHtml(style.title)}"
        onerror="this.onerror=null;this.src='https://picsum.photos/seed/${seed}/600/600'"
      >
      <div class="sv-tags">
        ${(style.tags || []).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
        ${userCan
          ? '<span class="badge-premium"><i class="fa-solid fa-unlock"></i> Included</span>'
          : '<span class="badge-free">Teaser</span>'}
      </div>
      <div class="sv-nav-row">
        <button class="btn btn-ghost btn-sm" onclick="svStep(-1)" ${canGoPrev ? '' : 'disabled'}>
          <i class="fa-solid fa-chevron-left"></i> Previous
        </button>
        <button class="btn btn-ghost btn-sm" onclick="svStep(1)" ${canGoNext ? '' : 'disabled'}>
          Next <i class="fa-solid fa-chevron-right"></i>
        </button>
      </div>
    </div>

    <div class="sv-content-col">
      <h2 class="sv-title">${escapeHtml(style.title)}</h2>
      <div class="sv-meta">
        <span><i class="fa-regular fa-eye"></i> ${style.view_count || 0} views</span>
        <span><i class="fa-regular fa-clock"></i> ${timeAgo(style.created_at)}</span>
        ${userCan ? '<span style="color:#34d399;"><i class="fa-solid fa-circle-check"></i> Prompt access</span>' : ''}
      </div>

      <div class="prompt-block">
        <div class="prompt-block-label"><i class="fa-solid fa-wand-magic-sparkles"></i> AI Meta Prompt</div>

        ${userCan
          ? `<div class="prompt-text" id="svPromptText">${
                hasCachedPrompt
                  ? escapeHtml(cachedPrompt)
                  : '<span class="spinner"></span> Loading prompt...'
              }</div>
             <div class="prompt-action-row">
               <button class="btn btn-primary prompt-copy-btn" id="svCopyBtn" onclick="svCopyPrompt()" ${hasCachedPrompt && cachedPrompt ? '' : 'disabled'}>
                 <i class="fa-regular fa-copy"></i> Copy Meta Prompt
               </button>
               <button class="btn btn-outline prompt-copy-btn" id="svJsonBtn" onclick="svDownloadJson()" ${hasCachedPrompt && cachedDetails.json_prompt ? '' : 'disabled'}>
                 <i class="fa-solid fa-file-arrow-down"></i> Download JSON
               </button>
             </div>`
          : `<div class="prompt-text blurred">${escapeHtml(preview)}${hasMore ? '…' : ''}</div>
             <div class="prompt-locked-overlay">
               <p><i class="fa-solid fa-lock"></i> This image is a teaser. Unlock this category to access its prompts.</p>
               <a href="pricing.html?category_slug=${encodeURIComponent(currentCategorySlug)}" class="btn btn-primary">
                 <i class="fa-solid fa-key"></i> Unlock This Category
               </a>
               ${!loggedIn
                 ? `<a href="auth.html?tab=signup&back=${encodeURIComponent(window.location.href)}" class="btn btn-outline btn-sm">Sign up free to preview</a>`
                 : ''
               }
             </div>`
        }
      </div>

      ${style.description
        ? `<p class="sv-desc" style="margin-top:0.5rem;">${escapeHtml(style.description)}</p>`
        : ''}

      <details style="margin-top:1rem;">
        <summary style="cursor:pointer;font-size:0.82rem;color:var(--text-muted);list-style:none;display:flex;align-items:center;gap:0.4rem;">
          <i class="fa-solid fa-circle-info"></i> How to use this prompt
        </summary>
        <ol style="font-size:0.82rem;color:var(--text-secondary);line-height:1.7;margin-top:0.75rem;padding-left:1.2rem;">
          <li>Copy the prompt above, then open Midjourney, DALL-E, Stable Diffusion, etc.</li>
          <li>Paste the prompt and attach your product or reference image.</li>
          <li>Replace every <code style="color:var(--blue-300);">[PLACEHOLDER]</code> with your actual details.</li>
          <li>Generate and download your ad image.</li>
        </ol>
      </details>
    </div>
  `;
  } catch (err) {
    console.error('svOpen render error:', err);
    inner.innerHTML = `<div style="padding:3rem;text-align:center;color:var(--text-muted);">
      <i class="fa-solid fa-triangle-exclamation" style="font-size:2rem;color:#ef4444;"></i>
      <p style="margin-top:1rem;">Could not render this style.<br><small>${escapeHtml(String(err.message || err))}</small></p>
    </div>`;
  }

  if (userCan && !hasCachedPrompt) {
    svLoadPrompt(id);
  }
}

function svCopyPrompt() {
  const details = promptCache.get(currentStyleId);
  if (details?.normal_prompt) copyToClipboard(details.normal_prompt);
}

function svDownloadJson() {
  const details = promptCache.get(currentStyleId);
  const style = allStyles.find(item => item.id === currentStyleId);
  downloadJsonPromptFile(style?.title || 'prompt', details?.json_prompt || '');
}

async function quickCopyPrompt(id) {
  if (!promptCache.has(id)) {
    await svOpen(id);
    return;
  }
  const details = promptCache.get(id);
  if (details?.normal_prompt) copyToClipboard(details.normal_prompt);
}

async function svPrefetchPrompt(id) {
  const style = allStyles.find(s => s.id === id);
  if (!style || promptCache.has(id)) return;
  const userCan = (typeof canAccessStyle === 'function' && canAccessStyle(style));
  if (!userCan) return;
  try {
    await svFetchPrompt(id);
  } catch (e) { /* prefetch failures are handled on click */ }
}

async function svFetchPrompt(id) {
  if (promptCache.has(id)) return promptCache.get(id);
  const res = await fetch(`${API_URL}/api/prompts/${encodeURIComponent(id)}`, {
    headers: await getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Could not load prompt');
  const details = {
    normal_prompt: data.normal_prompt || data.prompt || '',
    json_prompt: data.json_prompt || ''
  };
  promptCache.set(id, details);
  return details;
}

async function svLoadPrompt(id) {
  const promptEl = document.getElementById('svPromptText');
  const copyBtn = document.getElementById('svCopyBtn');
  const jsonBtn = document.getElementById('svJsonBtn');
  try {
    const details = await svFetchPrompt(id);
    if (promptEl) {
      promptEl.textContent = details.normal_prompt || 'No prompt added yet for this style.';
    }
    if (copyBtn) {
      copyBtn.disabled = !details.normal_prompt;
    }
    if (jsonBtn) {
      jsonBtn.disabled = !details.json_prompt;
    }
  } catch (err) {
    if (promptEl) {
      promptEl.innerHTML = `
        <div class="prompt-error">
          <strong>Prompt could not load.</strong>
          <span>${escapeHtml(err.message || 'Network error')}</span>
          <button class="btn btn-outline btn-sm" onclick="svLoadPrompt('${id}')">Try again</button>
        </div>`;
    }
    showToast(err.message || 'Could not load prompt.', 'error');
  }
}

function svStep(direction) {
  if (!currentStyleId) return;
  const styles = visibleStyles();
  const index = styles.findIndex(style => style.id === currentStyleId);
  const next = styles[index + direction];
  if (next) svOpen(next.id);
}

function svClose() {
  document.getElementById('svOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

function svCloseBg(e) {
  if (e.target === document.getElementById('svOverlay')) svClose();
}
