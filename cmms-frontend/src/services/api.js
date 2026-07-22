import axios from 'axios';

// Production (VM): di-set lewat .env.production ke '/api' (relatif — frontend &
// backend satu domain lewat nginx proxy), jadi tidak perlu hardcode nama domain.
// Dev lokal: fallback ke Flask lokal karena Vite dev server & Flask beda port/origin.
export const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: BASE_URL,
});

// Otomatis tambahkan token Authorization dari localStorage di setiap request
api.interceptors.request.use((config) => {
  const storedUser = localStorage.getItem('cmms_user');
  if (storedUser) {
    const { token } = JSON.parse(storedUser);
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
