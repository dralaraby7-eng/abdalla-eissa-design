// Category gallery page
let allStyles = [];
let currentFilter = 'all';
let searchQuery = '';
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
    .select('id, title, image_url, tags, is_premium, description, view_count, created_at, prompt_preview')
    .eq('category_id', cat.id)
    .eq('is_active', true)
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
  if (!overlay || !inner) return;

  const style = allStyles.find(s => s.id === id);
  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';

  if (!style) {
    inner.innerHTML = `<div style="padding:3rem;text-align:center;color:var(--text-muted);">
      <i class="fa-solid fa-triangle-exclamation" style="font-size:2rem;color:#f59e0b;"></i>
      <p style="margin-top:1rem;">Style not found. Try refreshing the page.</p>
    </div>`;
    return;
  }

  try {
    sb.rpc('increment_view_count', { style_id: id }).catch(() => {});
  } catch (e) { /* ignore */ }

  const userCan = (typeof isPremium === 'function' && isPremium())
                || (typeof isAdmin === 'function' && isAdmin())
                || !style.is_premium;
  const preview = style.prompt_preview || '';
  const hasMore = !!preview;
  const seed = id.slice(0, 8);
  const loggedIn = typeof currentUser !== 'undefined' && currentUser;
  const hasCachedPrompt = promptCache.has(id);
  const cachedPrompt = promptCache.get(id) || '';

  try {
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

      <div class="prompt-block">
        <div class="prompt-block-label"><i class="fa-solid fa-wand-magic-sparkles"></i> AI Meta Prompt</div>

        ${userCan
          ? `<div class="prompt-text" id="svPromptText">${
                hasCachedPrompt
                  ? escapeHtml(cachedPrompt)
                  : '<span class="spinner"></span> Loading prompt...'
              }</div>
             <button class="btn btn-primary prompt-copy-btn" id="svCopyBtn" onclick="svCopyPrompt()" ${hasCachedPrompt && cachedPrompt ? '' : 'disabled'}>
               <i class="fa-regular fa-copy"></i> Copy Prompt
             </button>`
          : `<div class="prompt-text blurred">${escapeHtml(preview)}${hasMore ? '…' : ''}</div>
             <div class="prompt-locked-overlay">
               <p><i class="fa-solid fa-lock"></i> Upgrade to access the full prompt</p>
               <a href="pricing.html" class="btn btn-primary">
                 <i class="fa-solid fa-crown"></i> Unlock with Premium
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
  const text = document.getElementById('svPromptText')?.textContent;
  if (text && !text.includes('Loading prompt')) copyToClipboard(text);
}

async function svPrefetchPrompt(id) {
  const style = allStyles.find(s => s.id === id);
  if (!style || promptCache.has(id)) return;
  const userCan = (typeof isPremium === 'function' && isPremium())
                || (typeof isAdmin === 'function' && isAdmin())
                || !style.is_premium;
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
  const prompt = data.prompt || '';
  promptCache.set(id, prompt);
  return prompt;
}

async function svLoadPrompt(id) {
  const promptEl = document.getElementById('svPromptText');
  const copyBtn = document.getElementById('svCopyBtn');
  try {
    const prompt = await svFetchPrompt(id);
    if (promptEl) {
      promptEl.textContent = prompt || 'No prompt added yet for this style.';
    }
    if (copyBtn) {
      copyBtn.disabled = !prompt;
    }
  } catch (err) {
    if (promptEl) {
      promptEl.textContent = err.message || 'Could not load prompt.';
    }
    showToast(err.message || 'Could not load prompt.', 'error');
  }
}

function svClose() {
  document.getElementById('svOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

function svCloseBg(e) {
  if (e.target === document.getElementById('svOverlay')) svClose();
}
