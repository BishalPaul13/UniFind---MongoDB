/**
 * UniFind - Frontend Application Controller
 * Handles RESTful CRUD interactions with PyMongo, Chart.js visualizer for
 * MongoDB aggregation pipelines, and live schema validation inspector.
 */

// Application State
const state = {
    items: [],
    activeItem: null,
    filters: {
        type: '',
        category: '',
        location: '',
        status: '',
        search: '',
        sort: 'date_desc'
    },
    charts: {
        hotspots: null,
        categories: null,
        turnaround: null,
        roles: null
    }
};

// DOM Content Loaded Handler
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initTabNavigation();
    initModals();
    initFilterListeners();
    initFormSubmissions();
    initPresentationButtons();

    // Initial Data Fetch
    fetchKPIs();
    fetchItems();
    fetchAnalytics();
    fetchSchema();
});

/* ==========================================================================
   Theme Management
   ========================================================================== */
function initTheme() {
    const savedTheme = localStorage.getItem('unifind_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    document.getElementById('theme-toggle').addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', nextTheme);
        localStorage.setItem('unifind_theme', nextTheme);
        updateThemeIcon(nextTheme);

        // Re-render charts with updated theme colors
        if (state.charts.hotspots) fetchAnalytics();
    });
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (icon) icon.textContent = theme === 'dark' ? '☀️' : '🌙';
}

/* ==========================================================================
   Tab Navigation
   ========================================================================== */
function initTabNavigation() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => {
                b.classList.remove('active');
                b.setAttribute('aria-selected', 'false');
            });
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            btn.setAttribute('aria-selected', 'true');
            const targetId = btn.getAttribute('data-tab');
            const targetContent = document.getElementById(targetId);
            if (targetContent) targetContent.classList.add('active');

            // If switching to analytics, resize or re-draw charts
            if (targetId === 'tab-analytics') {
                setTimeout(() => {
                    Object.values(state.charts).forEach(chart => {
                        if (chart) chart.resize();
                    });
                }, 100);
            }
        });
    });
}

/* ==========================================================================
   Modals Management
   ========================================================================== */
function initModals() {
    // Open Create Modal
    document.getElementById('btn-open-create-modal').addEventListener('click', () => {
        document.getElementById('form-create-item').reset();
        openModal('modal-create');
    });

    // Close buttons
    document.querySelectorAll('[data-close]').forEach(btn => {
        btn.addEventListener('click', () => {
            const modalId = btn.getAttribute('data-close');
            closeModal(modalId);
        });
    });

    // Backdrop click to close
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                closeModal(backdrop.id);
            }
        });
    });

    // Escape key listener
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-backdrop').forEach(modal => {
                if (modal.style.display !== 'none') closeModal(modal.id);
            });
        }
    });
}

function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = 'flex';
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = 'none';
}

/* ==========================================================================
   CRUD: READ - Items Listing, Filters, & Search
   ========================================================================== */
function initFilterListeners() {
    // Type pills
    document.querySelectorAll('.pill-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.filters.type = btn.getAttribute('data-type');
            fetchItems();
        });
    });

    // Dropdowns
    document.getElementById('filter-category').addEventListener('change', (e) => {
        state.filters.category = e.target.value;
        fetchItems();
    });

    document.getElementById('filter-location').addEventListener('change', (e) => {
        state.filters.location = e.target.value;
        fetchItems();
    });

    document.getElementById('filter-status').addEventListener('change', (e) => {
        state.filters.status = e.target.value;
        fetchItems();
    });

    document.getElementById('filter-sort').addEventListener('change', (e) => {
        state.filters.sort = e.target.value;
        fetchItems();
    });

    // Search Box with Debounce
    const searchInput = document.getElementById('input-search');
    const clearBtn = document.getElementById('btn-clear-search');

    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        const query = e.target.value.trim();
        clearBtn.style.display = query ? 'block' : 'none';

        debounceTimer = setTimeout(() => {
            state.filters.search = query;
            fetchItems();
        }, 300);
    });

    clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        clearBtn.style.display = 'none';
        state.filters.search = '';
        fetchItems();
    });

    // Refresh & Reset buttons
    document.getElementById('btn-refresh-items').addEventListener('click', () => {
        fetchItems();
        fetchKPIs();
    });

    document.getElementById('btn-reset-filters').addEventListener('click', resetFilters);
}

