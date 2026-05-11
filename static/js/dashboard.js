'use strict';

const STATS_POLL_MS = 5000;
let _allApps = [];
let _pinnedIds = [];

const $ = (id) => document.getElementById(id);
const $all = (sel) => document.querySelectorAll(sel);

function updateGreeting() {
    const el = $('greetingText');
    if (!el) return;
    const hour = new Date().getHours();
    let greeting = "";
    if (hour >= 4 && hour < 12) greeting = "Good Morning";
    else if (hour >= 12 && hour < 17) greeting = "Good Afternoon";
    else if (hour >= 17 && hour < 22) greeting = "Good Evening";
    else greeting = "Good Night";
    el.textContent = `${greeting}, Ithiel.`;
}

async function loadWallpaper() {
    try {
        const res = await fetch('/api/wallpaper');
        const data = await res.json();
        const bg = $('wallpaperBg');
        if (!bg) return;
        if (data.type === 'url' || data.type === 'image') bg.style.backgroundImage = `url('${data.value}')`;
        else bg.style.background = data.value;
    } catch(e) {}
}

async function fetchStats() {
    try {
        const [res, statsRes] = await Promise.all([
            fetch('/api/widget/stats'),
            fetch('/api/stats')
        ]);
        const data = await res.json();
        const fullStats = await statsRes.json();

        if ($('cpuValue')) $('cpuValue').textContent = Math.round(data.cpu_percent) + '%';
        if ($('ramValue')) $('ramValue').textContent = data.ram_used_gb.toFixed(1) + ' GB';
        
        if ($('tempValue') && fullStats.temperatures) {
            const temps = Object.values(fullStats.temperatures);
            if (temps.length > 0) {
                const t = temps[0];
                $('tempValue').textContent = Math.round(t) + '°C';
                // Resource Guard: Alert on High Temp
                if (t > 80) showSystemNotification('🔥 High Temp Warning', `Pi temperature is ${t}°C!`);
            }
        }

        const storageText = $('storageWidgetText');
        const storageFill = $('storageWidgetFill');
        if (storageText) storageText.textContent = data.storage_used_tb.toFixed(2) + ' TB / ' + data.storage_total_tb.toFixed(2) + ' TB';
        if (storageFill) {
            storageFill.style.width = data.storage_percent + '%';
            if (data.storage_percent > 95) showSystemNotification('💾 Storage Critical', `Disk usage is at ${data.storage_percent}%!`);
        }
    } catch(e) {}
}

let _lastNotif = 0;
function showSystemNotification(title, body) {
    if (!("Notification" in window) || Notification.permission !== "granted") return;
    if (Date.now() - _lastNotif < 300000) return; // Limit to every 5 mins
    new Notification(title, { body });
    _lastNotif = Date.now();
}

async function loadApps() {
    try {
        const [appsRes, pinnedRes] = await Promise.all([
            fetch('/api/apps'),
            fetch('/app/wallpaper/api/pinned')
        ]);
        _allApps = await appsRes.json();
        _pinnedIds = await pinnedRes.json();
        renderHomeGrid();
        renderFullGrid();
    } catch(e) {}
}

function renderHomeGrid() {
    const grid = $('homeAppGrid');
    if (!grid) return;
    let displayApps = _allApps.filter(a => _pinnedIds.includes(a.id));
    if (displayApps.length === 0) displayApps = _allApps.slice(0, 6);
    grid.innerHTML = displayApps.map((a, i) => renderAppTile(a, i)).join('');
}

function renderFullGrid() {
    const grid = $('fullAppGrid');
    if (!grid) return;
    grid.innerHTML = _allApps.map((a, i) => renderAppTile(a, i)).join('');
}

function renderAppTile(a, index) {
    return `
        <a href="${a.url}" class="app-tile" data-name="${a.name}" onclick="handleAppClick(event, '${a.url}', '${a.name}')" style="--tile-color: ${a.color}; animation-delay: ${index * 0.05}s">
            <div class="app-squircle">
                <span class="app-emoji">${a.icon}</span>
            </div>
            <span class="app-label">${a.name}</span>
        </a>`;
}

window.handleAppClick = (e, url, name) => {
    e.preventDefault();
    openAppInFrame(url, name);
};

window.openAppInFrame = (url, title) => {
    const overlay = $('appFrameOverlay');
    const iframe = $('appFrameIframe');
    $('appFrameTitle').textContent = title;
    iframe.src = url;
    overlay.style.display = 'flex';
    document.body.style.overflow = 'hidden';
};

window.closeAppFrame = () => {
    const overlay = $('appFrameOverlay');
    overlay.style.display = 'none';
    $('appFrameIframe').src = '';
    document.body.style.overflow = '';
};

function initNavigation() {
    $all('.dock-icon').forEach(icon => {
        icon.addEventListener('click', (e) => {
            const section = icon.dataset.section;
            if (!section) return;
            e.preventDefault();
            $all('.content-section').forEach(s => s.classList.remove('active'));
            $all('.dock-icon').forEach(i => i.classList.remove('active'));
            const target = section === 'home' ? 'sectionHome' : 'sectionAppStore';
            $(target).classList.add('active');
            icon.classList.add('active');
            if (section === 'home') renderHomeGrid();
            else if (section === 'appstore') renderFullGrid();
        });
    });
}

window.openSearch = () => {
    const appStoreIcon = document.querySelector('.dock-icon[data-section="appstore"]');
    if (appStoreIcon) appStoreIcon.click();
};

document.addEventListener('DOMContentLoaded', () => {
    updateGreeting();
    loadWallpaper();
    loadApps();
    fetchStats();
    initNavigation();
    if ("Notification" in window) Notification.requestPermission();
    setInterval(fetchStats, STATS_POLL_MS);
    setInterval(updateGreeting, 60000);
});
