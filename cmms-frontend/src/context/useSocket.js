// src/context/useSocket.js
import { useContext } from 'react';
import { SocketContext } from './SocketContext';

// Custom Hook untuk kemudahan penggunaan
export const useSocket = () => {
    const context = useContext(SocketContext);
    if (!context) {
        throw new Error('useSocket must be used within a SocketProvider');
    }
    return context;
};