function resetFilters() {
    state.filters = { type: '', category: '', location: '', status: '', search: '', sort: 'date_desc' };
    document.querySelectorAll('.pill-btn').forEach((b, idx) => b.classList.toggle('active', idx === 0));
    document.getElementById('filter-category').value = '';
    document.getElementById('filter-location').value = '';
    document.getElementById('filter-status').value = '';
    document.getElementById('filter-sort').value = 'date_desc';
    document.getElementById('input-search').value = '';
    document.getElementById('btn-clear-search').style.display = 'none';
    fetchItems();
}

async function fetchItems() {
    const metaBar = document.getElementById('items-count-text');
    metaBar.textContent = 'Querying MongoDB...';

    const params = new URLSearchParams();
    if (state.filters.type) params.append('type', state.filters.type);
    if (state.filters.category) params.append('category', state.filters.category);
    if (state.filters.location) params.append('location', state.filters.location);
    if (state.filters.status) params.append('status', state.filters.status);
    if (state.filters.search) params.append('search', state.filters.search);
    if (state.filters.sort) params.append('sort', state.filters.sort);

    try {
        const response = await fetch(`/api/items?${params.toString()}`);
        const data = await response.json();

        if (data.success) {
            state.items = data.items;
            renderItemsGrid(data.items);
            if (data.teacher_filter_active) {
                metaBar.innerHTML = `Showing ${data.items.length} item${data.items.length === 1 ? '' : 's'} <span class="badge-tech" style="margin-left: 8px;">Code Filter: ${escapeHtml(JSON.stringify(data.active_code_filter))}</span>`;
            } else {
                metaBar.textContent = `Showing ${data.items.length} item${data.items.length === 1 ? '' : 's'} from MongoDB collection`;
            }
        } else {
            showToast(data.error || 'Failed to fetch items', 'error');
            metaBar.textContent = 'Error querying database';
        }
    } catch (err) {
        console.error('Fetch error:', err);
        showToast('Connection error querying MongoDB', 'error');
        metaBar.textContent = 'Connection error';
    }
}

function renderItemsGrid(items) {
    const grid = document.getElementById('items-grid');
    const emptyState = document.getElementById('items-empty-state');

    if (!items || items.length === 0) {
        grid.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }

    emptyState.style.display = 'none';
    grid.innerHTML = items.map(item => {
        const typeBadgeClass = item.type === 'Lost' ? 'badge-lost' : 'badge-found';
        const statusSlug = item.status ? item.status.replace(/\s+/g, '-') : 'Open';
        const formattedDate = item.date_reported ? new Date(item.date_reported).toLocaleDateString(undefined, {
            month: 'short', day: 'numeric', year: 'numeric'
        }) : 'Recent';

        return `
            <div class="item-card" onclick="viewItemDetail('${item._id}')">
                <div>
                    <div class="item-card-header">
                        <span class="badge ${typeBadgeClass}">${escapeHtml(item.type)}</span>
                        <span class="badge-status status-${statusSlug}">${escapeHtml(item.status)}</span>
                    </div>
                    <h3 class="item-title">${escapeHtml(item.title)}</h3>
                    <p class="item-desc">${escapeHtml(item.description)}</p>
                    <div class="item-meta-pills">
                        <span class="meta-pill">📍 ${escapeHtml(item.campus_location)}</span>
                        <span class="meta-pill">🏷️ ${escapeHtml(item.category)}</span>
                    </div>
                </div>
                <div class="item-card-footer">
                    <span class="reporter-brief">👤 ${escapeHtml(item.reporter?.name || 'Anonymous')}</span>
                    <span>${formattedDate}</span>
                </div>
            </div>
        `;
    }).join('');
}

/* ==========================================================================
   CRUD: READ - Single Item View & Detail Modal
   ========================================================================== */
