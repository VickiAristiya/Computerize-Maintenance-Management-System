// src/context/SocketProvider.jsx
import React, { useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import { BASE_URL } from '../services/api';
import { SocketContext } from './SocketContext';

// Server Socket.IO jalan di root backend (bukan di bawah /api)
const SOCKET_URL = BASE_URL.replace(/\/api\/?$/, '');

export const SocketProvider = ({ children }) => {
    const [socket, setSocket] = useState(null);
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        const s = io(SOCKET_URL, {
            transports: ['websocket', 'polling'],
        });

        s.on('connect', () => setConnected(true));
        s.on('disconnect', () => setConnected(false));

        setSocket(s);

        return () => {
            s.disconnect();
        };
    }, []);

    const value = { socket, connected };

    return <SocketContext.Provider value={value}>{children}</SocketContext.Provider>;
};
