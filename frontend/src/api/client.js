/**
 * Single API client – paths match backend Section 9.
 */
import axios from 'axios';

const api = axios.create({
  // Prefer absolute backend URL so requests always reach uvicorn (CORS allows 5173).
  baseURL: import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api',
  timeout: 60000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('jobshield_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const payload = err.response?.data?.error;
    const message = payload?.message || err.message || 'Request failed';
    const error = new Error(message);
    error.code = payload?.code || 'REQUEST_ERROR';
    error.status = err.response?.status;
    error.details = payload?.details || [];
    error.raw = err.response?.data;
    return Promise.reject(error);
  }
);

export const health = () => api.get('/health').then((r) => r.data);

export const register = (body) => api.post('/auth/register', body).then((r) => r.data);
export const login = (body) => api.post('/auth/login', body).then((r) => r.data);
export const verifyEmail = (body) => api.post('/auth/verify-email', body).then((r) => r.data);
export const resendOtp = (body) => api.post('/auth/resend-otp', body).then((r) => r.data);
export const forgotPassword = (body) => api.post('/auth/forgot-password', body).then((r) => r.data);
export const resetPassword = (body) => api.post('/auth/reset-password', body).then((r) => r.data);
export const me = () => api.get('/auth/me').then((r) => r.data);

export const analyzeJob = (body) => api.post('/analyze', body).then((r) => r.data);

export const ocrAnalyze = (formData) =>
  api.post('/ocr/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);

export const analyzeUrl = (body) => api.post('/url/analyze', body).then((r) => r.data);

export const verifyCompany = (body) => api.post('/company/verify', body).then((r) => r.data);

export const createReport = (formData) =>
  api.post('/reports', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);

export const listReports = (params) => api.get('/reports', { params }).then((r) => r.data);

export const submitFeedback = (body) => api.post('/feedback', body).then((r) => r.data);

export const listHistory = (params) => api.get('/history', { params }).then((r) => r.data);
export const getHistoryItem = (id) => api.get(`/history/${id}`).then((r) => r.data);
export const deleteHistoryItem = (id) => api.delete(`/history/${id}`).then((r) => r.data);

export const getDashboard = () => api.get('/dashboard').then((r) => r.data);

export default api;
