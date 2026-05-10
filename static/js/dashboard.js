/* ═══════
   ServerOS – Dashboard JS
   Seamless Smooth Edition with HiFi Glassmorphism
   ═══════ */

'use strict';

// ── Constants ──
const USER_NAME = 'StrawHaIthi';
const STATS_POLL_MS = 5000;

// ── DOM helpers ──
const $ = (id) => document.getElementById(id);
const $q = (sel) => document.querySelector(sel);
const $all = (sel) => document.querySelectorAll(sel);

// ─────────────────────────────────────────
// Clock
// ─────────────────────────────────────────
function updateClock() {
    const el = $('headerClock');
    if (!el) return;
    const now = new Date();
    el.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// ─────────────────────────────────────────
// Greeting
// ─────────────────────────────────────────
function updateGreeting() {
    const el = $('greetingText');
    if (!el) return;
    const hour = new Date().getHours();
    let tod = hour < 12 ? 'morning' : hour < 18 ? 'afternoon' : 'evening';
    el.textContent = `Good ${tod}, ${USER_NAME}.`;
}

// ─────────────────────────────────────────
// Wallpaper
// ─────────────────────────────────────────
function loadWallpaper() {
    const bg = $('wallpaperBg');
    if (!bg) return;
    fetch('/api/wallpaper')
        .then(r => r.json())
        .then(data => {
            if (data.type === 'url' && data.value) {
                bg.style.backgroundImage = `url('${data.value}')`;
                bg.style.backgroundAttachment = 'fixed';
            } else if (data.type === 'gradient' && data.value) {
                bg.style.background = data.value;
                bg.style.backgroundAttachment = 'fixed';
            }
        })
        .catch(() => {});
}

// ─────────────────────────────────────────
// Themes
// ─────────────────────────────────────────
function applyTheme(vars) {
    const root = document.documentElement;
    Object.entries(vars).forEach(([key, val]) => {
        root.style.setProperty(key, val);
    });
}

function loadTheme() {
    const themeName = localStorage.getItem('serveros_theme');
    if (!themeName) return;
    fetch('/api/themes').then(r => r.json()).then(themes => {
        if (themes[themeName]) applyTheme(themes[themeName]);
    });
}

window.setTheme = function(name) {
    localStorage.setItem('serveros_theme', name);
    fetch('/api/themes').then(r => r.json()).then(themes => {
        if (themes[name]) {
            applyTheme(themes[name]);
            // Notify children (iframes)
            $all('iframe').forEach(iframe => {
                iframe.contentWindow.postMessage({ type: 'serveros-theme-change', theme: name }, '*');
            });
        }
    });
};

// ─────────────────────────────────────────
// Widget Stats (chips + storage card)
// ─────────────────────────────────────────
function fetchWidgetStats() {
    fetch('/api/widget/stats')
        .then(r => r.json())
        .then(data => {
            const cpuVal = $('cpuValue');
            const ramVal = $('ramValue');
            const diskVal = $('diskValue');
            if (cpuVal) cpuVal.textContent = data.cpu_percent != null ? data.cpu_percent.toFixed(1) + '%' : '—%';
            if (ramVal) ramVal.textContent = data.ram_percent != null ? data.ram_percent.toFixed(1) + '%' : '—%';
            if (diskVal) diskVal.textContent = data.disk_percent != null ? data.disk_percent.toFixed(1) + '%' : '—%';

            // Storage widget fill
            const fill = $('storageWidgetFill');
            const usedLabel = $('storageUsedLabel');
            const totalLabel = $('storageTotalLabel');
            if (fill && data.storage_percent != null) {
                fill.style.width = data.storage_percent + '%';
            }
            if (usedLabel && data.storage_used_tb != null) {
                usedLabel.textContent = data.storage_used_tb.toFixed(2) + ' TB';
            }
            if (totalLabel && data.storage_total_tb != null) {
                totalLabel.textContent = data.storage_total_tb.toFixed(2) + ' TB';
            }
        })
        .catch(() => {});
}

// ─────────────────────────────────────────
// Stats (legacy /api/stats polling)
// ─────────────────────────────────────────
function fetchStats() {
    fetch('/api/stats')
        .then(r => r.json())
        .then(data => {
            const tempEl = $('tempValue');
            if (tempEl && data.temperatures) {
                const temps = Object.values(data.temperatures);
                if (temps.length > 0 && temps[0] !== 'N/A') {
                    tempEl.textContent = temps[0] + '°C';
                }
            }
        })
        .catch(() => {});
}

// ─────────────────────────────────────────
// Storage Section
// ─────────────────────────────────────────
function loadDiskHealth() {
    const el = $('diskHealthList');
    if (!el) return;
    fetch('/api/storage/health')
        .then(r => r.json())
        .then(disks => {
            if (!disks.length) { el.innerHTML = '<div class="storage-loading">No disks found.</div>'; return; }
            el.innerHTML = disks.map(d => `
                <div class="disk-item">
                    <div class="disk-name">${d.device} → ${d.mount}</div>
                    <div class="disk-bar-wrap"><div class="disk-bar-fill" style="width:${d.percent_used}%"></div></div>
                    <div class="disk-meta">${d.used_human} / ${d.total_human} (${d.percent_used}%)</div>
                </div>`).join('');
        })
        .catch(() => { el.innerHTML = '<div class="storage-loading">Error loading disks.</div>'; });
}

function loadExternalDrives() {
    const el = $('externalDrivesList');
    if (!el) return;
    fetch('/api/storage/drives')
        .then(r => r.json())
        .then(drives => {
            if (!drives.length) { el.innerHTML = '<div class="storage-loading">No external drives found.</div>'; return; }
            el.innerHTML = drives.map(d => `
                <div class="drive-item">
                    <div class="drive-name">💾 ${d.model} (${d.size_human})</div>
                    <div class="drive-parts">${d.partitions.map(p => p.mountpoint || 'unmounted').join(', ')}</div>
                </div>`).join('');
        })
        .catch(() => { el.innerHTML = '<div class="storage-loading">No external drives detected.</div>'; });
}

function loadStorage() {
    loadDiskHealth();
    loadExternalDrives();
}

// ─────────────────────────────────────────
// Section Navigation
// ─────────────────────────────────────────
const navItems = $all('.nav-item, .dock-icon[data-section]');

function switchSection(sectionId) {
    $all('.content-section').forEach(s => s.classList.remove('active'));
    const target = $(sectionId);
    if (target) {
        target.classList.add('active');
        // Trigger stagger animation reset
        target.querySelectorAll('.app-tile').forEach((t, i) => {
            t.style.animationDelay = `${i * 0.03}s`;
        });
    }
    navItems.forEach(n => {
        n.classList.toggle('active', n.dataset.section === sectionId.replace('section', '').toLowerCase());
    });
    if (sectionId === 'sectionStorage') loadStorage();
    if (sectionId === 'sectionAppStore') loadAppStore();
}

// ─────────────────────────────────────────
// App Store
// ─────────────────────────────────────────
function loadAppStore() {
    const grid = $('appStoreGrid');
    if (!grid || grid.children.length > 0) return;
    fetch('/api/apps')
        .then(r => r.json())
        .then(apps => {
            grid.innerHTML = apps.map(a => `
                <a href="${a.url}" class="store-card" data-app-id="${a.id}">
                    <span class="store-card-icon">${a.icon}</span>
                    <div class="store-card-info">
                        <div class="store-card-name">${a.name}</div>
                        <div class="store-card-desc">${a.description}</div>
                    </div>
                </a>`).join('');
            // Intercept clicks in app store too
            grid.querySelectorAll('.store-card').forEach(card => {
                card.addEventListener('click', e => {
                    e.preventDefault();
                    openAppInFrame(card.href, card.querySelector('.store-card-name').textContent);
                });
            });
        })
        .catch(() => {});
}

// ─────────────────────────────────────────
// Search
// ─────────────────────────────────────────
let _allApps = [];

function openSearch() {
    const overlay = $('searchModalOverlay');
    if (overlay) {
        overlay.classList.add('open');
        const input = $('searchInput');
        if (input) { input.value = ''; input.focus(); renderSearchResults(''); }
    }
}

function closeSearch() {
    const overlay = $('searchModalOverlay');
    if (overlay) overlay.classList.remove('open');
}

function renderSearchResults(query) {
    const results = $('searchResults');
    if (!results) return;
    const q = query.trim().toLowerCase();
    const filtered = q ? _allApps.filter(a => a.name.toLowerCase().includes(q) || a.description.toLowerCase().includes(q)) : _allApps;
    if (!filtered.length) {
        results.innerHTML = '<div class="search-empty">No apps found.</div>';
        return;
    }
    results.innerHTML = filtered.map(a => `
        <a href="${a.url}" class="search-result-item" data-app-id="${a.id}">
            <span class="search-result-icon">${a.icon}</span>
            <div>
                <div class="search-result-name">${a.name}</div>
                <div class="search-result-desc">${a.description}</div>
            </div>
        </a>`).join('');
    results.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', e => {
            e.preventDefault();
            closeSearch();
            openAppInFrame(item.href, item.querySelector('.search-result-name').textContent);
        });
    });
}

