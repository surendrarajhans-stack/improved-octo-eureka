const qs = (s, p=document) => p.querySelector(s);
const qsa = (s, p=document) => [...p.querySelectorAll(s)];
function setTheme(theme){ document.documentElement.setAttribute('data-theme', theme); localStorage.setItem('theme', theme); }
function initTheme(){ setTheme(localStorage.getItem('theme') || 'light'); }
function showToast(message, type='primary'){ const wrap = qs('#toast-container'); if(!wrap) return; const el = document.createElement('div'); el.className = `toast align-items-center text-bg-${type} border-0`; el.innerHTML = `<div class="d-flex"><div class="toast-body">${message}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>`; wrap.appendChild(el); new bootstrap.Toast(el, {delay: 4000}).show(); el.addEventListener('hidden.bs.toast', ()=>el.remove()); }
async function fetchJSON(url, options={}){ const res = await fetch(url, {headers: {'X-Requested-With':'fetch', ...(options.headers||{})}, ...options}); if(!res.ok){ const text = await res.text(); throw new Error(text || `HTTP ${res.status}`); } return res.headers.get('content-type')?.includes('application/json') ? res.json() : res.text(); }
async function postJSON(url, body){ return fetchJSON(url, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)}); }
function debounce(fn, wait=300){ let t; return (...args)=>{ clearTimeout(t); t=setTimeout(()=>fn(...args), wait); }; }
function initSidebar(){ qs('#sidebarToggle')?.addEventListener('click', ()=> qs('.sidebar')?.classList.toggle('show')); }
function initThemeToggle(){ qs('#themeToggle')?.addEventListener('click', ()=> setTheme((localStorage.getItem('theme')||'light') === 'light' ? 'dark' : 'light')); }
function initValidation(){ qsa('form.needs-validation').forEach(form=>form.addEventListener('submit', e=>{ if(!form.checkValidity()){ e.preventDefault(); e.stopPropagation(); } form.classList.add('was-validated'); })); }
function initAutoRefresh(){ const seconds = Number(document.body.dataset.refresh || 0); if(seconds > 0){ setInterval(()=>window.location.reload(), seconds * 1000); } }
function initGlobalSearch(){ const input = qs('#globalSearch'); if(!input) return; input.addEventListener('input', debounce(()=>{ const query = input.value.toLowerCase(); qsa('[data-searchable]').forEach(row=> row.classList.toggle('d-none', !row.dataset.searchable.toLowerCase().includes(query))); }, 200)); }
async function pollNotifications(){ const bell = qs('#notificationCount'); if(!bell) return; try { const data = await fetchJSON('/notifications/unread-count'); bell.textContent = data.count; } catch (e) {} }
function initPolling(){ pollNotifications(); setInterval(pollNotifications, 60000); }
function initConfirmations(){ qsa('[data-confirm]').forEach(btn=>btn.addEventListener('click', e=>{ if(!window.confirm(btn.dataset.confirm)){ e.preventDefault(); } })); }
function formatDateTime(value){ try { return new Intl.DateTimeFormat(undefined, {dateStyle:'medium', timeStyle:'short'}).format(new Date(value)); } catch { return value; } }
window.App = {fetchJSON, postJSON, showToast, formatDateTime};
document.addEventListener('DOMContentLoaded', ()=>{ initTheme(); initSidebar(); initThemeToggle(); initValidation(); initAutoRefresh(); initGlobalSearch(); initPolling(); initConfirmations(); const flash = document.cookie.split('; ').find(v=>v.startsWith('flash_message=')); if(flash){ showToast(decodeURIComponent(flash.split('=')[1]), 'success'); document.cookie = 'flash_message=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/'; } });
