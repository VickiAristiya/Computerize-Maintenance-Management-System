// src/components/Layout.jsx
import React, { useState } from 'react';
import { Outlet, Link } from 'react-router-dom';
import SidebarLink from './SidebarLink.jsx'; 
import NotificationDropdown from './NotificationDropdown.jsx'; // IMPORT KOMPONEN BARU
import DummyCompressorSimulator from '../dummy-compressor/DummyCompressorSimulator.jsx';
import {
  LayoutDashboard,
  HardDrive,
  ClipboardList,
  Menu,
  X,
  CalendarClock,
  History,
  ClipboardCheck,
  ShieldCheck,
  Users,
  LogOut,
  Warehouse,
  ClipboardCopy,
  Search,
  Activity,
} from 'lucide-react';
import { useAuth } from '../context/useAuth.js'; 
import LogoImage from '../assets/logo.png'; 

export default function Layout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const { user, logout, checkRole } = useAuth(); 

  const navItems = [
    { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard", roles: ['any'] },
    { to: "/assets", icon: HardDrive, label: "Daftar Aset", roles: ['admin', 'manager'] }, 
    { to: "/monitoring", icon: Activity, label: "Machine Monitoring", roles: ['admin', 'manager', 'technician'] },
    { to: "/work-orders", icon: ClipboardList, label: "Work Order", roles: ['any'] },
    { to: "/schedules", icon: CalendarClock, label: "Penjadwalan", roles: ['admin', 'manager'] },
    { to: "/inventory", icon: Warehouse, label: "Gudang (Inventaris)", roles: ['admin', 'manager'] },
    { to: "/templates", icon: ClipboardCopy, label: "Template Aset", roles: ['admin'] },
    { to: "/history", icon: History, label: "Riwayat Perawatan", roles: ['any'] },
    { to: "/reports", icon: ClipboardCheck, label: "Laporan", roles: ['admin', 'manager'] },
    { to: "/compliance", icon: ShieldCheck, label: "Kalibrasi & Regulasi", roles: ['admin', 'manager'] },
    { to: "/users", icon: Users, label: "Manajemen Pengguna", roles: ['admin'] },
  ];

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-900"> 
      
      {/* --- SIDEBAR DESKTOP --- */}
      <aside className="hidden md:flex md:flex-col w-72 bg-white border-r border-slate-200 h-full fixed left-0 top-0 z-30">
        <div className="h-20 flex items-center px-6 border-b border-slate-100">
            <Link to="/" className="flex items-center gap-3 group">
                <div className="bg-blue-50 p-1.5 rounded-lg group-hover:bg-blue-100 transition-colors">
                    <img src={LogoImage} alt="Maint-Track Pro" className="h-8 w-8 object-contain"/>
                </div>
                <div>
                    <h1 className="text-lg font-extrabold text-slate-800 leading-none">Maint-Track</h1>
                    <span className="text-xs font-bold text-blue-600 tracking-widest">PRO</span>
                </div>
            </Link>
        </div>

        <nav className="flex-1 overflow-y-auto p-4 space-y-1 custom-scrollbar">
            <p className="px-4 text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 mt-2">Menu Utama</p>
            {navItems.map((item) => (
                checkRole(item.roles) && (
                <SidebarLink key={item.to} to={item.to} icon={<item.icon size={20} />}>
                    {item.label}
                </SidebarLink>
                )
            ))}
        </nav>

        <div className="p-4 border-t border-slate-100">
            <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold shadow-sm">
                    {user?.name?.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-slate-700 truncate">{user?.name}</p>
                    <p className="text-xs text-slate-500 truncate capitalize">{user?.role}</p>
                </div>
                <button 
                    onClick={logout} 
                    className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    title="Logout"
                >
                    <LogOut size={18} />
                </button>
            </div>
        </div>
      </aside>


      {/* --- SIDEBAR MOBILE --- */}
      {isSidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={() => setIsSidebarOpen(false)}></div>
          <aside className="absolute top-0 left-0 w-72 h-full bg-white shadow-2xl flex flex-col">
            <div className="h-20 flex items-center justify-between px-6 border-b border-slate-100">
              <div className="flex items-center gap-2">
                  <img src={LogoImage} alt="Logo" className="h-8"/>
                  <span className="font-bold text-lg text-slate-800">Maint-Track</span>
              </div>
              <button onClick={() => setIsSidebarOpen(false)} className="text-slate-500 hover:text-slate-800">
                <X size={24} />
              </button>
            </div>
            <nav className="flex-1 overflow-y-auto p-4 space-y-1">
              {navItems.map((item) => (
                checkRole(item.roles) && (
                  <SidebarLink key={item.to} to={item.to} icon={<item.icon size={20} />}>
                    {item.label}
                  </SidebarLink>
                )
              ))}
            </nav>
            <div className="p-4 border-t">
                <button 
                    onClick={logout}
                    className="w-full flex items-center justify-center gap-2 p-3 bg-red-50 text-red-600 rounded-xl font-medium hover:bg-red-100 transition"
                >
                    <LogOut size={20} /> Logout
                </button>
            </div>
          </aside>
        </div>
      )}


      {/* --- KONTEN UTAMA --- */}
      <div className="flex-1 flex flex-col md:ml-72 h-full overflow-hidden">
        
        {/* Header */}
        <header className="h-20 flex items-center justify-between px-6 md:px-8 bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-20">
            <div className="flex items-center gap-4">
                <button 
                    onClick={() => setIsSidebarOpen(true)} 
                    className="md:hidden p-2 text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                    <Menu size={24} />
                </button>
                
                <div className="hidden md:flex items-center bg-slate-100 rounded-full px-4 py-2 w-64 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all">
                    <Search size={18} className="text-slate-400 mr-2" />
                    <input 
                        type="text" 
                        placeholder="Cari aset atau WO..." 
                        className="bg-transparent border-none outline-none text-sm text-slate-700 w-full placeholder:text-slate-400"
                    />
                </div>
            </div>

            <div className="flex items-center gap-4">
                
                {/* --- NOTIFICATION DROPDOWN (Ganti tombol statis dengan komponen ini) --- */}
                <NotificationDropdown />
                {/* ------------------------------------------------------------------- */}

                <div className="flex items-center gap-3 pl-4 border-l border-slate-200">
                    <div className="text-right hidden sm:block">
                        <p className="text-sm font-bold text-slate-800 leading-tight">{user?.name}</p>
                        <p className="text-xs text-slate-500 font-medium uppercase">{user?.role}</p>
                    </div>
                    <div className="w-10 h-10 rounded-full bg-slate-200 overflow-hidden border-2 border-white shadow-sm cursor-pointer">
                         <div className="w-full h-full bg-slate-800 flex items-center justify-center text-white font-bold">
                             {user?.name?.charAt(0)}
                         </div>
                    </div>
                </div>
            </div>
        </header>
        
        {/* Content Scroll Area */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 scroll-smooth">
          <div className="max-w-7xl mx-auto">
              <Outlet />
          </div>
        </main>

        <DummyCompressorSimulator />

      </div>
    </div>
  );
}
