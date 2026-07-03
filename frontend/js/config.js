// ============================================================
// Abdalla Eissa for Design — Supabase Config
// Replace the values below with your own Supabase project
// ============================================================

const SUPABASE_URL  = 'https://ukjwbcrbnutxemwsebsc.supabase.co';
const SUPABASE_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVrandiY3JibnV0eGVtd3NlYnNjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkxMzY0NDIsImV4cCI6MjA5NDcxMjQ0Mn0.hV7H2PVyPyfo_1ciiq5TddUFwJRx0Xna5isv2r5gEQc';

// FastAPI backend. Render explicitly allows the production Vercel origin.
const API_URL = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
  ? 'http://localhost:8000'
  : 'https://abdalla-eissa-design.onrender.com';

// Free tier: how many characters of the prompt to show before blur
const FREE_PREVIEW_CHARS = 140;

// Supabase client (global — used by all pages)
const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON);

// ---- Helpers -----------------------------------------------

function getParam(key) {
  return new URLSearchParams(window.location.search).get(key);
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer') ||
    (() => { const d = document.createElement('div'); d.id = 'toastContainer'; d.className = 'toast-container'; document.body.appendChild(d); return d; })();
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  const icons = { success: 'fa-check-circle', error: 'fa-circle-xmark', info: 'fa-circle-info' };
  const icon = document.createElement('i');
  icon.className = `fa-solid ${icons[type] || icons.info}`;
  const span = document.createElement('span');
  span.textContent = String(message);   // textContent, not innerHTML — safe against XSS
  t.append(icon, span);
  container.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transform = 'translateX(20px)'; t.style.transition = '0.3s'; setTimeout(() => t.remove(), 300); }, 3500);
}

async function copyToClipboard(text) {
  if (!text) return false;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
    } else {
      const field = document.createElement('textarea');
      field.value = text;
      field.setAttribute('readonly', '');
      field.style.cssText = 'position:fixed;left:-9999px;top:0;opacity:0;';
      document.body.appendChild(field);
      field.select();
      if (!document.execCommand('copy')) throw new Error('Copy command failed');
      field.remove();
    }
    showToast('Meta prompt copied!', 'success');
    return true;
  } catch (error) {
    showToast('Copy failed. Select the prompt and copy it manually.', 'error');
    return false;
  }
}

function downloadJsonPromptFile(title, jsonText) {
  if (!jsonText) {
    showToast('No JSON prompt is available for this style.', 'error');
    return false;
  }
  let normalized;
  try {
    normalized = JSON.stringify(JSON.parse(jsonText), null, 2);
  } catch (error) {
    showToast('This JSON prompt is invalid. Please contact support.', 'error');
    return false;
  }
  const safeTitle = String(title || 'prompt').replace(/[^A-Za-z0-9._-]+/g, '-').replace(/^-+|-+$/g, '') || 'prompt';
  const blob = new Blob([normalized + '\n'], { type: 'application/json;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${safeTitle}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  showToast('JSON prompt downloaded.', 'success');
  return true;
}

function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;')
    .replace(/'/g,'&#39;');
}

async function getAuthHeaders() {
  const { data: { session } } = await sb.auth.getSession();
  return session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {};
}

function timeAgo(dateStr) {
  const diff = (Date.now() - new Date(dateStr)) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
}

// ---- WhatsApp Floating Button (appears on every page) ------
const WHATSAPP_NUMBER = '201065479474';
(function injectWhatsApp() {
  function mount() {
    const a = document.createElement('a');
    a.href = `https://wa.me/${WHATSAPP_NUMBER}`;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.title = 'Chat on WhatsApp';
    a.innerHTML = '<i class="fa-brands fa-whatsapp"></i>';
    a.style.cssText = [
      'position:fixed', 'bottom:24px', 'left:24px',
      'width:54px', 'height:54px',
      'background:#25D366', 'color:#fff',
      'border-radius:50%',
      'display:flex', 'align-items:center', 'justify-content:center',
      'font-size:26px', 'z-index:9999',
      'box-shadow:0 4px 18px rgba(37,211,102,0.45)',
      'transition:transform 0.2s,box-shadow 0.2s',
      'text-decoration:none'
    ].join(';');
    a.onmouseover = () => { a.style.transform = 'scale(1.12)'; a.style.boxShadow = '0 6px 28px rgba(37,211,102,0.65)'; };
    a.onmouseout  = () => { a.style.transform = '';            a.style.boxShadow = '0 4px 18px rgba(37,211,102,0.45)'; };
    document.body.appendChild(a);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
