import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach cyber officer JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('tracelink_officer_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor to handle session expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token and redirect to login gateway if unauthorized
      localStorage.removeItem('tracelink_officer_token');
      localStorage.removeItem('tracelink_officer_profile');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login?session_expired=1';
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (credentials) => api.post('/auth/login', credentials),
  getMe: () => api.get('/auth/me'),
  getStations: () => api.get('/auth/stations'),
};

export const transactionsApi = {
  getTransactions: (params) => api.get('/transactions', { params }),
  getStats: () => api.get('/transactions/stats'),
};

export const casesApi = {
  getCases: () => api.get('/cases'),
  getCaseDetail: (id) => api.get(`/cases/${id}`),
  createCase: (data) => api.post('/cases', data),
};

export const tracesApi = {
  getGraph: (traceId) => api.get(`/traces/${traceId}/graph`),
  traceByPerson: (personId) => api.get(`/traces/by-person/${personId}`),
  initiateTrace: (data) => api.post('/traces', data),
};

export const requestsApi = {
  getNotices: () => api.get('/requests'),
  getNoticeDetail: (id) => api.get(`/requests/${id}`),
  createDraft: (data) => api.post('/requests/draft', data),
  signNotice: (id, signData) => api.post(`/requests/${id}/sign`, signData),
};

export const auditApi = {
  getAuditLogs: (params) => api.get('/audit', { params }),
  verifyChain: () => api.get('/audit/verify-chain'),
};

export const sanctionsApi = {
  checkAddress: (address) => api.get(`/sanctions/check/${address}`),
  batchCheck: (addresses) => api.post('/sanctions/batch-check', addresses),
  getStats: () => api.get('/sanctions/stats'),
};

export const reportsApi = {
  downloadCasePdfUrl: (caseId) => `/api/reports/case/${caseId}/pdf`,
  getCasePdfBlob: (caseId) => api.get(`/reports/case/${caseId}/pdf`, { responseType: 'blob' }),
};

export const systemApi = {
  getHealth: () => api.get('/health'),
  getWorkerHealth: () => api.get('/health/workers'),
  getSystemStats: () => api.get('/health/system'),
};

export default api;
