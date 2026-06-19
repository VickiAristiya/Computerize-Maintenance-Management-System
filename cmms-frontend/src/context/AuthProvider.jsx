// src/context/AuthProvider.jsx
import React, { useCallback, useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { AuthContext } from './AuthContext'; // Import Context dari file terpisah
// HAPUS BARIS INI: import { useAuth } from './useAuth'; 
// -------------------------------------------------------------------

// Definisikan API Login (Bisa diletakkan di file constants terpisah juga)
const API_LOGIN_URL = 'http://localhost:5000/api/auth/login';
const IDLE_TIMEOUT_MS = 15 * 60 * 1000;
const IDLE_LOGOUT_MESSAGE_KEY = 'cmms_idle_logout_message';
const ACTIVITY_EVENTS = [
    'click',
    'keydown',
    'mousedown',
    'mousemove',
    'scroll',
    'touchstart',
    'wheel',
];

// Buat Provider Component
export const AuthProvider = ({ children }) => {
    const idleTimerRef = useRef(null);

    // State akan menyimpan user info dan token
    const [user, setUser] = useState(() => {
        // Coba ambil user dari Local Storage saat inisialisasi
        const storedUser = localStorage.getItem('cmms_user');
        return storedUser ? JSON.parse(storedUser) : null;
    });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    // Efek samping untuk menyimpan state ke Local Storage dan mengatur header Axios
    useEffect(() => {
        if (user) {
            localStorage.setItem('cmms_user', JSON.stringify(user));
            // Konfigurasi Axios untuk menyertakan token di setiap permintaan
            axios.defaults.headers.common['Authorization'] = `Bearer ${user.token}`;
        } else {
            localStorage.removeItem('cmms_user');
            // Hapus token saat logout
            delete axios.defaults.headers.common['Authorization'];
        }
    }, [user]);

    // Fungsi utama untuk Login
    const login = async (email, password) => {
        setIsLoading(true);
        setError(null);
        sessionStorage.removeItem(IDLE_LOGOUT_MESSAGE_KEY);
        try {
            const response = await axios.post(API_LOGIN_URL, { email, password });
            
            const userData = {
                id: response.data.user_id,
                name: response.data.name,
                role: response.data.role, // Informasi peran/role di sini
                token: response.data.token
            };

            setUser(userData);
            return true; // Login berhasil
        } catch (err) {
            // Tangani error API dan set pesan error yang user-friendly
            const errorMessage = err.response?.data?.error || "Login gagal. Cek koneksi atau kredensial.";
            setError(errorMessage);
            return false; // Login gagal
        } finally {
            setIsLoading(false);
        }
    };

    // Fungsi untuk Logout
    const logout = useCallback((reason = 'manual') => {
        if (reason === 'idle') {
            sessionStorage.setItem(
                IDLE_LOGOUT_MESSAGE_KEY,
                'Sesi Anda otomatis logout karena tidak ada aktivitas selama 15 menit.'
            );
        } else {
            sessionStorage.removeItem(IDLE_LOGOUT_MESSAGE_KEY);
        }

        if (idleTimerRef.current) {
            window.clearTimeout(idleTimerRef.current);
            idleTimerRef.current = null;
        }
        setUser(null);
    }, []);

    useEffect(() => {
        if (!user) return undefined;

        const resetIdleTimer = () => {
            if (idleTimerRef.current) {
                window.clearTimeout(idleTimerRef.current);
            }

            idleTimerRef.current = window.setTimeout(() => {
                logout('idle');
            }, IDLE_TIMEOUT_MS);
        };

        resetIdleTimer();
        ACTIVITY_EVENTS.forEach((eventName) => {
            window.addEventListener(eventName, resetIdleTimer, { passive: true, capture: true });
        });

        return () => {
            if (idleTimerRef.current) {
                window.clearTimeout(idleTimerRef.current);
                idleTimerRef.current = null;
            }

            ACTIVITY_EVENTS.forEach((eventName) => {
                window.removeEventListener(eventName, resetIdleTimer, { capture: true });
            });
        };
    }, [logout, user]);
    
    // Fungsi bantuan untuk pengecekan peran (Role-Based Access Control)
    const checkRole = (requiredRoles) => {
        if (!user) return false;
        if (requiredRoles.includes('any')) return true; 
        
        return requiredRoles.includes(user.role);
    };

    const value = {
        user,
        isLoading,
        error,
        login,
        logout,
        checkRole
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
