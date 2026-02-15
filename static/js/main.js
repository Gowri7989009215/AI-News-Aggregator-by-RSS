/**
 * Main JavaScript file for NewsHub RSS Aggregator
 * Handles dynamic features, auto-refresh, and user interactions
 */

// Global variables
let autoRefreshInterval = null;
let isAutoRefreshing = false;
let lastUpdateTime = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize application features
 */
function initializeApp() {
    updateLastUpdatedTime();
    setupEventListeners();
    initializeTooltips();
    
    // Start auto-refresh if enabled
    if (localStorage.getItem('autoRefreshEnabled') === 'true') {
        startAutoRefresh();
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + R to refresh feeds
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            refreshFeeds();
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            closeAllModals();
        }
        
        // Ctrl/Cmd + K to focus search (if search is implemented)
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            // Focus search input when implemented
        }
    });
    
    // Add smooth scroll behavior
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Handle visibility change for auto-refresh
    document.addEventListener('visibilitychange', function() {
        if (document.hidden && isAutoRefreshing) {
            stopAutoRefresh();
        } else if (!document.hidden && localStorage.getItem('autoRefreshEnabled') === 'true') {
            startAutoRefresh();
        }
    });
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Refresh RSS feeds
 */
function refreshFeeds() {
    showLoadingModal();
    
    fetch('/api/refresh')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Feeds refreshed successfully!', 'success');
                updateLastUpdatedTime();
                
                // Reload the page after a short delay
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showNotification('Failed to refresh feeds: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Error refreshing feeds:', error);
            showNotification('Error refreshing feeds. Please try again.', 'danger');
        })
        .finally(() => {
            hideLoadingModal();
        });
}

/**
 * Toggle auto-refresh functionality
 */
function toggleAutoRefresh() {
    if (isAutoRefreshing) {
        stopAutoRefresh();
    } else {
        startAutoRefresh();
    }
}

/**
 * Start auto-refresh
 */
function startAutoRefresh() {
    if (isAutoRefreshing) return;
    
    isAutoRefreshing = true;
    localStorage.setItem('autoRefreshEnabled', 'true');
    
    const autoRefreshText = document.getElementById('auto-refresh-text');
    const autoRefreshButton = autoRefreshText ? autoRefreshText.parentElement : null;
    
    if (autoRefreshText) {
        autoRefreshText.textContent = 'Stop Auto Refresh';
    }
    
    if (autoRefreshButton) {
        autoRefreshButton.classList.remove('btn-outline-light');
        autoRefreshButton.classList.add('btn-danger');
    }
    
    // Refresh every 10 minutes (600000 ms)
    autoRefreshInterval = setInterval(() => {
        console.log('Auto-refreshing feeds...');
        refreshFeeds();
    }, 600000);
    
    showNotification('Auto-refresh enabled (every 10 minutes)', 'info');
}

/**
 * Stop auto-refresh
 */
function stopAutoRefresh() {
    if (!isAutoRefreshing) return;
    
    isAutoRefreshing = false;
    localStorage.setItem('autoRefreshEnabled', 'false');
    
    const autoRefreshText = document.getElementById('auto-refresh-text');
    const autoRefreshButton = autoRefreshText ? autoRefreshText.parentElement : null;
    
    if (autoRefreshText) {
        autoRefreshText.textContent = 'Auto Refresh';
    }
    
    if (autoRefreshButton) {
        autoRefreshButton.classList.remove('btn-danger');
        autoRefreshButton.classList.add('btn-outline-light');
    }
    
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
    
    showNotification('Auto-refresh disabled', 'info');
}

/**
 * Filter articles by category
 */
function filterByCategory(category) {
    if (category === 'all') {
        window.location.href = '/';
    } else {
        window.location.href = `/category/${encodeURIComponent(category)}`;
    }
}

/**
 * Show loading modal
 */
function showLoadingModal() {
    const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
    modal.show();
}

/**
 * Hide loading modal
 */
function hideLoadingModal() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
    if (modal) {
        modal.hide();
    }
}

/**
 * Close all modals
 */
function closeAllModals() {
    const modals = document.querySelectorAll('.modal.show');
    modals.forEach(modal => {
        const modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
            modalInstance.hide();
        }
    });
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 80px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

/**
 * Update last updated time display
 */
function updateLastUpdatedTime() {
    const lastUpdatedElement = document.getElementById('last-updated');
    if (lastUpdatedElement) {
        const now = new Date();
        lastUpdatedElement.textContent = formatTime(now);
        lastUpdateTime = now;
    }
}

/**
 * Format time for display
 */
function formatTime(date) {
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
}

