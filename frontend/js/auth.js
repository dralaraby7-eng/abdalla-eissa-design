// ============================================================
// Auth — shared across all pages
// ============================================================

let currentUser = null;
let currentProfile = null;
let currentAccess = { all_access: false, category_ids: [], categories: [] };

async function initAuth() {
  const { data: { session } } = await sb.auth.getSession();
  if (session) {
    currentUser = session.user;
    currentProfile = await fetchProfile(currentUser.id);
    currentAccess = await fetchAccessSummary();
  }
  renderNavAuth();

  sb.auth.onAuthStateChange(async (_event, session) => {
    currentUser = session?.user || null;
    currentProfile = currentUser ? await fetchProfile(currentUser.id) : null;
    currentAccess = currentUser ? await fetchAccessSummary() : { all_access: false, category_ids: [], categories: [] };
    renderNavAuth();
  });
}

async function fetchProfile(userId) {
  let { data } = await sb.from('profiles').select('*').eq('id', userId).single();
  if (!data) {
    // Profile row missing — the signup trigger may have never fired.
    // Call the self-heal RPC to create it now, then re-read.
    try {
      await sb.rpc('ensure_profile');
      const retry = await sb.from('profiles').select('*').eq('id', userId).single();
      data = retry.data;
    } catch (e) {
      console.warn('ensure_profile RPC failed:', e);
    }
  }
  return data;
}

function isPremium() {
  if (!currentProfile) return false;
  if (currentProfile.is_admin) return true; // admins always have full access
  if (currentAccess?.all_access) return true;
  if (currentProfile.plan_type === 'premium') {
    if (!currentProfile.subscription_expires_at) return true;
    return new Date(currentProfile.subscription_expires_at) > new Date();
  }
  return false;
}

function isAdmin() {
  return currentProfile?.is_admin === true;
}

async function fetchAccessSummary() {
  try {
    const res = await fetch(`${API_URL}/api/prompts/access`, {
      headers: await getAuthHeaders()
    });
    if (!res.ok) return { all_access: false, category_ids: [], categories: [] };
    const data = await res.json();
    return {
      all_access: !!data.all_access,
      category_ids: Array.isArray(data.category_ids) ? data.category_ids : [],
      categories: Array.isArray(data.categories) ? data.categories : []
    };
  } catch (e) {
    console.warn('Access summary failed:', e);
    return { all_access: false, category_ids: [], categories: [] };
  }
}

function hasCategoryAccess(categoryId) {
  if (!categoryId) return false;
  if (isPremium() || isAdmin()) return true;
  return (currentAccess?.category_ids || []).includes(categoryId);
}

function canAccessStyle(style) {
  return isAdmin() || isPremium() || hasCategoryAccess(style?.category_id);
}

function renderNavAuth() {
  const actionsEl = document.getElementById('navActions');
  const mobileActionsEl = document.getElementById('navMobileActions');
  if (!actionsEl) return;

  if (currentUser) {
    const name = currentProfile?.full_name || currentUser.email.split('@')[0];
    const safeName = escapeHtml(name);
    const initial = escapeHtml(name.charAt(0).toUpperCase());
    const planBadge = isPremium()
      ? '<span class="badge-premium">Premium</span>'
      : currentAccess.category_ids.length
        ? '<span class="badge-premium">Category</span>'
        : '<span class="badge-free">Free</span>';
    actionsEl.innerHTML = `
      <div class="nav-user">
        <div class="nav-avatar">${initial}</div>
        <span>${safeName}</span>
        ${planBadge}
      </div>
      ${isAdmin() ? '<a href="admin.html" class="btn btn-sm btn-outline"><i class="fa-solid fa-shield-halved"></i> Admin</a>' : ''}
      <a href="dashboard.html" class="btn btn-sm btn-ghost"><i class="fa-solid fa-grid-2"></i> Dashboard</a>
      <button onclick="signOut()" class="btn btn-sm btn-ghost"><i class="fa-solid fa-right-from-bracket"></i></button>
    `;
    if (mobileActionsEl) mobileActionsEl.innerHTML = actionsEl.innerHTML;
  } else {
    actionsEl.innerHTML = `
      <a href="auth.html?tab=login" class="btn btn-ghost btn-sm">Log In</a>
      <a href="auth.html?tab=signup" class="btn btn-primary btn-sm">Sign Up Free</a>
    `;
    if (mobileActionsEl) mobileActionsEl.innerHTML = actionsEl.innerHTML;
  }
}

async function signOut() {
  await sb.auth.signOut();
  window.location.href = 'index.html';
}

async function signIn(email, password) {
  const { data, error } = await sb.auth.signInWithPassword({ email, password });
  if (error) throw error;
  return data;
}

async function signUp(email, password, fullName) {
  const { data, error } = await sb.auth.signUp({
    email, password,
    options: { data: { full_name: fullName } }
  });
  if (error) throw error;
  return data;
}

// Redirect to auth if not logged in
function requireAuth(redirectBack = true) {
  if (!currentUser) {
    const back = redirectBack ? `?back=${encodeURIComponent(window.location.href)}` : '';
    window.location.href = `auth.html${back}`;
    return false;
  }
  return true;
}

// Redirect to pricing if not premium
function requirePremium() {
  if (!isPremium()) {
    window.location.href = 'pricing.html';
    return false;
  }
  return true;
}
