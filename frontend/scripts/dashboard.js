document.addEventListener('DOMContentLoaded', async () => {
    // Auth Check
    if (!ApiClient.getToken()) {
        window.location.href = '../index.html';
        return;
    }

    const logoutBtn = document.getElementById('nav-logout');
    const refreshBtn = document.getElementById('btn-refresh');
    const billsContainer = document.getElementById('bills-container');
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('dashboard-error');

    // Modal Elements
    const modal = document.getElementById('payment-modal');
    const cancelModal = document.getElementById('btn-cancel-payment');
    const paymentForm = document.getElementById('payment-form');

    // Providers Map Cache
    let providersMap = {};
    let currentUserId = null;

    // Initialization
    async function initDashboard() {
        try {
            const token = ApiClient.getToken();
            let base64Url = token.split('.')[1];
            let base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            // Pad the base64 string
            while (base64.length % 4) {
                base64 += '=';
            }
            const payload = JSON.parse(atob(base64));
            currentUserId = payload.user_id;

            document.getElementById('welcome-msg').textContent = `Welcome, ${payload.sub.split('@')[0]}`;
            document.getElementById('user-initial').textContent = payload.sub.charAt(0).toUpperCase();

            await fetchProviders();
            await fetchAllData();
        } catch (err) {
            console.error("Dashboard init error:", err);
            showError("Failed to load initial data: " + (err.detail || err.message || "Unknown error"));
            // Do NOT redirect or clear token here so the user can see the dashboard
        }
    }

    async function fetchProviders() {
        // Assume providers route might need admin? Wait, prompt says: "Provider Routes POST, GET, PATCH - Only ADMIN allowed". 
        // If GET /providers is ADMIN only, the standard USER dashboard can't fetch it!
        // To fix this without breaking requirements: let's try fetching, if it fails, just use provider ID.
        try {
            const providers = await ApiClient.request('/providers/');
            providers.forEach(p => {
                providersMap[p.id] = p.name;
            });
        } catch (e) {
            console.warn("Could not fetch providers, likely normal for standard Users (403).");
            // Do NOT throw error since it's expected for non-admins to fail this fetch.
        }
    }

    async function fetchAllData() {
        showLoading(true);
        errorEl.style.display = 'none';

        try {
            // Because GET /dashboard updates bill statuses (pending -> overdue)
            // Call dashboard first, then fetch bills or vice-versa
            const dash = await ApiClient.request(`/dashboard/${currentUserId}`);
            updateSummaryUI(dash);

            const bills = await ApiClient.request(`/bills/user/${currentUserId}`);
            renderBills(bills);
        } catch (err) {
            showError("Failed to fetch dashboard data. " + (err.detail || ""));
        } finally {
            showLoading(false);
        }
    }

    // Formatter
    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount);
    };

    function updateSummaryUI(dash) {
        document.getElementById('total-outstanding').textContent = formatCurrency(dash.total_outstanding);
        document.getElementById('total-pending').textContent = dash.pending_count;
        document.getElementById('total-overdue').textContent = dash.overdue_count;
    }

    // Modal & Payment Logic
    window.openPaymentModal = (billId, providerName, amount, status) => {
        document.getElementById('modal-bill-id').value = billId;
        document.getElementById('modal-provider-name').textContent = providerName;

        let displayAmount = amount;
        const penaltyNotice = document.getElementById('modal-penalty-notice');
        if (status === 'OVERDUE') {
            displayAmount = amount + (amount * 0.02);
            if (penaltyNotice) penaltyNotice.style.display = 'block';
        } else {
            if (penaltyNotice) penaltyNotice.style.display = 'none';
        }

        document.getElementById('modal-amount').textContent = formatCurrency(displayAmount);
        document.getElementById('payment-error').textContent = '';

        document.getElementById('payment-form').reset();
        modal.classList.add('active');
    };

    const closePaymentModal = () => {
        modal.classList.remove('active');
        document.getElementById('payment-form').reset();
    };

    paymentForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const btn = document.getElementById('btn-confirm-payment');
        const errEl = document.getElementById('payment-error');
        const billId = parseInt(document.getElementById('modal-bill-id').value);

        btn.disabled = true;
        btn.textContent = "Processing...";
        errEl.textContent = '';

        try {
            // 1. Create order on backend
            const orderRes = await ApiClient.request('/payments/create-order', {
                method: 'POST',
                body: JSON.stringify({ bill_id: billId })
            });

            // 2. Initialize Razorpay checkout options
            let paymentFailed = false;
            const options = {
                "key": orderRes.razorpay_key_id,
                "amount": orderRes.amount,
                "currency": orderRes.currency,
                "name": "SecPay Utility Services",
                "description": "Bill Payment",
                "order_id": orderRes.order_id,
                "handler": async function (response) {
                    // 3. On success, verify with backend
                    try {
                        await ApiClient.request('/payments/verify', {
                            method: 'POST',
                            body: JSON.stringify({
                                razorpay_order_id: response.razorpay_order_id,
                                razorpay_payment_id: response.razorpay_payment_id,
                                razorpay_signature: response.razorpay_signature,
                                bill_id: billId
                            })
                        });

                        closePaymentModal();
                        fetchAllData(); // Refresh UI
                        fetchHistory(); // Refresh History UI
                    } catch (verifyErr) {
                        errEl.textContent = verifyErr.detail || 'Payment verification failed.';
                        fetchAllData();
                        fetchHistory();
                    } finally {
                        btn.disabled = false;
                        btn.textContent = "Pay with Razorpay";
                    }
                },
                "prefill": {
                    "name": document.getElementById('user-name') ? document.getElementById('user-name').textContent : "User",
                },
                "theme": {
                    "color": "#4f46e5"
                },
                "modal": {
                    "ondismiss": async function () {
                        if (paymentFailed) {
                            btn.disabled = false;
                            btn.textContent = "Pay with Razorpay";
                            fetchAllData();
                            fetchHistory();
                            return;
                        }
                        try {
                            await ApiClient.request('/payments/verify', {
                                method: 'POST',
                                body: JSON.stringify({
                                    razorpay_order_id: orderRes.order_id,
                                    razorpay_payment_id: "",
                                    razorpay_signature: "",
                                    bill_id: billId
                                })
                            });
                        } catch (e) {
                            console.error("Failed to record dismissal:", e);
                        }
                        btn.disabled = false;
                        btn.textContent = "Pay with Razorpay";
                        fetchAllData();
                        fetchHistory();
                    }
                }
            };

            const rzp = new Razorpay(options);

            rzp.on('payment.failed', async function (response) {
                paymentFailed = true;
                try {
                    let pid = response.error ? (response.error.metadata ? response.error.metadata.payment_id : "") : "";
                    await ApiClient.request('/payments/verify', {
                        method: 'POST',
                        body: JSON.stringify({
                            razorpay_order_id: orderRes.order_id,
                            razorpay_payment_id: pid,
                            razorpay_signature: "",
                            bill_id: billId
                        })
                    });
                } catch (e) {
                    console.error("Failed to record payment failure:", e);
                }
                errEl.textContent = response.error.description || 'Payment cancelled or failed.';
                btn.disabled = false;
                btn.textContent = "Pay with Razorpay";
                fetchAllData();
                fetchHistory();
            });

            rzp.open();

        } catch (err) {
            errEl.textContent = err.detail || 'Failed to initiate payment.';
            btn.disabled = false;
            btn.textContent = "Pay with Razorpay";
        }
    });

    // History and Invoices
    async function fetchHistory() {
        try {
            const res = await ApiClient.request('/payments/history');
            const historyObj = res.data;
            const container = document.getElementById('history-container');
            container.innerHTML = '';

            if (historyObj.length === 0) {
                container.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 2rem;">No payment history found.</td></tr>';
                return;
            }

            historyObj.forEach(h => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${new Date(h.payment_date).toLocaleDateString()}</td>
                    <td>${h.bill_name}</td>
                    <td>${h.payment_method}</td>
                    <td>${formatCurrency(h.amount)}</td>
                    <td><span class="status-badge status-${h.status}">${h.status}</span></td>
                    <td style="text-align: right;"><button class="btn-secondary" style="padding: 0.25rem 0.75rem; font-size: 0.8rem;" onclick="openInvoice('${h.transaction_id}', '${h.payment_date}', '${h.payment_method}', '${h.status}', '${h.sender_name}', '${h.receiver_name}', '${h.bill_name}', ${h.amount}, ${h.penalty_amount})">View</button></td>
                `;
                container.appendChild(tr);
            });
        } catch (e) {
            console.error("Failed to fetch history:", e);
        }
    }

    const invoiceModal = document.getElementById('invoice-modal');
    window.openInvoice = (txId, date, method, status, sender, receiver, billName, amount, penalty) => {
        document.getElementById('inv-number').textContent = `INV-${new Date(date).toISOString().slice(0, 10).replace(/-/g, '')}-${txId.substr(-4)}`;
        document.getElementById('inv-txid').textContent = txId;
        document.getElementById('inv-date').textContent = new Date(date).toLocaleDateString();
        document.getElementById('inv-method').textContent = method;
        document.getElementById('inv-status').textContent = status;

        document.getElementById('inv-sender').textContent = sender;
        document.getElementById('inv-receiver').textContent = receiver;
        document.getElementById('inv-bill-name').textContent = billName;

        const baseAmount = amount - penalty;
        document.getElementById('inv-base-amount').textContent = formatCurrency(baseAmount);

        if (penalty > 0) {
            document.getElementById('inv-penalty-row').style.display = 'table-row';
            document.getElementById('inv-penalty-amount').textContent = formatCurrency(penalty);
        } else {
            document.getElementById('inv-penalty-row').style.display = 'none';
        }

        document.getElementById('inv-total-paid').textContent = formatCurrency(amount);

        invoiceModal.classList.add('active');
    };

    document.getElementById('btn-close-invoice').addEventListener('click', () => {
        invoiceModal.classList.remove('active');
    });

    document.getElementById('btn-print-invoice').addEventListener('click', () => {
        window.print();
    });

    // Event Listeners
    logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        ApiClient.clearToken();
        window.location.href = '../index.html';
    });

    refreshBtn.addEventListener('click', () => {
        fetchAllData();
        fetchHistory();
    });
    cancelModal.addEventListener('click', closePaymentModal);

    // Helpers
    function showLoading(show) {
        loadingEl.style.display = show ? 'flex' : 'none';
        if (show) billsContainer.style.display = 'none';
    }
    function showError(msg) {
        errorEl.textContent = msg;
        errorEl.style.display = 'block';
    }

    function renderBills(bills) {
        billsContainer.innerHTML = '';
        if (bills.length === 0) {
            billsContainer.innerHTML = '<div class="card"><p style="text-align:center; color: var(--text-muted);">No bills found.</p></div>';
            billsContainer.style.display = 'flex';
            return;
        }

        bills.forEach(bill => {
            const providerName = providersMap[bill.provider_id] || `Provider #${bill.provider_id}`;
            const isUnpaid = bill.status !== 'PAID';

            const billEl = document.createElement('div');
            billEl.className = 'bill-item';
            billEl.innerHTML = `
                <div class="bill-info">
                    <h4>${providerName}</h4>
                    <p>Due: ${new Date(bill.due_date).toLocaleDateString()}</p>
                </div>
                <div class="bill-meta">
                    <span class="badge ${bill.status.toLowerCase()}">${bill.status}</span>
                    <span class="bill-amount">${formatCurrency(bill.amount)}</span>
                    ${isUnpaid ? `<button class="btn-primary" onclick="openPaymentModal(${bill.id}, '${providerName}', ${bill.amount}, '${bill.status}')">Pay</button>` : `<button class="btn-secondary" disabled>Paid</button>`}
                </div>
            `;
            billsContainer.appendChild(billEl);
        });
        billsContainer.style.display = 'flex';
    }

    // Boot
    initDashboard();
    fetchHistory();
});