window.viewItemDetail = async function(itemId) {
    try {
        const response = await fetch(`/api/items/${itemId}`);
        const data = await response.json();

        if (!data.success || !data.item) {
            showToast(data.error || 'Failed to retrieve item', 'error');
            return;
        }

        const item = data.item;
        state.activeItem = item;

        // Populate Detail Modal Fields
        document.getElementById('detail-title').textContent = item.title;
        const typeBadge = document.getElementById('detail-type-badge');
        typeBadge.textContent = item.type;
        typeBadge.className = `badge ${item.type === 'Lost' ? 'badge-lost' : 'badge-found'}`;

        const statusSlug = item.status ? item.status.replace(/\s+/g, '-') : 'Open';
        document.getElementById('detail-status-wrapper').innerHTML = `
            <span class="badge-status status-${statusSlug}">${escapeHtml(item.status)}</span>
        `;

        document.getElementById('detail-category').textContent = item.category;
        document.getElementById('detail-location').textContent = item.campus_location;
        document.getElementById('detail-spot').textContent = item.specific_spot || 'Not specified';
        document.getElementById('detail-date').textContent = item.date_reported ? new Date(item.date_reported).toLocaleString() : 'N/A';
        document.getElementById('detail-id').textContent = item._id;
        document.getElementById('detail-description').textContent = item.description;

        // Tags
        const tagsContainer = document.getElementById('detail-tags');
        if (item.tags && item.tags.length > 0) {
            tagsContainer.innerHTML = item.tags.map(t => `<span class="tag-pill">#${escapeHtml(t)}</span>`).join('');
        } else {
            tagsContainer.innerHTML = '<span style="font-size:0.8rem; color:var(--text-muted);">No search tags recorded</span>';
        }

        // Reporter
        document.getElementById('detail-reporter-name').textContent = item.reporter?.name || 'Unknown Reporter';
        document.getElementById('detail-reporter-role').textContent = item.reporter?.role || 'Campus Member';
        const email = item.reporter?.email || 'N/A';
        const phone = item.reporter?.phone ? ` • ${item.reporter.phone}` : '';
        document.getElementById('detail-reporter-contact').textContent = `${email}${phone}`;

        // Claimed state management
        const claimBox = document.getElementById('detail-claim-box');
        const claimActionBox = document.getElementById('claim-action-container');

        if (item.status === 'Claimed') {
            claimBox.style.display = 'block';
            claimActionBox.style.display = 'none';
            const claimedDateStr = item.claim_details?.claimed_date ? new Date(item.claim_details.claimed_date).toLocaleString() : 'Recorded';
            document.getElementById('detail-claim-subtext').textContent = `Claimed by ${escapeHtml(item.claim_details?.claimed_by_name || 'Verified Owner')} on ${claimedDateStr}`;
            document.getElementById('detail-claim-notes').textContent = `Verification notes: "${escapeHtml(item.claim_details?.verification_notes || 'Confirmed')}"`;
        } else {
            claimBox.style.display = 'none';
            claimActionBox.style.display = 'block';
            document.getElementById('claim-item-id').value = item._id;
            document.getElementById('form-claim-item').reset();
        }

        openModal('modal-detail');
    } catch (err) {
        console.error('Error fetching item details:', err);
        showToast('Error loading item details', 'error');
    }
};

/* ==========================================================================
   CRUD: CREATE, UPDATE, DELETE & CLAIM Form Submissions
   ========================================================================== */