function initSearch() {
    fetch('/api/apps')
        .then(r => r.json())
        .then(apps => { _allApps = apps; })
        .catch(() => {});

    const floatBtn = $('searchFloatBtn');
    const closeBtn = $('searchCloseBtn');
    const input = $('searchInput');
    const overlay = $('searchModalOverlay');

    if (floatBtn) floatBtn.addEventListener('click', openSearch);
    if (closeBtn) closeBtn.addEventListener('click', closeSearch);
    if (overlay) overlay.addEventListener('click', e => { if (e.target === overlay) closeSearch(); });
    if (input) {
        input.addEventListener('input', () => renderSearchResults(input.value));
        input.addEventListener('keydown', e => { if (e.key === 'Escape') closeSearch(); });
    }
    document.addEventListener('keydown', e => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); openSearch(); }
    });
}

// ─────────────────────────────────────────
// App Frame (seamless overlay)
// ─────────────────────────────────────────
function openAppInFrame(url, title) {
    const overlay = $('appFrameOverlay');
    const iframe = $('appFrameIframe');
    const titleEl = $('appFrameTitle');
    if (!overlay || !iframe) { window.location.href = url; return; }
    if (titleEl) titleEl.textContent = title || '';
    iframe.src = url;
    overlay.classList.add('open');
    overlay.classList.add('visible');
    overlay.classList.remove('closing');
    document.body.style.overflow = 'hidden';
}

