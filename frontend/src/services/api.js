import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (window.location.pathname !== '/login' && !window.location.pathname.startsWith('/submit/')) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email, password) => api.post('/api/auth/login', { email, password }),
  register: (data) => api.post('/api/auth/register', data),
  getMe: () => api.get('/api/auth/me'),
};

export const controlsAPI = {
  list: (params) => api.get('/api/controls', { params }),
  create: (data) => api.post('/api/controls', data),
  get: (id) => api.get(`/api/controls/${id}`),
  update: (id, data) => api.put(`/api/controls/${id}`, data),
};

export const scopesAPI = {
  list: (params) => api.get('/api/scopes', { params }),
  create: (data) => api.post('/api/scopes', data),
  get: (id) => api.get(`/api/scopes/${id}`),
  update: (id, data) => api.put(`/api/scopes/${id}`, data),
};

export const assignmentsAPI = {
  list: (params) => api.get('/api/control-assignments', { params }),
  create: (data) => api.post('/api/control-assignments', data),
  get: (id) => api.get(`/api/control-assignments/${id}`),
  update: (id, data) => api.put(`/api/control-assignments/${id}`, data),
};

export const reviewsAPI = {
  list: (params) => api.get('/api/reviews', { params }),
  create: (data) => api.post('/api/reviews', data),
  get: (id) => api.get(`/api/reviews/${id}`),
  update: (id, data) => api.put(`/api/reviews/${id}`, data),
};

export const requestsAPI = {
  list: (params) => api.get('/api/evidence-requests', { params }),
  create: (data) => api.post('/api/evidence-requests', data),
  get: (id) => api.get(`/api/evidence-requests/${id}`),
  update: (id, data) => api.put(`/api/evidence-requests/${id}`, data),
  remind: (id) => api.post(`/api/evidence-requests/${id}/remind`),
  escalate: (id) => api.post(`/api/evidence-requests/${id}/escalate`),
  markComplete: (id) => api.post(`/api/evidence-requests/${id}/mark-complete`),
  getByToken: (token) => api.get(`/api/evidence-requests/token/${token}`),
};

export const evidenceAPI = {
  upload: (formData) => api.post('/api/evidence/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  get: (id) => api.get(`/api/evidence/${id}`),
  process: (id) => api.post(`/api/evidence/${id}/process`),
  revalidate: (id) => api.post(`/api/evidence/${id}/revalidate`),
};

export const communicationsAPI = {
  getByRequest: (requestId) => api.get(`/api/evidence-requests/${requestId}/communications`),
};

export const dashboardAPI = {
  getSummary: () => api.get('/api/dashboard/summary'),
  getOverdue: () => api.get('/api/dashboard/overdue'),
  triggerReminders: () => api.post('/api/dashboard/trigger-reminders'),
};

export const auditAPI = {
  getLogs: (params) => api.get('/api/audit-logs', { params }),
};

export default api;