function initFormSubmissions() {
    // CREATE Item
    document.getElementById('form-create-item').addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('btn-submit-create');
        submitBtn.disabled = true;

        const formData = new FormData(e.target);
        const payload = {
            title: formData.get('title'),
            description: formData.get('description'),
            type: formData.get('type'),
            category: formData.get('category'),
            campus_location: formData.get('campus_location'),
            specific_spot: formData.get('specific_spot'),
            tags: formData.get('tags'),
            date_incident: formData.get('date_incident') || null,
            reporter_name: formData.get('reporter_name'),
            reporter_email: formData.get('reporter_email'),
            reporter_phone: formData.get('reporter_phone'),
            reporter_role: formData.get('reporter_role')
        };

        try {
            const response = await fetch('/api/items', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            if (response.status === 201 && data.success) {
                showToast(data.message || 'Item created in MongoDB!', 'success');
                closeModal('modal-create');
                fetchItems();
                fetchKPIs();
                fetchAnalytics();
            } else if (response.status === 422) {
                // MongoDB Schema Validation Error
                showToast(`MongoDB Validation Error: ${data.details || data.error}`, 'error');
            } else {
                showToast(data.error || 'Failed to create item', 'error');
            }
        } catch (err) {
            console.error('Create item error:', err);
            showToast('Network error while saving to MongoDB', 'error');
        } finally {
            submitBtn.disabled = false;
        }
    });

    // CLAIM Item Quick Action
    document.getElementById('form-claim-item').addEventListener('submit', async (e) => {
        e.preventDefault();
        const itemId = document.getElementById('claim-item-id').value;
        const claimantName = document.getElementById('claim-name').value;
        const notes = document.getElementById('claim-notes').value;

        try {
            const response = await fetch(`/api/items/${itemId}/claim`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    claimant_name: claimantName,
                    verification_notes: notes
                })
            });

            const data = await response.json();
            if (data.success) {
                showToast(data.message || 'Item marked as claimed!', 'success');
                closeModal('modal-detail');
                fetchItems();
                fetchKPIs();
                fetchAnalytics();
            } else {
                showToast(data.error || 'Failed to claim item', 'error');
            }
        } catch (err) {
            console.error('Claim error:', err);
            showToast('Error recording claim', 'error');
        }
    });

    // OPEN EDIT MODAL
    document.getElementById('btn-open-edit-modal').addEventListener('click', () => {
        if (!state.activeItem) return;
        const item = state.activeItem;

        document.getElementById('edit-item-id').value = item._id;
        document.getElementById('edit-title').value = item.title;
        document.getElementById('edit-description').value = item.description;
        document.getElementById('edit-category').value = item.category;
        document.getElementById('edit-location').value = item.campus_location;
        document.getElementById('edit-spot').value = item.specific_spot || '';
        document.getElementById('edit-status').value = item.status;
        document.getElementById('edit-tags').value = (item.tags || []).join(', ');

        closeModal('modal-detail');
        openModal('modal-edit');
    });

    // SUBMIT EDIT (UPDATE)
    document.getElementById('form-edit-item').addEventListener('submit', async (e) => {
        e.preventDefault();
        const itemId = document.getElementById('edit-item-id').value;
        const payload = {
            title: document.getElementById('edit-title').value,
            description: document.getElementById('edit-description').value,
            category: document.getElementById('edit-category').value,
            campus_location: document.getElementById('edit-location').value,
            specific_spot: document.getElementById('edit-spot').value,
            status: document.getElementById('edit-status').value,
            tags: document.getElementById('edit-tags').value
        };

        try {
            const response = await fetch(`/api/items/${itemId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            if (data.success) {
                showToast('Item updated successfully in MongoDB!', 'success');
                closeModal('modal-edit');
                fetchItems();
                fetchKPIs();
                fetchAnalytics();
            } else {
                showToast(data.error || 'Failed to update item', 'error');
            }
        } catch (err) {
            console.error('Update error:', err);
            showToast('Error updating document', 'error');
        }
    });

    // DELETE ITEM
    document.getElementById('btn-delete-item').addEventListener('click', async () => {
        if (!state.activeItem) return;
        const confirmDelete = confirm(`Are you sure you want to permanently delete "${state.activeItem.title}" from MongoDB?`);
        if (!confirmDelete) return;

        try {
            const response = await fetch(`/api/items/${state.activeItem._id}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            if (data.success) {
                showToast('Item deleted permanently from MongoDB', 'info');
                closeModal('modal-detail');
                fetchItems();
                fetchKPIs();
                fetchAnalytics();
            } else {
                showToast(data.error || 'Failed to delete item', 'error');
            }
        } catch (err) {
            console.error('Delete error:', err);
            showToast('Error deleting item', 'error');
        }
    });
}

/* ==========================================================================
   KPIs Ribbon: Multi-Faceted $facet Aggregation
   ========================================================================== */
