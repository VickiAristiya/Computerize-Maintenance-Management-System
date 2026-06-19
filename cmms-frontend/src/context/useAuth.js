// src/context/useAuth.js
import { useContext } from 'react';
import { AuthContext } from './AuthContext';

// Custom Hook untuk kemudahan penggunaan
export const useAuth = () => {
    // Memberikan error yang jelas jika hook digunakan di luar provider
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};