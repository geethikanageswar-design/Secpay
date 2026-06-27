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
            while (base64.length % 4) {
                base64 += '=';
            }
            const payload = JSON.parse(atob(base64));
            currentUserId = payload.user_id;

            document.getElementById('user-initial').textContent = payload.sub.charAt(0).toUpperCase();

            await fetchProviders();
            await fetchAllData();
        } catch (err) {
            console.error("Dashboard init error:", err);
            showError("Failed to load initial data: " + (err.detail || err.message || "Unknown error"));
        }
    }

    async function fetchProviders() {
        try {
            const providers = await ApiClient.request('/providers/');
            providers.forEach(p => {
                providersMap[p.id] = p.name;
            });
        } catch (e) {
            console.warn("Could not fetch providers, likely normal for standard Users (403).");
        }
    }

    async function fetchAllData() {
        showLoading(true);
        errorEl.style.display = 'none';

        try {
            // Because GET /dashboard updates bill statuses (pending -> overdue)
            // It's good to hit it even if we don't display the results, so bills get updated
            await ApiClient.request(`/dashboard/${currentUserId}`);
            const bills = await ApiClient.request(`/bills/user/${currentUserId}`);
            renderBills(bills);
        } catch (err) {
            showError("Failed to fetch bills data. " + (err.detail || ""));
        } finally {
            showLoading(false);
        }
    }

    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount);
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
            let dueStr = bill.due_date;
            if (dueStr && !dueStr.endsWith('Z')) dueStr += 'Z';
            billEl.innerHTML = `
                <div class="bill-info">
                    <h4>${providerName}</h4>
                    <p>Due: ${new Date(dueStr).toLocaleDateString()}</p>
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

    // Modal & Payment Logic
    window.openPaymentModal = (billId, providerName, baseAmount, status) => {
        let totalAmount = baseAmount;
        const penaltyNotice = document.getElementById('modal-penalty-notice');

        if (status === 'OVERDUE') {
            const penalty = Math.round((baseAmount * 0.02) * 100) / 100;
            totalAmount = baseAmount + penalty;
            penaltyNotice.textContent = `Includes 2% late fee: ${formatCurrency(penalty)}`;
            penaltyNotice.style.display = 'block';
        } else {
            penaltyNotice.style.display = 'none';
        }

        document.getElementById('modal-bill-id').value = billId;
        document.getElementById('modal-provider-name').textContent = providerName;
        document.getElementById('modal-amount').textContent = formatCurrency(totalAmount);
        document.getElementById('modal-amount').dataset.val = totalAmount;
        document.getElementById('payment-error').textContent = '';
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
                        fetchAllData(); // Refresh UI on Success
                    } catch (verifyErr) {
                        errEl.textContent = verifyErr.detail || 'Payment verification failed.';
                        fetchAllData(); // Refresh UI to show verification failure if recorded
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
                    "ondismiss": function () {
                        // User closed the Razorpay checkout without completing payment
                        // Do NOT call verify here to avoid premature FAILED entries
                        btn.disabled = false;
                        btn.textContent = "Pay with Razorpay";
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
            });

            rzp.open();

        } catch (err) {
            errEl.textContent = err.detail || 'Failed to initiate payment.';
            btn.disabled = false;
            btn.textContent = "Pay with Razorpay";
        }
    });

    // Event Listeners
    logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        ApiClient.clearToken();
        window.location.href = '../index.html';
    });

    refreshBtn.addEventListener('click', fetchAllData);
    cancelModal.addEventListener('click', closePaymentModal);

    // Helpers
    function showLoading(show) {
        loadingEl.style.display = show ? 'flex' : 'none';
        if (show) {
            billsContainer.style.display = 'none';
        }
    }
    function showError(msg) {
        errorEl.textContent = msg;
        errorEl.style.display = 'block';
    }

    // Boot
    initDashboard();
});