async function fetchKPIs() {
    try {
        const response = await fetch('/api/analytics/summary');
        const res = await response.json();
        if (res.success && res.data && res.data.summary) {
            const s = res.data.summary;
            document.getElementById('stat-total-items').textContent = s.total_items ?? 0;
            document.getElementById('stat-total-lost').textContent = s.total_lost ?? 0;
            document.getElementById('stat-total-found').textContent = s.total_found ?? 0;
            document.getElementById('stat-total-claimed').textContent = s.total_claimed ?? 0;
            document.getElementById('stat-recovery-rate').textContent = `${s.recovery_rate ?? 0}%`;
        }
    } catch (err) {
        console.error('KPI fetch error:', err);
    }
}

/* ==========================================================================
   MongoDB Aggregation Pipelines & Visualizations (Chart.js)
   ========================================================================== */
async function fetchAnalytics() {
    try {
        // Fetch All 4 Aggregation Endpoints in Parallel
        const [hotspotsRes, categoriesRes, turnaroundRes, summaryRes] = await Promise.all([
            fetch('/api/analytics/hotspots').then(r => r.json()),
            fetch('/api/analytics/categories').then(r => r.json()),
            fetch('/api/analytics/turnaround').then(r => r.json()),
            fetch('/api/analytics/summary').then(r => r.json())
        ]);

        const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
        const textColor = isDark ? '#f8fafc' : '#0f172a';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';

        // 1. Hotspots Chart ($group + $sort)
        if (hotspotsRes.success) {
            document.getElementById('pipeline-hotspots-code').textContent = JSON.stringify(hotspotsRes.pipeline, null, 2);
            renderHotspotsChart(hotspotsRes.data, textColor, gridColor);
        }

        // 2. Categories Claim Rate Chart ($group + $cond + $project)
        if (categoriesRes.success) {
            document.getElementById('pipeline-categories-code').textContent = JSON.stringify(categoriesRes.pipeline, null, 2);
            renderCategoriesChart(categoriesRes.data, textColor, gridColor);
        }

        // 3. Turnaround Time Chart ($match + $subtract + $avg)
        if (turnaroundRes.success) {
            document.getElementById('pipeline-turnaround-code').textContent = JSON.stringify(turnaroundRes.pipeline, null, 2);
            renderTurnaroundChart(turnaroundRes.data, textColor, gridColor);
        }

        // 4. Reporter Demographics from $facet Pipeline
        if (summaryRes.success) {
            document.getElementById('pipeline-facet-code').textContent = JSON.stringify(summaryRes.pipeline, null, 2);
            renderRolesChart(summaryRes.data.by_reporter_role, textColor);
        }

    } catch (err) {
        console.error('Analytics fetch error:', err);
    }
}

function renderHotspotsChart(data, textColor, gridColor) {
    const ctx = document.getElementById('chart-hotspots');
    if (!ctx) return;
    if (state.charts.hotspots) state.charts.hotspots.destroy();

    const labels = data.map(d => d.location);
    const lostData = data.map(d => d.lost_count);
    const foundData = data.map(d => d.found_count);
    const claimedData = data.map(d => d.claimed_count);

    state.charts.hotspots = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Lost Reported',
                    data: lostData,
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    borderRadius: 4
                },
                {
                    label: 'Found Reported',
                    data: foundData,
                    backgroundColor: 'rgba(245, 158, 11, 0.8)',
                    borderRadius: 4
                },
                {
                    label: 'Claimed',
                    data: claimedData,
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: true,
                    ticks: { color: textColor, font: { size: 10 } },
                    grid: { color: gridColor }
                },
                y: {
                    stacked: true,
                    ticks: { color: textColor, stepSize: 1 },
                    grid: { color: gridColor }
                }
            },
            plugins: {
                legend: { labels: { color: textColor } }
            }
        }
    });
}

