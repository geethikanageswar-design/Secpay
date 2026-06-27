document.addEventListener('DOMContentLoaded', () => {

    // Redirect if already logged in
    if (ApiClient.getToken()) {
        window.location.href = 'pages/dashboard.html';
        return;
    }

    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const toRegisterBtn = document.getElementById('to-register');
    const toLoginBtn = document.getElementById('to-login');

    const loginError = document.getElementById('login-error');
    const registerError = document.getElementById('register-error');

    // UI Switching
    toRegisterBtn.addEventListener('click', (e) => {
        e.preventDefault();
        loginForm.classList.remove('active');
        registerForm.classList.add('active');
        loginError.textContent = '';
    });

    toLoginBtn.addEventListener('click', (e) => {
        e.preventDefault();
        registerForm.classList.remove('active');
        loginForm.classList.add('active');
        registerError.textContent = '';
    });

    // Form Validators (Enable/Disable Buttons)
    const checkForm = (formId, btnId) => {
        const form = document.getElementById(formId);
        const btn = document.getElementById(btnId);
        form.addEventListener('input', () => {
            btn.disabled = !form.checkValidity();
        });
    };
    checkForm('login-form', 'btn-login');
    checkForm('register-form', 'btn-register');

    // Handle Login
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('btn-login');
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        btn.textContent = 'Signing in...';
        btn.disabled = true;
        loginError.textContent = '';

        const formData = new URLSearchParams();
        formData.append('username', email); // OAuth2 requires username field
        formData.append('password', password);

        try {
            const data = await ApiClient.request('/auth/login', {
                method: 'POST',
                body: formData,
                isForm: true,
                noAuth: true
            });

            ApiClient.setToken(data.access_token);
            window.location.href = 'pages/dashboard.html';
        } catch (err) {
            loginError.textContent = err.detail || 'Login failed. Please check credentials.';
            btn.textContent = 'Sign In';
            btn.disabled = false;
        }
    });

    // Handle Registration
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('btn-register');
        const name = document.getElementById('register-name').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;

        btn.textContent = 'Creating account...';
        btn.disabled = true;
        registerError.textContent = '';

        try {
            await ApiClient.request('/auth/register', {
                method: 'POST',
                body: JSON.stringify({ name, email, password }),
                noAuth: true
            });

            // Auto Login after registration
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const loginData = await ApiClient.request('/auth/login', {
                method: 'POST', body: formData, isForm: true, noAuth: true
            });

            ApiClient.setToken(loginData.access_token);
            window.location.href = 'pages/dashboard.html';
        } catch (err) {
            registerError.textContent = err.detail || 'Registration failed.';
            btn.textContent = 'Register';
            btn.disabled = false;
        }
    });
});
