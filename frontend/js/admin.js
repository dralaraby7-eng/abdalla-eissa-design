// Admin panel
let adminCategories = [];
let adminStyles = [];
let adminUsers = [];

document.addEventListener('DOMContentLoaded', async () => {
  await initAuth();
  if (!currentUser || !isAdmin()) {
    document.getElementById('adminContent').innerHTML = `
      <div class="empty-state">
        <i class="fa-solid fa-shield-halved"></i>
        <h3>Access Denied</h3>
        <p>You don't have admin privileges.</p>
        <a href="index.html" class="btn btn-outline" style="margin-top:1rem;">Go Home</a>
      </div>`;
    return;
  }
  await loadAdminData();

  // Close modals on overlay click
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', e => {
      if (e.target === overlay) overlay.classList.remove('open');
    });
  });
});

async function loadAdminData() {
  const [catsRes, stylesRes, usersRes] = await Promise.all([
    sb.from('categories').select('*').order('display_order'),
    sb.from('ad_styles').select('*, categories(name)').order('created_at', { ascending: false }),
    sb.from('profiles').select('*').order('created_at', { ascending: false })
  ]);

  adminCategories = catsRes.data || [];
  adminStyles = stylesRes.data || [];
  adminUsers = usersRes.data || [];

  const premiumCount = adminUsers.filter(u => u.plan_type === 'premium').length;

  document.getElementById('adminContent').innerHTML = `
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:2rem;flex-wrap:wrap;">
      <h1 style="font-size:1.5rem;font-weight:700;color:var(--white);"><i class="fa-solid fa-shield-halved" style="color:var(--blue-400);"></i> Admin Panel</h1>
      <div style="margin-left:auto;display:flex;gap:0.5rem;">
        <a href="index.html" class="btn btn-ghost btn-sm"><i class="fa-solid fa-house"></i> View Site</a>
        <button onclick="signOut()" class="btn btn-ghost btn-sm"><i class="fa-solid fa-right-from-bracket"></i> Sign Out</button>
      </div>
    </div>

    <div class="stats-grid" style="margin-bottom:2.5rem;">
      <div class="stat-card">
        <div class="stat-icon"><i class="fa-solid fa-folder"></i></div>
        <span class="stat-value">${adminCategories.length}</span>
        <span class="stat-label">Categories</span>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><i class="fa-solid fa-image"></i></div>
        <span class="stat-value">${adminStyles.length}</span>
        <span class="stat-label">Ad Styles</span>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><i class="fa-solid fa-users"></i></div>
        <span class="stat-value">${adminUsers.length}</span>
        <span class="stat-label">Total Users</span>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><i class="fa-solid fa-crown"></i></div>
        <span class="stat-value">${premiumCount}</span>
        <span class="stat-label">Premium Users</span>
      </div>
    </div>

    <!-- Categories section -->
    <div class="admin-section">
      <h2>
        <i class="fa-solid fa-folder-open" style="color:var(--blue-400);"></i> Categories
        <button onclick="openCatModal()" class="btn btn-primary btn-sm" style="margin-left:auto;">
          <i class="fa-solid fa-plus"></i> Add Category
        </button>
      </h2>
      <div style="overflow-x:auto;border-radius:var(--radius-lg);border:1px solid var(--border);">
        <table class="admin-table">
          <thead><tr><th>Icon</th><th>Name</th><th>Slug</th><th>Styles</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody id="categoriesTableBody">${renderCategoriesTable()}</tbody>
        </table>
      </div>
    </div>

    <!-- Styles section -->
    <div class="admin-section">
      <h2>
        <i class="fa-solid fa-images" style="color:var(--blue-400);"></i> Ad Styles
        <button onclick="openAddStyleModal()" class="btn btn-primary btn-sm" style="margin-left:auto;">
          <i class="fa-solid fa-plus"></i> Add Style
        </button>
      </h2>
      <div style="overflow-x:auto;border-radius:var(--radius-lg);border:1px solid var(--border);">
        <table class="admin-table">
          <thead><tr><th>Image</th><th>Title</th><th>Category</th><th>Type</th><th>Views</th><th>Actions</th></tr></thead>
          <tbody id="stylesTableBody">${renderStylesTable()}</tbody>
        </table>
      </div>
    </div>

    <!-- Users section -->
    <div class="admin-section">
      <h2>
        <i class="fa-solid fa-users" style="color:var(--blue-400);"></i> Users
        <button onclick="openCreateUserModal()" class="btn btn-primary btn-sm" style="margin-left:auto;">
          <i class="fa-solid fa-user-plus"></i> Create User
        </button>
      </h2>
      <div style="overflow-x:auto;border-radius:var(--radius-lg);border:1px solid var(--border);">
        <table class="admin-table">
          <thead><tr><th>Name</th><th>Email</th><th>Plan</th><th>Joined</th><th>Actions</th></tr></thead>
          <tbody>${renderUsersTable()}</tbody>
        </table>
      </div>
    </div>
  `;

  populateCategorySelect();
}

