const API_BASE_URL = 'http://localhost:8000/api';

class ApiClient {
    static getToken() {
        return localStorage.getItem('secpay_token');
    }

    static setToken(token) {
        localStorage.setItem('secpay_token', token);
    }

    static clearToken() {
        localStorage.removeItem('secpay_token');
    }

    static async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        const token = this.getToken();
        if (token && !options.noAuth) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            ...options,
            headers,
        };

        // For OAuth2 form encoding handling (Login)
        if (options.isForm) {
            delete headers['Content-Type'];
        }

        try {
            const response = await fetch(url, config);
            const contentType = response.headers.get("content-type");
            
            let data;
            if (contentType && contentType.indexOf("application/json") !== -1) {
                data = await response.json();
            } else {
                data = await response.text();
            }

            if (!response.ok) {
                // Return detailed error object
                throw { status: response.status, detail: data.detail || 'API request failed', message: data.message };
            }

            return data;
        } catch (error) {
            throw error;
        }
    }
}
