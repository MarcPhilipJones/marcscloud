// Sample data for the Contractor Portal

const sampleJobs = [
    {
        id: "JOB-001",
        title: "Electrical Panel Upgrade",
        customer: "Sarah Johnson",
        address: "123 Oak Street, Suite 100",
        status: "in-progress",
        scheduledDate: "2026-01-28",
        scheduledTime: "09:00 AM",
        estimatedDuration: "4 hours",
        priority: "high",
        description: "Upgrade main electrical panel from 100A to 200A service. Replace old breakers and install new grounding system. Customer has requested work to be completed before noon if possible."
    },
    {
        id: "JOB-002",
        title: "Office Lighting Installation",
        customer: "TechCorp Inc.",
        address: "456 Business Park Drive",
        status: "pending",
        scheduledDate: "2026-01-28",
        scheduledTime: "02:00 PM",
        estimatedDuration: "3 hours",
        priority: "medium",
        description: "Install LED lighting fixtures in the new conference room. Replace existing fluorescent fixtures with energy-efficient alternatives. Total of 12 fixtures to be installed."
    },
    {
        id: "JOB-003",
        title: "Emergency Outlet Repair",
        customer: "Mike Davis",
        address: "789 Residential Lane",
        status: "pending",
        scheduledDate: "2026-01-28",
        scheduledTime: "05:00 PM",
        estimatedDuration: "1 hour",
        priority: "high",
        description: "Kitchen outlet not working. Customer reports sparks when plugging in appliances. Check wiring and replace outlet if necessary. May require inspection of circuit breaker."
    },
    {
        id: "JOB-004",
        title: "Smart Home Wiring",
        customer: "The Anderson Family",
        address: "321 Modern Ave",
        status: "completed",
        scheduledDate: "2026-01-27",
        scheduledTime: "10:00 AM",
        estimatedDuration: "6 hours",
        priority: "low",
        description: "Install wiring for smart home system including smart switches, doorbell camera, and thermostat. Run CAT6 cables to key locations throughout the house."
    },
    {
        id: "JOB-005",
        title: "Commercial Electrical Inspection",
        customer: "Downtown Restaurant Group",
        address: "555 Main Street",
        status: "in-progress",
        scheduledDate: "2026-01-29",
        scheduledTime: "08:00 AM",
        estimatedDuration: "5 hours",
        priority: "medium",
        description: "Annual electrical safety inspection for restaurant. Check all outlets, breakers, and commercial kitchen equipment connections. Prepare compliance report for city inspector."
    },
    {
        id: "JOB-006",
        title: "Generator Installation",
        customer: "Green Valley Medical Clinic",
        address: "888 Healthcare Blvd",
        status: "pending",
        scheduledDate: "2026-01-30",
        scheduledTime: "07:00 AM",
        estimatedDuration: "8 hours",
        priority: "high",
        description: "Install 50kW backup generator with automatic transfer switch. Coordinate with gas company for fuel line installation. Critical for maintaining power to medical equipment during outages."
    }
];

const sampleNotifications = [
    {
        id: 1,
        type: "job",
        icon: "📋",
        title: "New Job Assigned",
        message: "You've been assigned to Emergency Outlet Repair at 789 Residential Lane",
        time: "10 minutes ago",
        read: false
    },
    {
        id: 2,
        type: "schedule",
        icon: "📅",
        title: "Schedule Change",
        message: "Office Lighting Installation has been rescheduled to 2:00 PM",
        time: "1 hour ago",
        read: false
    },
    {
        id: 3,
        type: "message",
        icon: "💬",
        title: "Customer Message",
        message: "Sarah Johnson sent you a message about the panel upgrade",
        time: "2 hours ago",
        read: true
    },
    {
        id: 4,
        type: "completed",
        icon: "✅",
        title: "Job Completed",
        message: "Smart Home Wiring has been marked as completed",
        time: "Yesterday",
        read: true
    }
];

const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

// Helper function to get today's date in YYYY-MM-DD format
function getTodayDate() {
    const today = new Date();
    return today.toISOString().split('T')[0];
}

// Helper function to format date for display
function formatDate(dateString) {
    const options = { weekday: 'short', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

// Get jobs for a specific date
function getJobsForDate(date) {
    return sampleJobs.filter(job => job.scheduledDate === date);
}

// Get today's schedule
function getTodaySchedule() {
    const today = getTodayDate();
    return sampleJobs
        .filter(job => job.scheduledDate === today && job.status !== 'completed')
        .sort((a, b) => a.scheduledTime.localeCompare(b.scheduledTime));
}

// Get jobs filtered by status
function getJobsByStatus(status) {
    if (status === 'all') return sampleJobs;
    return sampleJobs.filter(job => job.status === status);
}

// Search jobs
function searchJobs(query) {
    const lowerQuery = query.toLowerCase();
    return sampleJobs.filter(job => 
        job.title.toLowerCase().includes(lowerQuery) ||
        job.customer.toLowerCase().includes(lowerQuery) ||
        job.address.toLowerCase().includes(lowerQuery) ||
        job.id.toLowerCase().includes(lowerQuery)
    );
}

// Get job by ID
function getJobById(id) {
    return sampleJobs.find(job => job.id === id);
}

// Update job status
function updateJobStatus(id, newStatus) {
    const job = sampleJobs.find(j => j.id === id);
    if (job) {
        job.status = newStatus;
        return true;
    }
    return false;
}

// Get statistics
function getStats() {
    const today = getTodayDate();
    const thisMonth = new Date().getMonth();
    
    return {
        activeJobs: sampleJobs.filter(j => j.status === 'in-progress').length,
        completedThisMonth: sampleJobs.filter(j => {
            const jobMonth = new Date(j.scheduledDate).getMonth();
            return j.status === 'completed' && jobMonth === thisMonth;
        }).length,
        scheduledToday: sampleJobs.filter(j => j.scheduledDate === today && j.status !== 'completed').length,
        rating: 4.8
    };
}
