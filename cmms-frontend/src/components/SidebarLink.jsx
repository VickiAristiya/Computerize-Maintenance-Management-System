// src/components/SidebarLink.jsx
import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function SidebarLink({ to, icon, children }) {
  const location = useLocation();
  // Cek apakah path saat ini cocok dengan link (termasuk sub-route)
  const isActive = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));

  return (
    <Link
      to={to}
      className={`
        group flex items-center gap-3 px-4 py-3.5 rounded-xl text-sm font-medium transition-all duration-200
        ${isActive
          ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20 translate-x-1'
          : 'text-slate-500 hover:bg-slate-100 hover:text-blue-600 hover:translate-x-1'
        }
      `}
    >
      {/* Icon wrapper untuk efek visual tambahan */}
      <div className={`transition-transform duration-200 ${isActive ? 'scale-110' : 'group-hover:scale-110'}`}>
        {icon}
      </div>
      
      <span className="tracking-wide">{children}</span>

      {/* Indikator aktif (opsional, titik kecil di kanan) */}
      {isActive && (
        <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white/80" />
      )}
    </Link>
  );
}