function renderUsersTable() {
  if (!adminUsers.length) return '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);">No users yet</td></tr>';
  return adminUsers.map(u => {
    const isPrem = u.plan_type === 'premium';
    // Check if lifetime (no expiry) or expired
    const hasExpiry = !!u.subscription_expires_at;
    const expired = hasExpiry && new Date(u.subscription_expires_at) < new Date();
    const planBadge = isPrem && !expired
      ? `<span class="badge-premium"><i class="fa-solid fa-crown"></i> Premium${hasExpiry ? '' : ' ∞'}</span>`
      : `<span class="badge-free">Free</span>`;

    return `
      <tr>
        <td style="color:var(--text-primary);font-weight:600;">${escapeHtml(u.full_name || '—')}</td>
        <td style="font-size:0.8rem;color:var(--text-secondary);">${escapeHtml(u.email || '—')}</td>
        <td>${planBadge}</td>
        <td style="font-size:0.8rem;">${new Date(u.created_at).toLocaleDateString()}</td>
        <td>
          <div style="display:flex;gap:0.4rem;flex-wrap:wrap;">
            ${(!isPrem || expired)
              ? `<button onclick="adminGrantPremium('${u.id}')" class="btn btn-sm btn-outline" title="Grant Lifetime Premium">
                   <i class="fa-solid fa-crown"></i> Grant
                 </button>`
              : `<button onclick="adminRevokePremium('${u.id}')" class="btn btn-sm btn-danger" title="Revoke Premium">
                   Revoke
                 </button>`
            }
            <button onclick="adminResetPassword('${u.email || ''}')" class="btn btn-sm btn-ghost" title="Send password reset">
              <i class="fa-solid fa-key"></i>
            </button>
          </div>
        </td>
      </tr>`;
  }).join('');
}

function renderCategoriesTable() {
  return adminCategories.map(cat => {
    const styleCount = adminStyles.filter(s => s.category_id === cat.id).length;
    return `<tr>
      <td style="font-size:1.5rem;">${cat.icon || '🎨'}</td>
      <td style="color:var(--text-primary);font-weight:600;">${escapeHtml(cat.name)}</td>
      <td><code style="color:var(--blue-400);font-size:0.8rem;">${escapeHtml(cat.slug)}</code></td>
      <td>${styleCount}</td>
      <td>${cat.is_active ? '<span style="color:#34d399;font-size:0.8rem;"><i class="fa-solid fa-circle-check"></i> Active</span>' : '<span style="color:#f87171;font-size:0.8rem;">Inactive</span>'}</td>
      <td>
        <div style="display:flex;gap:0.4rem;">
          <button onclick="editCategory('${cat.id}')" class="btn btn-sm btn-outline"><i class="fa-solid fa-pen"></i></button>
          <button onclick="deleteCategory('${cat.id}')" class="btn btn-sm btn-danger"><i class="fa-solid fa-trash"></i></button>
        </div>
      </td>
    </tr>`;
  }).join('');
}

