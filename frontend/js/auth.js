// ============================================================
// Auth — shared across all pages
// ============================================================

let currentUser = null;
let currentProfile = null;

async function initAuth() {
  const { data: { session } } = await sb.auth.getSession();
  if (session) {
    currentUser = session.user;
    currentProfile = await fetchProfile(currentUser.id);
  }
  renderNavAuth();

  sb.auth.onAuthStateChange(async (_event, session) => {
    currentUser = session?.user || null;
    currentProfile = currentUser ? await fetchProfile(currentUser.id) : null;
    renderNavAuth();
  });
}

async function fetchProfile(userId) {
  const { data } = await sb.from('profiles').select('*').eq('id', userId).single();
  return data;
}

function isPremium() {
  if (!currentProfile) return false;
  if (currentProfile.plan_type === 'premium') {
    if (!currentProfile.subscription_expires_at) return true;
    return new Date(currentProfile.subscription_expires_at) > new Date();
  }
  return false;
}

function isAdmin() {
  return currentProfile?.is_admin === true;
}

function renderNavAuth() {
  const actionsEl = document.getElementById('navActions');
  const mobileActionsEl = document.getElementById('navMobileActions');
  if (!actionsEl) return;

  if (currentUser) {
    const name = currentProfile?.full_name || currentUser.email.split('@')[0];
    const initial = name.charAt(0).toUpperCase();
    const planBadge = isPremium()
      ? '<span class="badge-premium">Premium</span>'
      : '<span class="badge-free">Free</span>';
    actionsEl.innerHTML = `
      <div class="nav-user">
        <div class="nav-avatar">${initial}</div>
        <span>${name}</span>
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