function renderCategoriesChart(data, textColor, gridColor) {
    const ctx = document.getElementById('chart-categories');
    if (!ctx) return;
    if (state.charts.categories) state.charts.categories.destroy();

    const labels = data.map(d => d.category);
    const percentages = data.map(d => d.claim_percentage);

    state.charts.categories = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Recovery Rate (%)',
                data: percentages,
                backgroundColor: 'rgba(99, 102, 241, 0.8)',
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    max: 100,
                    ticks: { color: textColor, callback: val => `${val}%` },
                    grid: { color: gridColor }
                },
                y: {
                    ticks: { color: textColor, font: { size: 10 } },
                    grid: { display: false }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function renderTurnaroundChart(data, textColor, gridColor) {
    const ctx = document.getElementById('chart-turnaround');
    if (!ctx) return;
    if (state.charts.turnaround) state.charts.turnaround.destroy();

    const labels = data.length ? data.map(d => d.category) : ['No Claimed Items'];
    const days = data.length ? data.map(d => d.avg_days_to_claim) : [0];

    state.charts.turnaround = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Avg Turnaround (Days)',
                data: days,
                backgroundColor: 'rgba(6, 182, 212, 0.8)',
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    ticks: { color: textColor, font: { size: 10 } },
                    grid: { color: gridColor }
                },
                y: {
                    ticks: { color: textColor },
                    grid: { color: gridColor }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function renderRolesChart(rolesData, textColor) {
    const ctx = document.getElementById('chart-roles');
    if (!ctx) return;
    if (state.charts.roles) state.charts.roles.destroy();

    const labels = (rolesData || []).map(r => r.role);
    const counts = (rolesData || []).map(r => r.count);

    state.charts.roles = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: [
                    'rgba(99, 102, 241, 0.85)',
                    'rgba(16, 185, 129, 0.85)',
                    'rgba(245, 158, 11, 0.85)',
                    'rgba(239, 68, 68, 0.85)'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: textColor, font: { size: 11 } }
                }
            }
        }
    });
}

/* ==========================================================================
   Schema Inspector & Live Presentation Features
   ========================================================================== */
async function fetchSchema() {
    try {
        const response = await fetch('/api/schema');
        const data = await response.json();
        if (data.success && data.schema) {
            document.getElementById('schema-json-display').textContent = JSON.stringify(data.schema, null, 2);
        }
    } catch (err) {
        console.error('Schema fetch error:', err);
    }
}

function initPresentationButtons() {
    // 1. Seed Demo Data Button
    document.getElementById('btn-seed-data').addEventListener('click', async () => {
        const confirmSeed = confirm('Re-seed MongoDB with realistic campus sample data? This will reset demo items.');
        if (!confirmSeed) return;

        try {
            const response = await fetch('/api/seed', { method: 'POST' });
            const data = await response.json();
            if (data.success) {
                showToast(data.message, 'success');
                fetchKPIs();
                fetchItems();
                fetchAnalytics();
            } else {
                showToast(data.error || 'Seeding failed', 'error');
            }
        } catch (err) {
            showToast('Error executing seed script', 'error');
        }
    });

    // 2. Live Schema Validation Test Button (For Class Presentation)
    document.getElementById('btn-test-validation').addEventListener('click', async () => {
        const resultBox = document.getElementById('validation-test-result');
        resultBox.style.display = 'block';
        resultBox.textContent = 'Submitting invalid document to MongoDB to test $jsonSchema enforcement...';

        try {
            const response = await fetch('/api/test-validation', { method: 'POST' });
            const data = await response.json();

            if (data.validation_caught) {
                resultBox.style.borderColor = 'rgba(239, 68, 68, 0.5)';
                resultBox.style.color = '#fca5a5';
                resultBox.textContent = `[SUCCESSFUL TEST] MongoDB Database Engine Rejected Document!\n\n` +
                    `Validation Status: Caught by MongoDB Engine\n` +
                    `Message: ${data.message}\n\n` +
                    `MongoDB Rejection Details:\n${data.rejection_details}`;
                showToast('MongoDB successfully rejected invalid document!', 'success');
            } else {
                resultBox.textContent = data.message || 'Unexpected response';
            }
        } catch (err) {
            resultBox.textContent = `Error connecting to test endpoint: ${err.message}`;
        }
    });
}

/* ==========================================================================
   Utilities: Toast Notifications & Sanitization
   ========================================================================== */

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '❌';

    toast.innerHTML = `
        <span>${icon}</span>
        <div>${escapeHtml(message)}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