function renderStylesTable() {
  return adminStyles.slice(0, 50).map(style => `
    <tr>
      <td><img src="${escapeHtml(style.image_url)}" alt="" onerror="this.src='https://picsum.photos/48/48'"></td>
      <td style="color:var(--text-primary);">${escapeHtml(style.title)}</td>
      <td>${escapeHtml(style.categories?.name || '—')}</td>
      <td>${style.is_premium ? '<span class="badge-premium" style="font-size:0.68rem;">Premium</span>' : '<span class="badge-free" style="font-size:0.68rem;">Free</span>'}</td>
      <td>${style.view_count || 0}</td>
      <td>
        <div style="display:flex;gap:0.4rem;">
          <button onclick="editStyle('${style.id}')" class="btn btn-sm btn-outline"><i class="fa-solid fa-pen"></i></button>
          <button onclick="deleteStyle('${style.id}')" class="btn btn-sm btn-danger"><i class="fa-solid fa-trash"></i></button>
        </div>
      </td>
    </tr>
  `).join('');
}

function populateCategorySelect() {
  const sel = document.getElementById('styleCategory');
  if (!sel) return;
  sel.innerHTML = adminCategories.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('');
}

// ── Style Modal ────────────────────────────────────────────────

function openAddStyleModal() {
  document.getElementById('modalTitle').textContent = 'Add New Style';
  document.getElementById('editStyleId').value = '';
  document.getElementById('styleForm').reset();
  populateCategorySelect();
  document.getElementById('addStyleModal').classList.add('open');
}

function editStyle(id) {
  const style = adminStyles.find(s => s.id === id);
  if (!style) return;
  document.getElementById('modalTitle').textContent = 'Edit Style';
  document.getElementById('editStyleId').value = id;
  populateCategorySelect();
  document.getElementById('styleCategory').value = style.category_id;
  document.getElementById('styleTitle').value = style.title;
  document.getElementById('styleDesc').value = style.description || '';
  document.getElementById('styleImageUrl').value = style.image_url;
  document.getElementById('stylePrompt').value = style.meta_prompt || '';
  document.getElementById('styleTags').value = (style.tags || []).join(', ');
  document.getElementById('styleIsPremium').checked = style.is_premium;
  document.getElementById('addStyleModal').classList.add('open');
}

function closeModal() { document.getElementById('addStyleModal').classList.remove('open'); }

async function handleSaveStyle(e) {
  e.preventDefault();
  const btn = document.getElementById('saveStyleBtn');
  btn.disabled = true;
  const id = document.getElementById('editStyleId').value;
  const tags = document.getElementById('styleTags').value.split(',').map(t => t.trim()).filter(Boolean);
  const payload = {
    category_id: document.getElementById('styleCategory').value,
    title:        document.getElementById('styleTitle').value.trim(),
    description:  document.getElementById('styleDesc').value.trim() || null,
    image_url:    document.getElementById('styleImageUrl').value.trim(),
    meta_prompt:  document.getElementById('stylePrompt').value.trim(),
    tags,
    is_premium: document.getElementById('styleIsPremium').checked
  };
  let error;
  if (id) {
    ({ error } = await sb.from('ad_styles').update(payload).eq('id', id));
  } else {
    ({ error } = await sb.from('ad_styles').insert(payload));
  }
  btn.disabled = false;
  if (error) { showToast(error.message, 'error'); return; }
  showToast(id ? 'Style updated!' : 'Style added!', 'success');
  closeModal();
  await loadAdminData();
}

async function deleteStyle(id) {
  if (!confirm('Delete this style?')) return;
  const { error } = await sb.from('ad_styles').delete().eq('id', id);
  if (error) { showToast(error.message, 'error'); return; }
  showToast('Style deleted.', 'success');
  await loadAdminData();
}

// ── Category Modal ─────────────────────────────────────────────

function openCatModal(id = null) {
  document.getElementById('editCatId').value = id || '';
  document.getElementById('catForm').reset();
  if (id) {
    const cat = adminCategories.find(c => c.id === id);
    if (cat) {
      document.getElementById('catModalTitle').textContent = 'Edit Category';
      document.getElementById('catName').value = cat.name;
      document.getElementById('catSlug').value = cat.slug;
      document.getElementById('catIcon').value = cat.icon || '';
      document.getElementById('catDesc').value = cat.description || '';
      document.getElementById('catOrder').value = cat.display_order || 0;
    }
  } else {
    document.getElementById('catModalTitle').textContent = 'Add Category';
  }
  document.getElementById('addCatModal').classList.add('open');
}

