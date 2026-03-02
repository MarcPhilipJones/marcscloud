// Contractor Portal Application

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize navigation
    setupNavigation();
    
    // Load initial data
    loadDashboard();
    loadJobs();
    loadCalendar();
    
    // Setup event listeners
    setupEventListeners();
}

// Navigation
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            
            // Update active nav link
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // Show target section
            showSection(targetId);
        });
    });
}

function showSection(sectionId) {
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.classList.remove('active');
    });
    
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
    }
}

// Dashboard
function loadDashboard() {
    const stats = getStats();
    
    // Update stat values
    document.getElementById('active-jobs').textContent = stats.activeJobs;
    document.getElementById('completed-jobs').textContent = stats.completedThisMonth;
    document.getElementById('upcoming-jobs').textContent = stats.scheduledToday;
    document.getElementById('rating').textContent = stats.rating;
    
    // Load today's schedule
    loadTodaySchedule();
    
    // Load notifications
    loadNotifications();
}

function loadTodaySchedule() {
    const scheduleContainer = document.getElementById('today-schedule');
    const todayJobs = getTodaySchedule();
    
    if (todayJobs.length === 0) {
        scheduleContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📅</div>
                <h3>No jobs scheduled for today</h3>
                <p>Enjoy your day off!</p>
            </div>
        `;
        return;
    }
    
    scheduleContainer.innerHTML = todayJobs.map(job => `
        <div class="schedule-item" data-job-id="${job.id}">
            <span class="schedule-time">${job.scheduledTime}</span>
            <div class="schedule-info">
                <h4>${job.title}</h4>
                <p>${job.address}</p>
            </div>
        </div>
    `).join('');
    
    // Add click handlers to schedule items
    scheduleContainer.querySelectorAll('.schedule-item').forEach(item => {
        item.addEventListener('click', () => {
            const jobId = item.dataset.jobId;
            openJobModal(jobId);
        });
    });
}

function loadNotifications() {
    const notificationsContainer = document.getElementById('notifications');
    
    notificationsContainer.innerHTML = sampleNotifications.map(notification => `
        <div class="notification-item ${notification.read ? '' : 'unread'}">
            <span class="notification-icon">${notification.icon}</span>
            <div class="notification-content">
                <h4>${notification.title}</h4>
                <p>${notification.message}</p>
                <span class="notification-time">${notification.time}</span>
            </div>
        </div>
    `).join('');
}

// Jobs
function loadJobs(jobs = null) {
    const jobsList = document.getElementById('jobs-list');
    const jobsToShow = jobs || sampleJobs;
    
    if (jobsToShow.length === 0) {
        jobsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <h3>No jobs found</h3>
                <p>Try adjusting your search or filters</p>
            </div>
        `;
        return;
    }
    
    jobsList.innerHTML = jobsToShow.map(job => `
        <div class="job-card" data-job-id="${job.id}">
            <div class="job-header">
                <div>
                    <h3 class="job-title">${job.title}</h3>
                    <span class="job-id">${job.id}</span>
                </div>
                <span class="status-badge ${job.status}">${formatStatus(job.status)}</span>
            </div>
            <div class="job-details">
                <div class="job-detail">
                    <span class="job-detail-label">Customer</span>
                    <span class="job-detail-value">${job.customer}</span>
                </div>
                <div class="job-detail">
                    <span class="job-detail-label">Location</span>
                    <span class="job-detail-value">${job.address}</span>
                </div>
                <div class="job-detail">
                    <span class="job-detail-label">Scheduled</span>
                    <span class="job-detail-value">${formatDate(job.scheduledDate)} at ${job.scheduledTime}</span>
                </div>
                <div class="job-detail">
                    <span class="job-detail-label">Duration</span>
                    <span class="job-detail-value">${job.estimatedDuration}</span>
                </div>
            </div>
        </div>
    `).join('');
    
    // Add click handlers to job cards
    jobsList.querySelectorAll('.job-card').forEach(card => {
        card.addEventListener('click', () => {
            const jobId = card.dataset.jobId;
            openJobModal(jobId);
        });
    });
}

function formatStatus(status) {
    const statusMap = {
        'pending': 'Pending',
        'in-progress': 'In Progress',
        'completed': 'Completed'
    };
    return statusMap[status] || status;
}

