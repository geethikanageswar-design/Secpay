document.addEventListener('DOMContentLoaded', async () => {
    // Auth Check
    if (!ApiClient.getToken()) {
        window.location.href = '../index.html';
        return;
    }

    const logoutBtn = document.getElementById('nav-logout');
    const totalOutstandingEl = document.getElementById('total-outstanding');
    const totalPendingEl = document.getElementById('total-pending');
    const totalOverdueEl = document.getElementById('total-overdue');
    const totalPaidEl = document.getElementById('total-paid');
    const totalFailedEl = document.getElementById('total-failed');

    let currentUserId = null;

    // Initialization
    async function initDashboard() {
        try {
            const token = ApiClient.getToken();
            let base64Url = token.split('.')[1];
            let base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            while (base64.length % 4) {
                base64 += '=';
            }
            const payload = JSON.parse(atob(base64));
            currentUserId = payload.user_id;

            document.getElementById('welcome-msg').textContent = `Welcome, ${payload.sub.split('@')[0]}`;
            document.getElementById('user-initial').textContent = payload.sub.charAt(0).toUpperCase();

            await fetchAllData();
        } catch (err) {
            console.error("Dashboard init error:", err);
        }
    }

    async function fetchAllData() {
        try {
            const dashboardData = await ApiClient.request(`/dashboard/${currentUserId}`);
            updateSummaryUI(dashboardData);
        } catch (err) {
            console.error("Failed to fetch dashboard data.", err);
        }
    }

    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount);
    }

    function updateSummaryUI(dash) {
        if (totalOutstandingEl) totalOutstandingEl.textContent = formatCurrency(dash.total_outstanding);
        if (totalPendingEl) totalPendingEl.textContent = dash.pending_count || dash.bills_pending;
        if (totalOverdueEl) totalOverdueEl.textContent = dash.overdue_count || dash.bills_overdue;

        if (totalPaidEl) totalPaidEl.textContent = dash.paid_count || dash.bills_paid || 0;
        if (totalFailedEl) totalFailedEl.textContent = dash.failed_count || dash.payments_failed || 0;

        if (dash.total_outstanding > 0) {
            if (totalOutstandingEl) totalOutstandingEl.style.color = 'var(--danger-color, #dc3545)';
        } else {
            if (totalOutstandingEl) totalOutstandingEl.style.color = '#28a745';
        }

        if (dash.overdue_count > 0 || dash.bills_overdue > 0) {
            if (totalOverdueEl) totalOverdueEl.style.color = 'var(--danger-color, #dc3545)';
        } else {
            if (totalOverdueEl) totalOverdueEl.style.color = 'var(--text-main)';
        }
    }

    // Event Listeners
    logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        ApiClient.clearToken();
        window.location.href = '../index.html';
    });

    // Boot
    initDashboard();
});
