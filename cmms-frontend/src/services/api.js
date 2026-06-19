import axios from 'axios';

export const BASE_URL = 'http://localhost:5000/api';

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