function closeAppFrame() {
    const overlay = $('appFrameOverlay');
    const iframe = $('appFrameIframe');
    if (!overlay) return;
    overlay.classList.add('closing');
    overlay.classList.remove('visible');
    setTimeout(() => {
        overlay.classList.remove('open', 'closing');
        if (iframe) iframe.src = 'about:blank';
        document.body.style.overflow = '';
    }, 350);
}

function initAppFrame() {
    const backBtn = $('appFrameBackBtn');
    if (backBtn) backBtn.addEventListener('click', closeAppFrame);

    // Intercept app-tile clicks
    document.addEventListener('click', e => {
        const tile = e.target.closest('.app-tile');
        if (tile) {
            e.preventDefault();
            const url = tile.getAttribute('href') || tile.dataset.url;
            const name = tile.dataset.name || tile.querySelector('.app-label')?.textContent || '';
            if (url) openAppInFrame(url, name);
        }
    });

    // Listen for postMessage from iframe
    window.addEventListener('message', e => {
        if (e.data === 'serveros-close-app' || e.data.type === 'serveros-close-app') closeAppFrame();
        if (e.data && e.data.type === 'serveros-theme-change') {
            window.setTheme(e.data.theme);
        }
    });
}

// ─────────────────────────────────────────
// Mobile Sidebar
// ─────────────────────────────────────────
function openMobileSidebar() {
    const sidebar = $('sidebar');
    const overlay = $('sidebarOverlay');
    if (sidebar) { sidebar.style.display = 'flex'; sidebar.style.transform = 'translateX(0)'; }
    if (overlay) overlay.classList.add('show');
}

function closeMobileSidebar() {
    const sidebar = $('sidebar');
    const overlay = $('sidebarOverlay');
    if (sidebar) { sidebar.style.transform = 'translateX(-100%)'; }
    if (overlay) overlay.classList.remove('show');
}

function initMobileSidebar() {
    const toggle = $('sidebarToggle');
    const overlay = $('sidebarOverlay');
    if (toggle) toggle.addEventListener('click', openMobileSidebar);
    if (overlay) overlay.addEventListener('click', closeMobileSidebar);
}

// ─────────────────────────────────────────
// Dock & Nav section switching
// ─────────────────────────────────────────
function initNavigation() {
    document.addEventListener('click', e => {
        const navEl = e.target.closest('[data-section]');
        if (!navEl) return;
        const sec = navEl.dataset.section;
        if (!sec) return;
        const sectionMap = {
            'home': 'sectionHome',
            'appstore': 'sectionAppStore',
            'storage': 'sectionStorage',
        };
        if (sectionMap[sec]) {
            e.preventDefault();
            switchSection(sectionMap[sec]);
        }
    });
}

// ─────────────────────────────────────────
// Resource Guard (notifications)
// ─────────────────────────────────────────
let lastNotificationTime = 0;
function checkResourceGuard(stats) {
    if (!('Notification' in window) || Notification.permission !== 'granted') return;
    const now = Date.now();
    if (now - lastNotificationTime < 300000) return;
    let msg = '';
    if (stats.temperature > 75) msg = '🌡️ High Temp: ' + stats.temperature + '°C';
    else if (stats.storage_percent > 95) msg = '💾 Storage Low: ' + stats.storage_percent + '%';
    if (msg) {
        new Notification('ServerOS Alert', { body: msg });
        lastNotificationTime = now;
    }
}
document.addEventListener('click', () => {
    if (Notification.permission === 'default') Notification.requestPermission();
}, { once: true });

// ─────────────────────────────────────────
// Init
// ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    updateClock();
    updateGreeting();
    loadWallpaper();
    loadTheme();
    fetchWidgetStats();
    fetchStats();
    initSearch();
    initAppFrame();
    initNavigation();
    initMobileSidebar();

    // Clock tick
    setInterval(updateClock, 1000);

    // Stats polling
    setInterval(() => {
        fetchWidgetStats();
        fetchStats();
    }, STATS_POLL_MS);
});