// Calendar
function loadCalendar() {
    const calendarGrid = document.getElementById('calendar-grid');
    const today = new Date();
    const startOfWeek = new Date(today);
    startOfWeek.setDate(today.getDate() - today.getDay());
    
    // Update calendar title
    const options = { month: 'long', day: 'numeric', year: 'numeric' };
    document.getElementById('calendar-title').textContent = 
        `Week of ${startOfWeek.toLocaleDateString('en-US', options)}`;
    
    let calendarHTML = '';
    
    for (let i = 0; i < 7; i++) {
        const currentDate = new Date(startOfWeek);
        currentDate.setDate(startOfWeek.getDate() + i);
        const dateString = currentDate.toISOString().split('T')[0];
        const isToday = dateString === getTodayDate();
        const dayJobs = getJobsForDate(dateString);
        
        calendarHTML += `
            <div class="calendar-day ${isToday ? 'today' : ''}">
                <div class="calendar-day-header">${weekDays[currentDate.getDay()]}</div>
                <div class="calendar-day-number">${currentDate.getDate()}</div>
                ${dayJobs.slice(0, 3).map(job => `
                    <div class="calendar-event" title="${job.title}">${job.scheduledTime.substring(0, 5)} ${job.title}</div>
                `).join('')}
                ${dayJobs.length > 3 ? `<div class="text-muted" style="font-size: 0.75rem;">+${dayJobs.length - 3} more</div>` : ''}
            </div>
        `;
    }
    
    calendarGrid.innerHTML = calendarHTML;
}

// Modal
function openJobModal(jobId) {
    const job = getJobById(jobId);
    if (!job) return;
    
    const modal = document.getElementById('job-modal');
    const modalBody = document.getElementById('job-modal-body');
    
    modalBody.innerHTML = `
        <div class="job-detail-grid">
            <div class="job-detail-item">
                <label>Job ID</label>
                <span>${job.id}</span>
            </div>
            <div class="job-detail-item">
                <label>Status</label>
                <span class="status-badge ${job.status}">${formatStatus(job.status)}</span>
            </div>
            <div class="job-detail-item">
                <label>Customer</label>
                <span>${job.customer}</span>
            </div>
            <div class="job-detail-item">
                <label>Priority</label>
                <span class="tag ${job.priority === 'high' ? 'tag-primary' : ''}">${job.priority}</span>
            </div>
            <div class="job-detail-item">
                <label>Address</label>
                <span>${job.address}</span>
            </div>
            <div class="job-detail-item">
                <label>Scheduled</label>
                <span>${formatDate(job.scheduledDate)} at ${job.scheduledTime}</span>
            </div>
            <div class="job-detail-item">
                <label>Estimated Duration</label>
                <span>${job.estimatedDuration}</span>
            </div>
        </div>
        <div class="job-description">
            <h4>Description</h4>
            <p>${job.description}</p>
        </div>
        <div class="form-group mt-lg">
            <label>Update Status</label>
            <select id="job-status-select" class="select">
                <option value="pending" ${job.status === 'pending' ? 'selected' : ''}>Pending</option>
                <option value="in-progress" ${job.status === 'in-progress' ? 'selected' : ''}>In Progress</option>
                <option value="completed" ${job.status === 'completed' ? 'selected' : ''}>Completed</option>
            </select>
        </div>
    `;
    
    // Store current job ID for update
    modal.dataset.currentJobId = jobId;
    
    modal.classList.add('active');
}

function closeModal() {
    const modal = document.getElementById('job-modal');
    modal.classList.remove('active');
}

// Event Listeners
function setupEventListeners() {
    // Close modal
    document.getElementById('close-modal').addEventListener('click', closeModal);
    document.getElementById('cancel-modal').addEventListener('click', closeModal);
    document.querySelector('.modal-overlay').addEventListener('click', closeModal);
    
    // Update job status
    document.getElementById('update-job-status').addEventListener('click', function() {
        const modal = document.getElementById('job-modal');
        const jobId = modal.dataset.currentJobId;
        const newStatus = document.getElementById('job-status-select').value;
        
        if (updateJobStatus(jobId, newStatus)) {
            closeModal();
            loadDashboard();
            loadJobs();
            loadCalendar();
            showToast('Job status updated successfully!', 'success');
        }
    });
    
    // Job search
    document.getElementById('job-search').addEventListener('input', function() {
        const query = this.value.trim();
        const filteredJobs = query ? searchJobs(query) : sampleJobs;
        loadJobs(filteredJobs);
    });
    
    // Job status filter
    document.getElementById('job-status-filter').addEventListener('change', function() {
        const status = this.value;
        const filteredJobs = getJobsByStatus(status);
        loadJobs(filteredJobs);
    });
    
    // Calendar navigation
    document.getElementById('prev-week').addEventListener('click', function() {
        showToast('Previous week navigation coming soon!', 'info');
    });
    
    document.getElementById('next-week').addEventListener('click', function() {
        showToast('Next week navigation coming soon!', 'info');
    });
    
    // Profile form
    document.getElementById('profile-form').addEventListener('submit', function(e) {
        e.preventDefault();
        showToast('Profile updated successfully!', 'success');
    });
    
    // Logout
    document.getElementById('logout-btn').addEventListener('click', function() {
        showToast('Logout functionality coming soon!', 'info');
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

// Toast notification
function showToast(message, type = 'info') {
    // Remove existing toast
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    const toast = document.createElement('div');
    toast.className = `toast alert alert-${type}`;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 3000;
        min-width: 300px;
        animation: slideIn 0.3s ease;
    `;
    toast.innerHTML = message;
    
    document.body.appendChild(toast);
    
    // Add slide-in animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
