document.addEventListener('DOMContentLoaded', async () => {
    // Auth Check
    if (!ApiClient.getToken()) {
        window.location.href = '../index.html';
        return;
    }

    const logoutBtn = document.getElementById('nav-logout');
    const refreshBtn = document.getElementById('btn-refresh');
    const historyContainer = document.getElementById('history-container');
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('dashboard-error');

    let paymentHistoryCache = [];

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

            document.getElementById('user-initial').textContent = payload.sub.charAt(0).toUpperCase();

            await fetchAllData();
        } catch (err) {
            console.error("Dashboard init error:", err);
            showError("Failed to load initial data: " + (err.detail || err.message || "Unknown error"));
        }
    }

    async function fetchAllData() {
        showLoading(true);
        errorEl.style.display = 'none';

        try {
            const history = await ApiClient.request(`/payments/history`);
            paymentHistoryCache = history;
            renderPaymentHistory(history);
        } catch (err) {
            showError("Failed to fetch payment history. " + (err.detail || ""));
        } finally {
            showLoading(false);
        }
    }

    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount);
    }

    function renderPaymentHistory(history) {
        historyContainer.innerHTML = '';

        if (!history || history.length === 0) {
            historyContainer.innerHTML = '<div class="card"><p style="text-align:center; color: var(--text-muted);">No payment history found.</p></div>';
            historyContainer.style.display = 'flex';
            return;
        }

        const table = document.createElement('table');
        table.className = 'history-table';
        table.style.width = '100%';
        table.style.borderCollapse = 'collapse';

        table.innerHTML = `
            <thead>
                <tr>
                    <th style="padding: 1rem; text-align: left;">Date</th>
                    <th style="padding: 1rem; text-align: left;">Transaction ID</th>
                    <th style="padding: 1rem; text-align: left;">Provider</th>
                    <th style="padding: 1rem; text-align: left;">Amount</th>
                    <th style="padding: 1rem; text-align: left;">Status</th>
                    <th style="padding: 1rem; text-align: right;">Action</th>
                </tr>
            </thead>
            <tbody></tbody>
        `;

        const tbody = table.querySelector('tbody');

        history.forEach((payment, index) => {
            const providerName = payment.provider_name || 'Unknown Provider';
            let dStr = payment.payment_date;
            if (dStr && !dStr.endsWith('Z')) dStr += 'Z';
            const dateStr = new Date(dStr).toLocaleString();

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${dateStr}</td>
                <td style="font-family: monospace; font-size: 0.9em; color: var(--text-muted); word-break: break-all; max-width: 150px;">
                    ${payment.transaction_id || 'N/A'}
                </td>
                <td>${providerName}</td>
                <td style="font-weight: 500;">${formatCurrency(payment.amount)}</td>
                <td><span class="status-badge status-${payment.status}">${payment.status}</span></td>
                <td style="text-align: right;">
                    ${payment.status === 'SUCCESS' ?
                    `<button class="btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.875rem;" onclick='openInvoiceModal(${index})'>Receipt</button>`
                    : ''}
                </td>
            `;
            tbody.appendChild(tr);
        });

        historyContainer.appendChild(table);
        historyContainer.style.display = 'block';
    }

    // Modal Exported Logic (Needs to be global for onclick)
    window.openInvoiceModal = (index) => {
        const payment = paymentHistoryCache[index];
        if (!payment) return;

        const providerName = payment.provider_name || 'Unknown Provider';

        let dStr = payment.payment_date;
        if (dStr && !dStr.endsWith('Z')) dStr += 'Z';

        const shortHash = payment.transaction_id.substring(payment.transaction_id.length - 6);
        document.getElementById('inv-number').textContent = `INV-${shortHash}`;
        document.getElementById('inv-txn-id').textContent = payment.transaction_id;
        document.getElementById('inv-date').textContent = new Date(dStr).toLocaleString();
        document.getElementById('inv-status').textContent = payment.status;
        document.getElementById('inv-status').className = `badge ${payment.status.toLowerCase() === 'SUCCESS' ? 'paid' : payment.status.toLowerCase()}`;
        document.getElementById('inv-sender').textContent = payment.sender_name || 'User';
        document.getElementById('inv-receiver').textContent = providerName;

        document.getElementById('inv-bill-name').textContent = payment.bill_name || "Utility Bill Payment";
        document.getElementById('inv-method').textContent = payment.payment_method || 'Online';

        const penalty = payment.penalty_amount || 0;
        const totalAmount = payment.amount;
        const baseAmount = totalAmount - penalty;

        document.getElementById('inv-base-amount').textContent = formatCurrency(baseAmount);

        if (penalty > 0) {
            document.getElementById('inv-late-fee-row').style.display = 'table-row';
            document.getElementById('inv-late-fee').textContent = formatCurrency(penalty);
        } else {
            document.getElementById('inv-late-fee-row').style.display = 'none';
        }

        document.getElementById('inv-total').textContent = formatCurrency(totalAmount);

        document.getElementById('invoice-modal').classList.add('active');
    };

    window.closeInvoiceModal = () => {
        document.getElementById('invoice-modal').classList.remove('active');
    };

    window.printInvoice = () => {
        const originalTitle = document.title;
        const invNumber = document.getElementById('inv-number').textContent;
        document.title = invNumber;
        window.print();
        document.title = originalTitle;
    };

    // Event Listeners
    logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        ApiClient.clearToken();
        window.location.href = '../index.html';
    });

    refreshBtn.addEventListener('click', fetchAllData);

    // Helpers
    function showLoading(show) {
        loadingEl.style.display = show ? 'flex' : 'none';
        if (show) {
            historyContainer.style.display = 'none';
        }
    }
    function showError(msg) {
        errorEl.textContent = msg;
        errorEl.style.display = 'block';
    }

    // Boot
    initDashboard();
});
