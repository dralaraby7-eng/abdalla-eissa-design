// ============================================================
// Auth — shared across all pages
// ============================================================

let currentUser = null;
let currentProfile = null;
let currentAccess = { all_access: false, category_ids: [], categories: [] };
let authContextVersion = 0;

const AUTH_REQUEST_TIMEOUT_MS = 12000;

function emptyAccess() {
  return { all_access: false, category_ids: [], categories: [] };
}

function withTimeout(promise, label, timeoutMs = AUTH_REQUEST_TIMEOUT_MS) {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${label} timed out. Please try again.`)), timeoutMs);
  });
  return Promise.race([Promise.resolve(promise), timeout]).finally(() => clearTimeout(timer));
}

function applySession(session) {
  const nextUser = session?.user || null;
  const changedUser = currentUser?.id !== nextUser?.id;
  currentUser = nextUser;
  if (changedUser) {
    currentProfile = null;
    currentAccess = emptyAccess();
  }
  if (!currentUser) {
    currentProfile = null;
    currentAccess = emptyAccess();
  }
  renderNavAuth();
}

async function refreshAuthContext(user) {
  if (!user?.id) return;
  const version = ++authContextVersion;
  const [profileResult, accessResult] = await Promise.allSettled([
    fetchProfile(user.id),
    fetchAccessSummary()
  ]);
  if (version !== authContextVersion || currentUser?.id !== user.id) return;
  currentProfile = profileResult.status === 'fulfilled' ? profileResult.value : null;
  currentAccess = accessResult.status === 'fulfilled' ? accessResult.value : emptyAccess();
  if (profileResult.status === 'rejected') console.warn('Profile loading failed:', profileResult.reason);
  if (accessResult.status === 'rejected') console.warn('Access loading failed:', accessResult.reason);
  renderNavAuth();
  document.dispatchEvent(new CustomEvent('authcontextchange'));
}

async function initAuth() {
  try {
    const { data: { session } } = await withTimeout(sb.auth.getSession(), 'Session loading');
    applySession(session);
    if (session?.user) await refreshAuthContext(session.user);
  } catch (error) {
    console.warn('Session loading failed:', error);
    applySession(null);
  }

  sb.auth.onAuthStateChange((_event, session) => {
    // Supabase can deadlock when another async Supabase call is awaited inside
    // this callback. Apply the session synchronously, then load context later.
    applySession(session);
    const user = session?.user;
    if (user) {
      setTimeout(() => refreshAuthContext(user).catch(error => {
        console.warn('Auth context refresh failed:', error);
      }), 0);
    }
  });
}

async function fetchProfile(userId) {
  const first = await withTimeout(
    sb.from('profiles').select('*').eq('id', userId).maybeSingle(),
    'Profile loading'
  );
  if (first.error) throw first.error;
  let data = first.data;
  if (!data) {
    // Profile row missing — the signup trigger may have never fired.
    // Call the self-heal RPC to create it now, then re-read.
    try {
      const repair = await withTimeout(sb.rpc('ensure_profile'), 'Profile repair');
      if (repair.error) throw repair.error;
      const retry = await withTimeout(
        sb.from('profiles').select('*').eq('id', userId).maybeSingle(),
        'Profile reload'
      );
      if (retry.error) throw retry.error;
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
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), AUTH_REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(`${API_URL}/api/prompts/access`, {
      headers: await getAuthHeaders(),
      signal: controller.signal
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
    return emptyAccess();
  } finally {
    clearTimeout(timer);
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
  document.querySelectorAll('.nav-links a[href^="auth.html"]').forEach(link => {
    link.href = currentUser ? 'dashboard.html' : 'auth.html?tab=login';
    link.textContent = currentUser ? 'Dashboard' : 'Log In';
  });
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
  const { data, error } = await withTimeout(
    sb.auth.signInWithPassword({ email, password }),
    'Login',
    20000
  );
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
