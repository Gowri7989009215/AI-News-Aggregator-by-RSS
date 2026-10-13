/**
 * NewsHub RSS Aggregator - Main Frontend Engine
 * Modern Vanilla JavaScript for UI state, theming, instant search,
 * bookmarks, previews, and real-time feed synchronization.
 */

// Application State
const AppState = {
    theme: 'light',
    autoRefreshInterval: null,
    isAutoRefreshing: false,
    viewMode: 'grid',
    bookmarks: [],
    searchQuery: '',
    statsCache: null
};

// Initialize Application on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initBookmarks();
    initViewMode();
    initAutoRefresh();
    setupEventListeners();
    setupScrollMonitoring();
});

/* ==========================================================================
   Theme Management (Light & Dark Modes)
   ========================================================================== */
function initTheme() {
    const savedTheme = localStorage.getItem('newshub-theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    AppState.theme = savedTheme || (prefersDark ? 'dark' : 'light');
    applyTheme(AppState.theme);

    // Watch for OS theme changes if user hasn't set manual preference
    if (!savedTheme && window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('newshub-theme')) {
                applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
}

function toggleTheme() {
    AppState.theme = AppState.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('newshub-theme', AppState.theme);
    applyTheme(AppState.theme);
    showToast(`Switched to ${AppState.theme === 'dark' ? 'Dark' : 'Light'} Mode`, 'bi-circle-half');
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        if (theme === 'dark') {
            themeIcon.className = 'bi bi-sun-fill text-warning';
        } else {
            themeIcon.className = 'bi bi-moon-stars';
        }
    }
}

/* ==========================================================================
   Bookmarks Management (LocalStorage)
   ========================================================================== */
function initBookmarks() {
    try {
        const stored = localStorage.getItem('newshub-bookmarks');
        AppState.bookmarks = stored ? JSON.parse(stored) : [];
    } catch (e) {
        console.error('Error reading bookmarks from localStorage:', e);
        AppState.bookmarks = [];
    }
    updateBookmarkUI();
}

function toggleBookmark(url, title, source, image) {
    const index = AppState.bookmarks.findIndex(b => b.url === url);
    if (index >= 0) {
        AppState.bookmarks.splice(index, 1);
        showToast('Article removed from saved items', 'bi-bookmark-x');
    } else {
        AppState.bookmarks.unshift({
            url: url,
            title: title,
            source: source,
            image: image || '',
            savedAt: new Date().toISOString()
        });
        showToast('Article saved to bookmarks', 'bi-bookmark-check-fill');
    }

    try {
        localStorage.setItem('newshub-bookmarks', JSON.stringify(AppState.bookmarks));
    } catch (e) {
        console.error('Error saving bookmarks to localStorage:', e);
    }
    updateBookmarkUI();
}

function updateBookmarkUI() {
    // Update badge counter in navbar
    const badge = document.getElementById('bookmark-badge');
    if (badge) {
        const count = AppState.bookmarks.length;
        badge.textContent = count;
        if (count > 0) {
            badge.classList.remove('d-none');
        } else {
            badge.classList.add('d-none');
        }
    }

    // Update bookmark icon states on all visible cards
    const bookmarkedUrls = new Set(AppState.bookmarks.map(b => b.url));
    document.querySelectorAll('.card-bookmark-btn').forEach(btn => {
        const url = btn.getAttribute('data-url');
        const icon = btn.querySelector('i');
        if (url && bookmarkedUrls.has(url)) {
            btn.classList.add('bookmarked');
            if (icon) icon.className = 'bi bi-bookmark-fill';
        } else {
            btn.classList.remove('bookmarked');
            if (icon) icon.className = 'bi bi-bookmark';
        }
    });
}

function openBookmarksModal() {
    const container = document.getElementById('bookmarks-container');
    if (!container) return;

    if (AppState.bookmarks.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4 text-muted">
                <i class="bi bi-bookmark-x display-4 mb-2"></i>
                <p class="mb-0 fw-semibold">No saved articles yet</p>
                <small>Click the bookmark icon on any article card to save it for reading later.</small>
            </div>
        `;
    } else {
        let html = '<div class="list-group list-group-flush">';
        AppState.bookmarks.forEach((item, index) => {
            html += `
                <div class="list-group-item d-flex align-items-center justify-content-between py-3 px-2 border-bottom" style="background: transparent; color: var(--text-primary); border-color: var(--border-color) !important;">
                    <div class="d-flex align-items-center gap-3 pe-3 flex-grow-1 overflow-hidden">
                        <span class="badge bg-secondary-subtle text-secondary border">${item.source}</span>
                        <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="text-decoration-none fw-semibold text-truncate" style="color: var(--text-primary);">
                            ${item.title}
                        </a>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-outline-primary" title="Open article">
                            <i class="bi bi-box-arrow-up-right"></i>
                        </a>
                        <button class="btn btn-sm btn-outline-danger" onclick="removeBookmarkByIndex(${index})" title="Remove bookmark">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        container.innerHTML = html;
    }

    const modal = new bootstrap.Modal(document.getElementById('bookmarksModal'));
    modal.show();
}

function removeBookmarkByIndex(index) {
    if (index >= 0 && index < AppState.bookmarks.length) {
        AppState.bookmarks.splice(index, 1);
        localStorage.setItem('newshub-bookmarks', JSON.stringify(AppState.bookmarks));
        updateBookmarkUI();
        openBookmarksModal();
    }
}

function clearAllBookmarks() {
    if (AppState.bookmarks.length === 0) return;
    if (confirm('Clear all saved bookmarks?')) {
        AppState.bookmarks = [];
        localStorage.removeItem('newshub-bookmarks');
        updateBookmarkUI();
        openBookmarksModal();
        showToast('All bookmarks cleared', 'bi-trash');
    }
}

/* ==========================================================================
   Live Instant Search & Client-Side Filtering
   ========================================================================== */
function handleLiveSearch(query) {
    AppState.searchQuery = (query || '').trim().toLowerCase();
    const cards = document.querySelectorAll('.article-card');
    const heroShowcase = document.getElementById('hero-showcase');
    let visibleCount = 0;

    cards.forEach(card => {
        const title = card.getAttribute('data-title') || '';
        const desc = card.getAttribute('data-desc') || '';
        const source = (card.getAttribute('data-source') || '').toLowerCase();
        const category = (card.getAttribute('data-category') || '').toLowerCase();

        const matches = !AppState.searchQuery ||
            title.includes(AppState.searchQuery) ||
            desc.includes(AppState.searchQuery) ||
            source.includes(AppState.searchQuery) ||
            category.includes(AppState.searchQuery);

        if (matches) {
            card.style.display = '';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });

    // Toggle hero showcase visibility when searching
    if (heroShowcase) {
        heroShowcase.style.display = AppState.searchQuery ? 'none' : '';
    }

    // Update count display
    const countDisplay = document.getElementById('article-count-display');
    if (countDisplay) {
        countDisplay.innerHTML = `<strong>${visibleCount}</strong> stories`;
    }

    // Show empty state if 0 visible
    let emptySearchNotice = document.getElementById('search-empty-notice');
    if (visibleCount === 0 && cards.length > 0) {
        if (!emptySearchNotice) {
            emptySearchNotice = document.createElement('div');
            emptySearchNotice.id = 'search-empty-notice';
            emptySearchNotice.className = 'text-center py-5 my-4';
            emptySearchNotice.innerHTML = `
                <i class="bi bi-search text-muted display-4 mb-3"></i>
                <h5 class="font-heading">No matching articles for "${AppState.searchQuery}"</h5>
                <p class="text-muted small">Try searching with broader terms or clear your search input.</p>
                <button class="btn btn-outline-primary btn-sm" onclick="clearLiveSearch()">Clear Search</button>
            `;
            const grid = document.getElementById('articles-grid');
            if (grid && grid.parentNode) {
                grid.parentNode.appendChild(emptySearchNotice);
            }
        }
    } else if (emptySearchNotice) {
        emptySearchNotice.remove();
    }
}

function clearLiveSearch() {
    const input = document.getElementById('live-search-input');
    if (input) {
        input.value = '';
        handleLiveSearch('');
    }
}

/* ==========================================================================
   View Mode (Grid vs Compact List)
   ========================================================================== */
function initViewMode() {
    const saved = localStorage.getItem('newshub-viewmode') || 'grid';
    setViewMode(saved, false);
}

function setViewMode(mode, save = true) {
    AppState.viewMode = mode;
    if (save) localStorage.setItem('newshub-viewmode', mode);

    const grid = document.getElementById('articles-grid');
    const gridBtn = document.getElementById('view-mode-grid');
    const compactBtn = document.getElementById('view-mode-compact');

    if (!grid) return;

    if (mode === 'compact') {
        grid.style.gridTemplateColumns = '1fr';
        document.querySelectorAll('.article-card').forEach(card => {
            card.classList.add('flex-md-row');
            const thumb = card.querySelector('.card-thumb-container');
            if (thumb) {
                thumb.style.width = '240px';
                thumb.style.minWidth = '240px';
                thumb.style.height = 'auto';
            }
        });
        if (gridBtn) gridBtn.classList.remove('active');
        if (compactBtn) compactBtn.classList.add('active');
    } else {
        grid.style.gridTemplateColumns = '';
        document.querySelectorAll('.article-card').forEach(card => {
            card.classList.remove('flex-md-row');
            const thumb = card.querySelector('.card-thumb-container');
            if (thumb) {
                thumb.style.width = '';
                thumb.style.minWidth = '';
                thumb.style.height = '190px';
            }
        });
        if (gridBtn) gridBtn.classList.add('active');
        if (compactBtn) compactBtn.classList.remove('active');
    }
}

/* ==========================================================================
   Quick Article Preview Modal (Ethical OpenGraph Scraper)
   ========================================================================== */
function openPreviewModal(url, title, source, relativeTime) {
    const modalEl = document.getElementById('previewModal');
    if (!modalEl) return;

    const modal = new bootstrap.Modal(modalEl);
    
    // Set headers & initial states
    document.getElementById('preview-source-badge').textContent = source;
    document.getElementById('preview-time-ago').textContent = relativeTime || 'Recently';
    document.getElementById('preview-title').textContent = title;
    document.getElementById('preview-external-link').href = url;
    
    const loadingEl = document.getElementById('preview-loading');
    const contentEl = document.getElementById('preview-content');
    const imgEl = document.getElementById('preview-img');
    const descEl = document.getElementById('preview-description');
    const leadEl = document.getElementById('preview-lead-text');
    const authorEl = document.getElementById('preview-author');
    const readingEl = document.getElementById('preview-reading-time');

    loadingEl.classList.remove('d-none');
    contentEl.classList.add('d-none');
    imgEl.classList.add('d-none');
    leadEl.classList.add('d-none');
    descEl.textContent = '';

    modal.show();

    // Call ethical backend preview endpoint
    fetch(`/api/preview?url=${encodeURIComponent(url)}`)
        .then(res => res.json())
        .then(data => {
            loadingEl.classList.add('d-none');
            contentEl.classList.remove('d-none');

            if (data.success && data.metadata) {
                const meta = data.metadata;
                if (meta.image) {
                    imgEl.src = meta.image;
                    imgEl.classList.remove('d-none');
                }
                descEl.textContent = meta.description || 'Full coverage available directly on publisher site.';
                
                if (meta.lead_text) {
                    leadEl.textContent = `"${meta.lead_text}"`;
                    leadEl.classList.remove('d-none');
                }
                if (meta.author) {
                    authorEl.innerHTML = `<i class="bi bi-person me-1"></i>${meta.author}`;
                } else {
                    authorEl.innerHTML = `<i class="bi bi-building me-1"></i>${source}`;
                }
                if (meta.reading_time_minutes) {
                    readingEl.innerHTML = `<i class="bi bi-stopwatch me-1"></i>${meta.reading_time_minutes} min read`;
                }
            } else {
                descEl.textContent = 'Preview excerpt not available. Please view the full story on publisher website.';
            }
        })
        .catch(err => {
            console.error('Error fetching preview:', err);
            loadingEl.classList.add('d-none');
            contentEl.classList.remove('d-none');
            descEl.textContent = 'Unable to extract remote preview. Click below to view directly on publisher site.';
        });
}

/* ==========================================================================
   Feed Refresh & Synchronization
   ========================================================================== */
function refreshFeeds() {
    const refreshBtn = document.getElementById('refresh-feeds-btn');
    const refreshIcon = document.getElementById('refresh-icon');

    if (refreshIcon) refreshIcon.classList.add('spin-animation');
    if (refreshBtn) refreshBtn.disabled = true;

    showToast('Syncing 10 news feeds...', 'bi-arrow-clockwise');

    fetch('/api/refresh')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(`Refreshed ${data.total_articles} articles across 10 sources`, 'bi-check2-circle');
                setTimeout(() => {
                    window.location.reload();
                }, 800);
            } else {
                showToast('Refresh failed: ' + (data.error || 'Server error'), 'bi-exclamation-triangle');
            }
        })
        .catch(err => {
            console.error('Error refreshing feeds:', err);
            showToast('Network error while refreshing feeds', 'bi-wifi-off');
        })
        .finally(() => {
            if (refreshIcon) refreshIcon.classList.remove('spin-animation');
            if (refreshBtn) refreshBtn.disabled = false;
        });
}