function editCategory(id) { openCatModal(id); }
function closeCatModal() { document.getElementById('addCatModal').classList.remove('open'); }

async function handleSaveCategory(e) {
  e.preventDefault();
  const id = document.getElementById('editCatId').value;
  const payload = {
    name:          document.getElementById('catName').value.trim(),
    slug:          document.getElementById('catSlug').value.trim(),
    icon:          document.getElementById('catIcon').value.trim() || '🎨',
    description:   document.getElementById('catDesc').value.trim() || null,
    display_order: parseInt(document.getElementById('catOrder').value) || 0
  };
  let error;
  if (id) {
    ({ error } = await sb.from('categories').update(payload).eq('id', id));
  } else {
    ({ error } = await sb.from('categories').insert(payload));
  }
  if (error) { showToast(error.message, 'error'); return; }
  showToast(id ? 'Category updated!' : 'Category added!', 'success');
  closeCatModal();
  await loadAdminData();
}

async function deleteCategory(id) {
  if (!confirm('Delete this category? All its styles will also be deleted.')) return;
  const { error } = await sb.from('categories').delete().eq('id', id);
  if (error) { showToast(error.message, 'error'); return; }
  showToast('Category deleted.', 'success');
  await loadAdminData();
}

// ── User Management ────────────────────────────────────────────

async function adminGrantPremium(userId) {
  // Grant lifetime premium — no expiry date
  const { error } = await sb.from('profiles').update({
    plan_type: 'premium',
    subscription_expires_at: null   // null = lifetime
  }).eq('id', userId);
  if (error) { showToast(error.message, 'error'); return; }
  showToast('Lifetime Premium granted.', 'success');
  await loadAdminData();
}

async function adminRevokePremium(userId) {
  if (!confirm('Revoke premium access for this user?')) return;
  const { error } = await sb.from('profiles').update({
    plan_type: 'free',
    subscription_expires_at: null
  }).eq('id', userId);
  if (error) { showToast(error.message, 'error'); return; }
  showToast('Premium revoked.', 'success');
  await loadAdminData();
}

async function adminResetPassword(email) {
  if (!email) { showToast('No email for this user.', 'error'); return; }
  if (!confirm(`Send password reset email to ${email}?`)) return;
  const { error } = await sb.auth.resetPasswordForEmail(email, {
    redirectTo: window.location.origin + '/auth.html'
  });
  if (error) { showToast(error.message, 'error'); return; }
  showToast(`Password reset email sent to ${email}`, 'success');
}

// ── Create User Modal ──────────────────────────────────────────

function openCreateUserModal() {
  document.getElementById('createUserForm').reset();
  document.getElementById('createUserError').classList.remove('visible');
  document.getElementById('createUserModal').classList.add('open');
}

function closeCreateUserModal() {
  document.getElementById('createUserModal').classList.remove('open');
}

async function handleCreateUser(e) {
  e.preventDefault();
  const btn = document.getElementById('createUserBtn');
  const btnText = document.getElementById('createUserBtnText');
  const spinner = document.getElementById('createUserSpinner');
  const errEl = document.getElementById('createUserError');
  const errMsg = document.getElementById('createUserErrorMsg');

  btn.disabled = true;
  btnText.style.display = 'none';
  spinner.style.display = 'inline-block';
  errEl.classList.remove('visible');

  const name     = document.getElementById('newUserName').value.trim();
  const email    = document.getElementById('newUserEmail').value.trim();
  const password = document.getElementById('newUserPassword').value;
  const premium  = document.getElementById('newUserPremium').checked;

  try {
    const { data: { session } } = await sb.auth.getSession();
    const token = session?.access_token;

    const res = await fetch(`${API_URL}/api/admin/create-user`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ name, email, password, grant_premium: premium })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to create user');

    showToast(`User "${name}" created${premium ? ' with Premium' : ''}.`, 'success');
    closeCreateUserModal();
    await loadAdminData();
  } catch (err) {
    errMsg.textContent = err.message || 'Failed to create user.';
    errEl.classList.add('visible');
  } finally {
    btn.disabled = false;
    btnText.style.display = '';
    spinner.style.display = 'none';
  }
}
