// src/main.jsx

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { BrowserRouter } from 'react-router-dom'
// PERBAIKAN: Impor AuthProvider dari file Provider.jsx yang benar
import { AuthProvider } from './context/AuthProvider.jsx'; 

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      {/* --- WRAP APP DENGAN PROVIDER --- */}
      <AuthProvider>
        <App />
      </AuthProvider>
      {/* ---------------------------------- */}
    </BrowserRouter>
  </React.StrictMode>,
)