function initAutoRefresh() {
    const saved = localStorage.getItem('newshub-autorefresh');
    if (saved === 'true') {
        startAutoRefresh(false);
    }
}

function toggleAutoRefresh() {
    if (AppState.isAutoRefreshing) {
        stopAutoRefresh();
    } else {
        startAutoRefresh(true);
    }
}

function startAutoRefresh(notify = true) {
    AppState.isAutoRefreshing = true;
    localStorage.setItem('newshub-autorefresh', 'true');

    const btn = document.getElementById('auto-refresh-btn');
    const label = document.getElementById('auto-refresh-label');
    if (btn) btn.classList.add('active');
    if (label) label.textContent = 'Auto: On';

    if (AppState.autoRefreshInterval) clearInterval(AppState.autoRefreshInterval);
    // Background refresh every 5 minutes (300,000ms)
    AppState.autoRefreshInterval = setInterval(() => {
        refreshFeeds();
    }, 300000);

    if (notify) showToast('Auto-refresh active (updates every 5 mins)', 'bi-clock-history');
}

function stopAutoRefresh() {
    AppState.isAutoRefreshing = false;
    localStorage.setItem('newshub-autorefresh', 'false');

    const btn = document.getElementById('auto-refresh-btn');
    const label = document.getElementById('auto-refresh-label');
    if (btn) btn.classList.remove('active');
    if (label) label.textContent = 'Auto';

    if (AppState.autoRefreshInterval) {
        clearInterval(AppState.autoRefreshInterval);
        AppState.autoRefreshInterval = null;
    }
    showToast('Auto-refresh deactivated', 'bi-pause-circle');
}