/**
 * Share article
 */
function shareArticle(url, title) {
    if (navigator.share) {
        navigator.share({
            title: title,
            url: url
        }).catch(err => {
            console.log('Error sharing:', err);
            copyToClipboard(url);
        });
    } else {
        copyToClipboard(url);
    }
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
        document.execCommand('copy');
        showNotification('Link copied to clipboard!', 'success');
    } catch (err) {
        console.error('Failed to copy:', err);
        showNotification('Failed to copy link', 'danger');
    }
    
    document.body.removeChild(textarea);
}

/**
 * Scroll to top
 */
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

/**
 * Show statistics modal
 */
function showStats() {
    const modal = new bootstrap.Modal(document.getElementById('statsModal'));
    const statsContent = document.getElementById('stats-content');
    
    // Show loading state
    statsContent.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2 mb-0">Loading statistics...</p>
        </div>
    `;
    
    modal.show();
    
    // Fetch statistics
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayStats(data.stats);
            } else {
                statsContent.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Failed to load statistics: ${data.error}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error fetching stats:', error);
            statsContent.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Error loading statistics. Please try again.
                </div>
            `;
        });
}

/**
 * Display statistics in modal
 */
function displayStats(stats) {
    const statsContent = document.getElementById('stats-content');
    
    let categoryHtml = '';
    if (stats.category_distribution) {
        for (const [category, count] of Object.entries(stats.category_distribution)) {
            categoryHtml += `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span>${category}</span>
                    <span class="badge bg-primary">${count}</span>
                </div>
            `;
        }
    }
    
    let sourceHtml = '';
    if (stats.source_distribution) {
        for (const [source, count] of Object.entries(stats.source_distribution)) {
            sourceHtml += `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span>${source}</span>
                    <span class="badge bg-success">${count}</span>
                </div>
            `;
        }
    }
    
    statsContent.innerHTML = `
        <div class="row">
            <div class="col-md-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-primary">${stats.total_articles || 0}</h5>
                        <p class="card-text">Total Articles</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-success">${Object.keys(stats.category_distribution || {}).length}</h5>
                        <p class="card-text">Categories</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-info">${Object.keys(stats.source_distribution || {}).length}</h5>
                        <p class="card-text">Sources</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <h6><i class="bi bi-tags me-2"></i>Category Distribution</h6>
                ${categoryHtml || '<p class="text-muted">No data available</p>'}
            </div>
            <div class="col-md-6">
                <h6><i class="bi bi-building me-2"></i>Source Distribution</h6>
                ${sourceHtml || '<p class="text-muted">No data available</p>'}
            </div>
        </div>
        
        <div class="mt-3">
            <small class="text-muted">
                <i class="bi bi-clock me-1"></i>
                Last updated: ${new Date(stats.last_updated).toLocaleString()}
            </small>
        </div>
    `;
}

/**
 * Show about dialog
 */
function showAbout() {
    const aboutContent = `
        <div class="text-center">
            <h4><i class="bi bi-newspaper me-2"></i>NewsHub RSS Aggregator</h4>
            <p class="text-muted">Professional News Aggregation Platform</p>
            <hr>
            <p class="text-start">
                NewsHub is a modern RSS news aggregator that brings you the latest news 
                from trusted sources like Reuters, BBC, and CNN. With real-time updates, 
                smart categorization, and a beautiful interface, staying informed has never been easier.
            </p>
            <p class="text-start">
                <strong>Features:</strong><br>
                • Real-time RSS feed aggregation<br>
                • Smart article categorization<br>
                • Auto-refresh functionality<br>
                • Responsive design<br>
                • No database required<br>
                • Professional UI/UX
            </p>
            <p class="text-muted small">
                Built with Flask, Bootstrap, and modern web technologies.
            </p>
        </div>
    `;
    
    // Create modal dynamically
    const modalHtml = `
        <div class="modal fade" id="aboutModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">About NewsHub</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${aboutContent}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing about modal if present
    const existingModal = document.getElementById('aboutModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add new modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('aboutModal'));
    modal.show();
}

/**
 * Handle online/offline status
 */
window.addEventListener('online', function() {
    showNotification('Connection restored', 'success');
});

window.addEventListener('offline', function() {
    showNotification('Connection lost. Some features may not work.', 'warning');
});

/**
 * Performance monitoring
 */
window.addEventListener('load', function() {
    // Log page load time for performance monitoring
    const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
    console.log(`Page load time: ${loadTime}ms`);
    
    // Show performance warning if load time is too slow
    if (loadTime > 3000) {
        console.warn('Slow page load detected. Consider optimization.');
    }
});
