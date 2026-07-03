// Prompt viewer page
document.addEventListener('DOMContentLoaded', async () => {
  await initAuth();

  const id = getParam('id');
  if (!id) { window.location.href = 'index.html'; return; }

  await loadStyle(id);

  document.getElementById('hamburger')?.addEventListener('click', () =>
    document.getElementById('mobileNav')?.classList.toggle('open')
  );
});

async function loadStyle(id) {
  const page = document.getElementById('promptPage');

  const { data: style, error } = await sb
    .from('ad_styles')
    .select('id, category_id, title, image_url, tags, is_premium, description, view_count, created_at, prompt_preview')
    .eq('id', id)
    .eq('is_active', true)
    .single();

  if (error || !style) {
    page.innerHTML = `<div class="empty-state">
      <i class="fa-solid fa-triangle-exclamation"></i>
      <h3>Style not found</h3>
      <p><a href="index.html" style="color:var(--blue-400);">Go back home</a></p>
    </div>`;
    return;
  }

  document.title = `${style.title} | Abdalla Eissa for Design`;

  // Fetch category info separately (avoids FK join errors)
  let cat = null;
  if (style.category_id) {
    const { data } = await sb.from('categories').select('name, slug, icon').eq('id', style.category_id).single();
    cat = data;
  }

  const userCan = canAccessStyle(style);
  let promptText = '';
  let promptError = '';
  window.currentJsonPrompt = '';
  window.currentStyleTitle = style.title;
  if (userCan) {
    try {
      const res = await fetch(`${API_URL}/api/prompts/${encodeURIComponent(id)}`, {
        headers: await getAuthHeaders()
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Could not load prompt');
      promptText = data.normal_prompt || data.prompt || '';
      window.currentJsonPrompt = data.json_prompt || '';
    } catch (err) {
      promptError = err.message || 'Could not load prompt.';
      showToast(promptError, 'error');
    }
  }
  const preview = style.prompt_preview || '';
  const hasMore = !!preview;

  page.innerHTML = `
    <div class="breadcrumb" style="margin-bottom:1.5rem;">
      <a href="index.html"><i class="fa-solid fa-house"></i> Home</a>
      <span class="sep">/</span>
      <a href="category.html?slug=${encodeURIComponent(cat?.slug || '')}">${escapeHtml(cat?.icon || '')} ${escapeHtml(cat?.name || 'Category')}</a>
      <span class="sep">/</span>
      <span>${escapeHtml(style.title)}</span>
    </div>

    <div class="prompt-layout">

      <!-- Left: image -->
      <div class="prompt-image-wrap">
        <img
          src="${escapeHtml(style.image_url)}"
          alt="${escapeHtml(style.title)}"
          onerror="this.src='https://picsum.photos/600/600?random=${id.slice(0,6)}'"
        >
        <div style="display:flex;gap:0.6rem;margin-top:0.75rem;flex-wrap:wrap;">
          ${(style.tags || []).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
          ${userCan ? '<span class="badge-premium"><i class="fa-solid fa-unlock"></i> Included</span>' : '<span class="badge-free">Teaser</span>'}
        </div>
      </div>

      <!-- Right: prompt -->
      <div class="prompt-content">
        <h1>${escapeHtml(style.title)}</h1>
        <div class="prompt-meta">
          <span><i class="fa-regular fa-eye"></i> ${style.view_count || 0} views</span>
          <span><i class="fa-regular fa-clock"></i> ${timeAgo(style.created_at)}</span>
          ${userCan ? '<span style="color:#34d399;"><i class="fa-solid fa-circle-check"></i> Prompt access</span>' : ''}
        </div>

        ${style.description ? `<p style="color:var(--text-secondary);font-size:0.875rem;line-height:1.7;margin-bottom:1.5rem;">${escapeHtml(style.description)}</p>` : ''}

        <!-- Prompt block -->
        <div class="prompt-block">
          <div class="prompt-block-label"><i class="fa-solid fa-wand-magic-sparkles"></i> AI Meta Prompt</div>

          ${userCan
            ? promptError
              ? `<div class="prompt-error"><strong>Prompt could not load.</strong><span>${escapeHtml(promptError)}</span><button class="btn btn-outline btn-sm" onclick="loadStyle('${id}')">Try again</button></div>`
              : promptText
              ? `<div class="prompt-text" id="promptText">${escapeHtml(promptText)}</div>
                 <div class="prompt-action-row">
                   <button class="btn btn-primary prompt-copy-btn" onclick="copyPromptText()">
                     <i class="fa-regular fa-copy"></i> Copy Meta Prompt
                   </button>
                   <button class="btn btn-outline prompt-copy-btn" onclick="downloadCurrentJsonPrompt()" ${window.currentJsonPrompt ? '' : 'disabled'}>
                     <i class="fa-solid fa-file-arrow-down"></i> Download JSON
                   </button>
                 </div>`
              : `<div style="color:var(--text-muted);font-size:0.85rem;padding:1rem 0;">No prompt added yet for this style.</div>`
            : `<div class="prompt-text blurred" id="promptText">${escapeHtml(preview)}${hasMore ? '…' : ''}</div>
               <div class="prompt-locked-overlay">
                 <p><i class="fa-solid fa-lock"></i> Unlock this category to access the full prompt and JSON file.</p>
                 <a href="pricing.html${cat?.slug ? `?category_slug=${encodeURIComponent(cat.slug)}` : ''}" class="btn btn-primary">
                   <i class="fa-solid fa-key"></i> Unlock This Category
                 </a>
                 ${!currentUser ? `<a href="auth.html?tab=signup&back=${encodeURIComponent(window.location.href)}" class="btn btn-outline btn-sm">Sign up free to preview</a>` : ''}
               </div>`
          }
        </div>

        <!-- How to use -->
        <div class="how-to-use">
          <h3><i class="fa-solid fa-circle-info"></i> How to use this prompt</h3>
          <ol>
            <li>Copy the prompt above using the <strong>Copy</strong> button.</li>
            <li>Open your AI image tool (Midjourney, DALL-E, Stable Diffusion, etc.).</li>
            <li>Paste the prompt and <strong>attach your product/reference image</strong>.</li>
            <li>Replace the <code style="color:var(--blue-300);">[PLACEHOLDER]</code> fields with your business details.</li>
            <li>Generate and download your ad image.</li>
          </ol>
        </div>

        ${!userCan ? `<div style="margin-top:1.5rem;">
          <a href="pricing.html${cat?.slug ? `?category_slug=${encodeURIComponent(cat.slug)}` : ''}" class="btn btn-primary" style="width:100%;justify-content:center;">
            <i class="fa-solid fa-key"></i> Unlock This Category
          </a>
        </div>` : ''}

        <!-- Back button -->
        <div style="margin-top:2rem;">
          <button onclick="history.back()" class="btn btn-ghost">
            <i class="fa-solid fa-arrow-left"></i> Back to Gallery
          </button>
        </div>
      </div>
    </div>
  `;
}

function copyPromptText() {
  const text = document.getElementById('promptText')?.textContent || '';
  copyToClipboard(text);
}

function downloadCurrentJsonPrompt() {
  downloadJsonPromptFile(window.currentStyleTitle || 'prompt', window.currentJsonPrompt || '');
}