/* ==========================================================================
   Aggregation Statistics Modal
   ========================================================================== */
function showStats() {
    const modalEl = document.getElementById('statsModal');
    const statsContainer = document.getElementById('stats-content');
    if (!modalEl || !statsContainer) return;

    const modal = new bootstrap.Modal(modalEl);
    modal.show();

    statsContainer.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2 text-muted small">Loading live aggregator metrics...</p>
        </div>
    `;

    fetch('/api/stats')
        .then(res => res.json())
        .then(data => {
            if (data.success && data.stats) {
                renderStats(data.stats, statsContainer);
            } else {
                statsContainer.innerHTML = '<div class="alert alert-danger">Failed to load statistics.</div>';
            }
        })
        .catch(err => {
            console.error('Error fetching stats:', err);
            statsContainer.innerHTML = '<div class="alert alert-danger">Error fetching stats. Please retry.</div>';
        });
}

function renderStats(stats, container) {
    const total = stats.total_articles || 1;
    
    // Category Breakdown Bars
    let catHtml = '';
    for (const [cat, count] of Object.entries(stats.category_distribution || {})) {
        const pct = Math.round((count / total) * 100);
        catHtml += `
            <div class="mb-2">
                <div class="d-flex justify-content-between small mb-1">
                    <span class="fw-semibold">${cat}</span>
                    <span class="text-muted">${count} articles (${pct}%)</span>
                </div>
                <div class="progress" style="height: 6px; background: var(--bg-surface-muted);">
                    <div class="progress-bar bg-primary" role="progressbar" style="width: ${pct}%"></div>
                </div>
            </div>
        `;
    }

    // Source Breakdown Bars
    let srcHtml = '';
    for (const [src, count] of Object.entries(stats.source_distribution || {})) {
        const pct = Math.round((count / total) * 100);
        srcHtml += `
            <div class="mb-2">
                <div class="d-flex justify-content-between small mb-1">
                    <span class="fw-semibold">${src}</span>
                    <span class="text-muted">${count} articles (${pct}%)</span>
                </div>
                <div class="progress" style="height: 6px; background: var(--bg-surface-muted);">
                    <div class="progress-bar bg-success" role="progressbar" style="width: ${pct}%"></div>
                </div>
            </div>
        `;
    }

    container.innerHTML = `
        <div class="row g-3 mb-4 text-center">
            <div class="col-4">
                <div class="p-3 rounded-3" style="background: var(--bg-surface-muted); border: 1px solid var(--border-color);">
                    <h3 class="font-heading text-primary mb-0">${stats.total_articles}</h3>
                    <small class="text-muted">Total Stories</small>
                </div>
            </div>
            <div class="col-4">
                <div class="p-3 rounded-3" style="background: var(--bg-surface-muted); border: 1px solid var(--border-color);">
                    <h3 class="font-heading text-success mb-0">${stats.total_sources || 10}</h3>
                    <small class="text-muted">Active Feeds</small>
                </div>
            </div>
            <div class="col-4">
                <div class="p-3 rounded-3" style="background: var(--bg-surface-muted); border: 1px solid var(--border-color);">
                    <h3 class="font-heading text-info mb-0">${stats.cache_info ? stats.cache_info.cache_duration_minutes : 5}m</h3>
                    <small class="text-muted">Cache TTL</small>
                </div>
            </div>
        </div>

        <div class="row g-4">
            <div class="col-md-6">
                <h6 class="font-heading mb-3"><i class="bi bi-pie-chart me-1 text-primary"></i> Category Distribution</h6>
                ${catHtml}
            </div>
            <div class="col-md-6">
                <h6 class="font-heading mb-3"><i class="bi bi-building me-1 text-success"></i> Source Distribution</h6>
                ${srcHtml}
            </div>
        </div>

        <div class="pt-3 mt-3 border-top text-muted small d-flex justify-content-between" style="border-color: var(--border-color) !important;">
            <span><i class="bi bi-clock me-1"></i>Last Synced: ${new Date(stats.last_updated).toLocaleTimeString()}</span>
            <span>In-Memory Cache Active</span>
        </div>
    `;
}

/* ==========================================================================
   Article Sharing (Web Share API + Clipboard Fallback)
   ========================================================================== */
function shareArticle(url, title) {
    if (navigator.share) {
        navigator.share({
            title: title,
            text: `Read "${title}" on NewsHub:`,
            url: url
        }).catch(err => {
            if (err.name !== 'AbortError') {
                copyUrlToClipboard(url);
            }
        });
    } else {
        copyUrlToClipboard(url);
    }
}

function copyUrlToClipboard(url) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url)
            .then(() => showToast('Article link copied to clipboard!', 'bi-clipboard-check-fill'))
            .catch(() => fallbackClipboard(url));
    } else {
        fallbackClipboard(url);
    }
}

function fallbackClipboard(url) {
    const input = document.createElement('input');
    input.value = url;
    document.body.appendChild(input);
    input.select();
    try {
        document.execCommand('copy');
        showToast('Link copied to clipboard!', 'bi-clipboard-check-fill');
    } catch (e) {
        showToast('Could not copy link', 'bi-x-circle');
    }
    document.body.removeChild(input);
}

/* ==========================================================================
   Toast Notifications & UI Helpers
   ========================================================================== */
let toastTimeout = null;

function showToast(message, iconClass = 'bi-info-circle') {
    const toast = document.getElementById('app-toast');
    const msgEl = document.getElementById('toast-message');
    const iconEl = document.getElementById('toast-icon');

    if (!toast || !msgEl) return;

    msgEl.textContent = message;
    if (iconEl && iconClass) {
        iconEl.className = `bi ${iconClass}`;
    }

    toast.classList.add('show');
    if (toastTimeout) clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
        toast.classList.remove('show');
    }, 3200);
}

function setupScrollMonitoring() {
    const btn = document.getElementById('backToTopBtn');
    if (!btn) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
    }, { passive: true });
}

function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

function setupEventListeners() {
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + R -> refresh feeds
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            refreshFeeds();
        }

        // Forward slash '/' or Ctrl+K -> focus search
        if ((e.key === '/' || ((e.ctrlKey || e.metaKey) && e.key === 'k')) && document.activeElement.tagName !== 'INPUT') {
            const search = document.getElementById('live-search-input');
            if (search) {
                e.preventDefault();
                search.focus();
                search.select();
            }
        }

        // Escape -> close open modals or blur search
        if (e.key === 'Escape') {
            const search = document.getElementById('live-search-input');
            if (search && document.activeElement === search) {
                search.blur();
            }
        }
    });
}

// CSS Rotation helper
const style = document.createElement('style');
style.textContent = `
    .spin-animation {
        animation: spin 0.8s linear infinite;
        display: inline-block;
    }
    @keyframes spin {
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);
