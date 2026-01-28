/**
 * Contractor Portal - Front-end Application
 * 
 * Connects to the local API proxy for Dataverse operations.
 * All API calls go through /api/* endpoints.
 */

// =============================================================================
// STATE
// =============================================================================

const state = {
    contractor: null,
    bookings: [],
    selectedBookingId: null,
    currentWorkOrder: null,
    currentView: 'all',
    isLoading: false
};

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    // Setup event listeners
    setupEventListeners();
    
    // Load contractor info
    await loadContractor();
    
    // Load bookings
    await loadBookings('all');
}

function setupEventListeners() {
    // Filter tabs
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.addEventListener('click', () => handleFilterChange(tab.dataset.view));
    });
    
    // Save buttons
    document.getElementById('save-status-btn').addEventListener('click', handleSaveStatus);
    document.getElementById('save-summary-btn').addEventListener('click', handleSaveSummary);
    document.getElementById('save-instructions-btn').addEventListener('click', handleSaveInstructions);
    
    // Photo upload
    setupPhotoUpload();
}

// =============================================================================
// API CALLS
// =============================================================================

async function api(endpoint, options = {}) {
    const url = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                ...options.headers,
                ...(options.body && !(options.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {})
            },
            body: options.body && !(options.body instanceof FormData) ? JSON.stringify(options.body) : options.body
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `API error: ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
}

// =============================================================================
// CONTRACTOR
// =============================================================================

async function loadContractor() {
    try {
        state.contractor = await api('/api/contractor');
        document.getElementById('contractor-name').textContent = state.contractor.name;
    } catch (error) {
        document.getElementById('contractor-name').textContent = 'Error loading contractor';
        showToast('Failed to load contractor info', 'error');
    }
}

// =============================================================================
// BOOKINGS
// =============================================================================

async function loadBookings(view = 'all') {
    state.currentView = view;
    const bookingsList = document.getElementById('bookings-list');
    
    // Show loading state
    bookingsList.innerHTML = `
        <div class="loading-state">
            <div class="spinner"></div>
            <p>Loading bookings...</p>
        </div>
    `;
    
    try {
        const data = await api(`/api/bookings?view=${view}`);
        state.bookings = data.bookings;
        renderBookings();
    } catch (error) {
        bookingsList.innerHTML = `
            <div class="error-state">
                <h3>Error loading bookings</h3>
                <p>${error.message}</p>
                <button class="btn btn-primary" onclick="loadBookings('${view}')">Retry</button>
            </div>
        `;
    }
}

function renderBookings() {
    const bookingsList = document.getElementById('bookings-list');
    
    if (state.bookings.length === 0) {
        bookingsList.innerHTML = `
            <div class="no-bookings">
                <div class="no-bookings-icon">📅</div>
                <h3>No bookings found</h3>
                <p>No ${state.currentView === 'all' ? '' : state.currentView} bookings to display</p>
            </div>
        `;
        return;
    }
    
    bookingsList.innerHTML = state.bookings.map(booking => {
        const startDate = new Date(booking.startTime);
        const endDate = new Date(booking.endTime);
        const isSelected = booking.id === state.selectedBookingId;
        
        return `
            <div class="booking-card ${isSelected ? 'selected' : ''}" 
                 data-booking-id="${booking.id}"
                 data-workorder-id="${booking.workOrder?.id || ''}"
                 onclick="handleBookingClick('${booking.id}', '${booking.workOrder?.id || ''}')">
                <div class="booking-header">
                    <div class="booking-datetime">
                        <span class="booking-date">${formatDate(startDate)}</span>
                        <span class="booking-time">${formatTime(startDate)} - ${formatTime(endDate)}</span>
                    </div>
                    <span class="booking-status-badge ${getStatusClass(booking.bookingStatus)}">
                        ${booking.bookingStatus}
                    </span>
                </div>
                ${booking.workOrder ? `
                    <div class="booking-wo">
                        <div class="booking-wo-number">${booking.workOrder.name}</div>
                        <div class="booking-wo-details">
                            ${booking.serviceAccount?.name || 'No service account'}
                            ${booking.workOrder.address ? ` • ${booking.workOrder.address}` : ''}
                        </div>
                        <span class="booking-wo-status">WO: ${booking.workOrder.systemStatusName}</span>
                    </div>
                ` : `
                    <div class="booking-wo">
                        <div class="booking-wo-details">No work order linked</div>
                    </div>
                `}
            </div>
        `;
    }).join('');
}

function handleFilterChange(view) {
    // Update active tab
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.view === view);
    });
    
    loadBookings(view);
}

async function handleBookingClick(bookingId, workOrderId) {
    state.selectedBookingId = bookingId;
    
    // Update selected state in list
    document.querySelectorAll('.booking-card').forEach(card => {
        card.classList.toggle('selected', card.dataset.bookingId === bookingId);
    });
    
    if (workOrderId) {
        await loadWorkOrder(workOrderId);
    } else {
        showEmptyState();
    }
}

// =============================================================================
// WORK ORDER
// =============================================================================

async function loadWorkOrder(workOrderId) {
    const panel = document.getElementById('workorder-panel');
    const emptyState = document.getElementById('empty-state');
    const content = document.getElementById('workorder-content');
    const loading = document.getElementById('wo-loading');
    
    emptyState.style.display = 'none';
    content.style.display = 'none';
    loading.style.display = 'flex';
    
    try {
        const wo = await api(`/api/workorders/${workOrderId}`);
        state.currentWorkOrder = wo;
        renderWorkOrder(wo);
        content.style.display = 'block';
    } catch (error) {
        showToast(`Failed to load work order: ${error.message}`, 'error');
        showEmptyState();
    } finally {
        loading.style.display = 'none';
    }
}

function renderWorkOrder(wo) {
    // Header
    document.getElementById('wo-name').textContent = wo.name;
    
    const statusBadge = document.getElementById('wo-status-badge');
    statusBadge.textContent = wo.systemStatusName;
    statusBadge.className = `wo-status ${getWoStatusClass(wo.systemStatusName)}`;
    
    document.getElementById('wo-priority').textContent = wo.priority ? `Priority: ${wo.priority}` : '';
    
    // Details grid
    document.getElementById('wo-service-account').textContent = wo.serviceAccount?.name || '-';
    document.getElementById('wo-address').textContent = wo.address || '-';
    document.getElementById('wo-incident-type').textContent = wo.primaryIncidentType || '-';
    document.getElementById('wo-created').textContent = wo.createdOn ? formatDateTime(new Date(wo.createdOn)) : '-';
    
    // Incident description
    const incidentSection = document.getElementById('incident-section');
    if (wo.primaryIncidentDescription) {
        document.getElementById('wo-incident-description').textContent = wo.primaryIncidentDescription;
        incidentSection.style.display = 'block';
    } else {
        incidentSection.style.display = 'none';
    }
    
    // Instructions (read-only)
    const instructionsSection = document.getElementById('instructions-section');
    if (wo.instructions) {
        document.getElementById('wo-instructions').textContent = wo.instructions;
        instructionsSection.style.display = 'block';
    } else {
        instructionsSection.style.display = 'none';
    }
    
    // Related bookings
    const bookingsContainer = document.getElementById('wo-bookings');
    if (wo.bookings && wo.bookings.length > 0) {
        bookingsContainer.innerHTML = wo.bookings.map(b => `
            <div class="related-booking">
                <div class="related-booking-info">
                    <span class="related-booking-time">${formatDateTime(new Date(b.startTime))} - ${formatTime(new Date(b.endTime))}</span>
                    <span class="related-booking-resource">${b.resource}</span>
                </div>
                <span class="related-booking-status">${b.bookingStatus}</span>
            </div>
        `).join('');
    } else {
        bookingsContainer.innerHTML = '<p style="color: var(--gray-500);">No bookings found</p>';
    }
    
    // System Status dropdown
    const statusSelect = document.getElementById('wo-system-status');
    statusSelect.innerHTML = wo.systemStatusOptions.map(opt => `
        <option value="${opt.value}" ${opt.value === wo.systemStatus ? 'selected' : ''}>
            ${opt.label}
        </option>
    `).join('');
    
    // Summary (editable)
    document.getElementById('wo-summary').value = wo.summary || '';
    
    // Account Instructions (editable)
    const accountInstructionsSection = document.getElementById('account-instructions-section');
    if (wo.serviceAccount) {
        document.getElementById('wo-account-instructions').value = wo.serviceAccount.workOrderInstructions || '';
        accountInstructionsSection.style.display = 'block';
    } else {
        accountInstructionsSection.style.display = 'none';
    }
    
    // Photos
    renderPhotos(wo.photos || []);
    
    // Clear messages
    clearMessages();
}

function renderPhotos(photos) {
    const grid = document.getElementById('photos-grid');
    
    if (photos.length === 0) {
        grid.innerHTML = '<p style="color: var(--gray-500); font-size: 0.9rem;">No photos attached yet</p>';
        return;
    }
    
    grid.innerHTML = photos.map(photo => `
        <div class="photo-item" onclick="viewPhoto('${photo.id}', '${photo.filename}')">
            <img src="/api/annotations/${photo.id}/content" alt="${photo.filename}" loading="lazy">
            <div class="photo-item-info">
                <span>${photo.filename}</span>
            </div>
        </div>
    `).join('');
}

function viewPhoto(annotationId, filename) {
    window.open(`/api/annotations/${annotationId}/content`, '_blank');
}

function showEmptyState() {
    document.getElementById('empty-state').style.display = 'flex';
    document.getElementById('workorder-content').style.display = 'none';
    state.currentWorkOrder = null;
}

// =============================================================================
// SAVE HANDLERS
// =============================================================================

async function handleSaveStatus() {
    if (!state.currentWorkOrder) return;
    
    const btn = document.getElementById('save-status-btn');
    const select = document.getElementById('wo-system-status');
    const messageEl = document.getElementById('status-message');
    const newStatus = parseInt(select.value);
    
    setButtonLoading(btn, true);
    clearMessages();
    
    try {
        const result = await api(`/api/workorders/${state.currentWorkOrder.id}/status`, {
            method: 'PATCH',
            body: { systemStatus: newStatus }
        });
        
        messageEl.textContent = result.message;
        messageEl.className = 'save-message success';
        
        // Update UI
        const statusBadge = document.getElementById('wo-status-badge');
        statusBadge.textContent = result.newStatus.label;
        statusBadge.className = `wo-status ${getWoStatusClass(result.newStatus.label)}`;
        
        // Refresh bookings list to show updated status
        await loadBookings(state.currentView);
        
        showToast('System status updated', 'success');
    } catch (error) {
        messageEl.textContent = error.message;
        messageEl.className = 'save-message error';
        showToast('Failed to update status', 'error');
    } finally {
        setButtonLoading(btn, false);
    }
}

async function handleSaveSummary() {
    if (!state.currentWorkOrder) return;
    
    const btn = document.getElementById('save-summary-btn');
    const textarea = document.getElementById('wo-summary');
    const messageEl = document.getElementById('summary-message');
    const summary = textarea.value;
    
    setButtonLoading(btn, true);
    clearMessages();
    
    try {
        const result = await api(`/api/workorders/${state.currentWorkOrder.id}/summary`, {
            method: 'PATCH',
            body: { summary }
        });
        
        messageEl.textContent = result.message;
        messageEl.className = 'save-message success';
        showToast('Summary updated', 'success');
    } catch (error) {
        messageEl.textContent = error.message;
        messageEl.className = 'save-message error';
        showToast('Failed to update summary', 'error');
    } finally {
        setButtonLoading(btn, false);
    }
}

async function handleSaveInstructions() {
    if (!state.currentWorkOrder?.serviceAccount) return;
    
    const btn = document.getElementById('save-instructions-btn');
    const textarea = document.getElementById('wo-account-instructions');
    const messageEl = document.getElementById('instructions-message');
    const instructions = textarea.value;
    
    setButtonLoading(btn, true);
    clearMessages();
    
    try {
        const result = await api(`/api/accounts/${state.currentWorkOrder.serviceAccount.id}/instructions`, {
            method: 'PATCH',
            body: { instructions }
        });
        
        messageEl.textContent = result.message;
        messageEl.className = 'save-message success';
        showToast('Account instructions updated', 'success');
    } catch (error) {
        messageEl.textContent = error.message;
        messageEl.className = 'save-message error';
        showToast('Failed to update instructions', 'error');
    } finally {
        setButtonLoading(btn, false);
    }
}

// =============================================================================
// PHOTO UPLOAD
// =============================================================================

function setupPhotoUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('photo-input');
    const preview = document.getElementById('photo-preview');
    const previewImage = document.getElementById('preview-image');
    const previewFilename = document.getElementById('preview-filename');
    const uploadOptions = document.getElementById('upload-options');
    const removeBtn = document.getElementById('remove-photo-btn');
    const uploadBtn = document.getElementById('upload-photo-btn');
    
    // Click to select file
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
    
    // File input change
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFileSelect(fileInput.files[0]);
        }
    });
    
    // Remove selected file
    removeBtn.addEventListener('click', () => {
        clearPhotoSelection();
    });
    
    // Upload button
    uploadBtn.addEventListener('click', handlePhotoUpload);
}

function handleFileSelect(file) {
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!allowedTypes.includes(file.type)) {
        showToast('Please select a JPG, JPEG, or PNG file', 'error');
        return;
    }
    
    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
        showToast('File is too large. Maximum size is 10MB.', 'error');
        return;
    }
    
    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('preview-image').src = e.target.result;
        document.getElementById('preview-filename').textContent = file.name;
        document.getElementById('upload-area').style.display = 'none';
        document.getElementById('photo-preview').style.display = 'flex';
        document.getElementById('upload-options').style.display = 'flex';
    };
    reader.readAsDataURL(file);
}

function clearPhotoSelection() {
    document.getElementById('photo-input').value = '';
    document.getElementById('preview-image').src = '';
    document.getElementById('preview-filename').textContent = '';
    document.getElementById('photo-subject').value = '';
    document.getElementById('upload-area').style.display = 'block';
    document.getElementById('photo-preview').style.display = 'none';
    document.getElementById('upload-options').style.display = 'none';
    document.getElementById('upload-message').textContent = '';
}

async function handlePhotoUpload() {
    if (!state.currentWorkOrder) return;
    
    const fileInput = document.getElementById('photo-input');
    const file = fileInput.files[0];
    
    if (!file) {
        showToast('No file selected', 'error');
        return;
    }
    
    const btn = document.getElementById('upload-photo-btn');
    const messageEl = document.getElementById('upload-message');
    const subject = document.getElementById('photo-subject').value || 'Photo Upload';
    
    setButtonLoading(btn, true);
    
    try {
        const formData = new FormData();
        formData.append('photo', file);
        formData.append('subject', subject);
        
        const result = await api(`/api/workorders/${state.currentWorkOrder.id}/photos`, {
            method: 'POST',
            body: formData
        });
        
        messageEl.textContent = result.message;
        messageEl.className = 'save-message success';
        
        showToast('Photo uploaded successfully', 'success');
        
        // Clear selection and refresh photos
        clearPhotoSelection();
        
        // Reload work order to show new photo
        await loadWorkOrder(state.currentWorkOrder.id);
    } catch (error) {
        messageEl.textContent = error.message;
        messageEl.className = 'save-message error';
        showToast('Failed to upload photo', 'error');
    } finally {
        setButtonLoading(btn, false);
    }
}

// =============================================================================
// UI HELPERS
// =============================================================================

function setButtonLoading(btn, isLoading) {
    btn.disabled = isLoading;
    btn.querySelector('.btn-text').style.display = isLoading ? 'none' : 'inline';
    btn.querySelector('.btn-loading').style.display = isLoading ? 'inline-flex' : 'none';
}

function clearMessages() {
    document.querySelectorAll('.save-message').forEach(el => {
        el.textContent = '';
        el.className = 'save-message';
    });
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    
    const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ'
    };
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// =============================================================================
// FORMATTERS
// =============================================================================

function formatDate(date) {
    return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

function formatTime(date) {
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDateTime(date) {
    return `${formatDate(date)} ${formatTime(date)}`;
}

function getStatusClass(status) {
    const normalized = status.toLowerCase().replace(/\s+/g, '-');
    return normalized;
}

function getWoStatusClass(statusName) {
    const normalized = statusName.toLowerCase().replace(/\s+/g, '-');
    return normalized;
}

// Make functions available globally for inline onclick handlers
window.handleBookingClick = handleBookingClick;
window.viewPhoto = viewPhoto;
window.loadBookings = loadBookings;
