// src/pages/LandingPage.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
// PERBAIKAN: Menghapus ikon yang tidak terpakai (TrendingUp, BookOpen, Clock)
import { 
  LogIn, 
  ArrowRight, 
  ShieldCheck, 
  Warehouse, 
  ClipboardList, 
  Settings, 
  Code, 
  CheckCircle, 
  Zap, 
  Users, 
  BarChart3, 
  Award,
  Database,
  Activity
} from 'lucide-react';
import LogoImage from '../assets/logo.png';

// --- KOMPONEN KARTU FITUR ---
const FeatureCard = ({ icon, title, description, color }) => {
  return (
    <div className="group p-8 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
      <div 
        className={`w-14 h-14 rounded-xl flex items-center justify-center mb-6 transition-colors duration-300 group-hover:scale-110`}
        style={{ backgroundColor: `${color}15`, color: color }}
      >
        {icon}
      </div>
      <h3 className="text-xl font-bold text-slate-900 mb-3">{title}</h3>
      <p className="text-slate-600 text-sm leading-relaxed">{description}</p>
    </div>
  );
};

// --- KOMPONEN STATISTIK ---
const StatItem = ({ value, label }) => (
  <div className="text-center px-4 py-2">
    <p className="text-4xl font-extrabold text-white mb-1">{value}</p>
    <p className="text-sm font-medium text-blue-100 uppercase tracking-wider">{label}</p>
  </div>
);

// --- HALAMAN LANDING UTAMA ---
export default function LandingPage() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen font-sans text-slate-900 bg-slate-50 selection:bg-blue-100 selection:text-blue-900">
      
      {/* --- NAVBAR --- */}
      <header 
        className={`fixed w-full top-0 z-50 transition-all duration-300 ${
          scrolled ? 'bg-white/90 backdrop-blur-md shadow-sm py-3' : 'bg-transparent py-6'
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 flex justify-between items-center">
          {/* Logo Area */}
          <div className="flex items-center gap-3 cursor-pointer">
            <div className="bg-white p-1.5 rounded-lg shadow-sm">
                <img src={LogoImage} alt="Logo" className="w-6 h-6 object-contain" />
            </div>
            <span className={`text-xl font-bold tracking-tight ${scrolled ? 'text-slate-900' : 'text-slate-900 lg:text-white'}`}>
              Maint-Track <span className="text-blue-600">Pro</span>
            </span>
          </div>

          {/* Navigasi Kanan */}
          <div className="flex items-center gap-4">
            <Link to="/login">
              <button className={`hidden md:flex items-center gap-2 px-5 py-2.5 text-sm font-semibold rounded-full transition-all ${
                scrolled 
                  ? 'text-slate-600 hover:bg-slate-100' 
                  : 'text-white/90 hover:bg-white/10'
              }`}>
                <LogIn size={18} />
                Masuk
              </button>
            </Link>
            <Link to="/register">
              <button className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-full shadow-lg shadow-blue-600/30 transition-all transform hover:scale-105 active:scale-95">
                Daftar Gratis
                <ArrowRight size={16} />
              </button>
            </Link>
          </div>
        </div>
      </header>

      <main>
        {/* --- HERO SECTION --- */}
        <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden bg-slate-900">
          <div className="absolute inset-0">
            <div className="absolute top-0 left-0 w-full h-full bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20"></div>
            <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-blue-600 rounded-full blur-[120px] opacity-40 animate-pulse"></div>
            <div className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] bg-cyan-500 rounded-full blur-[120px] opacity-30"></div>
          </div>

          <div className="relative max-w-7xl mx-auto px-6 text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs font-bold uppercase tracking-wide mb-8 animate-fade-in-up">
              <Award size={14} />
              Solusi Manajemen Aset Terpercaya
            </div>
            
            <h1 className="text-5xl md:text-7xl font-extrabold text-white tracking-tight mb-6 leading-tight max-w-5xl mx-auto">
              Optimalkan Pemeliharaan, <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">
                Maksimalkan Produktivitas.
              </span>
            </h1>

            <p className="text-lg md:text-xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed">
              Maint-Track Pro menghubungkan manajemen aset, inventaris gudang, dan jadwal pemeliharaan dalam satu platform intuitif. Hilangkan downtime tak terduga hari ini.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
              <Link to="/register" className="w-full sm:w-auto">
                <button className="w-full sm:w-auto px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white text-lg font-bold rounded-xl shadow-xl shadow-blue-900/50 transition-all transform hover:-translate-y-1">
                  Mulai Sekarang
                </button>
              </Link>
              <Link to="/login" className="w-full sm:w-auto">
                <button className="w-full sm:w-auto px-8 py-4 bg-slate-800 hover:bg-slate-700 text-white text-lg font-semibold rounded-xl border border-slate-700 transition-all">
                  Lihat Demo
                </button>
              </Link>
            </div>

            {/* Stats Bar */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 border-t border-slate-800 pt-12 max-w-4xl mx-auto">
              <StatItem value="99%" label="Uptime Mesin" />
              <StatItem value="40%" label="Efisiensi Biaya" />
              <StatItem value="0" label="Human Error" />
              <StatItem value="24/7" label="Monitoring" />
            </div>
          </div>
        </section>

        {/* --- FEATURES GRID --- */}
        <section className="py-24 bg-white relative">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-20">
              <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">Fitur Lengkap untuk Industri Modern</h2>
              <p className="text-slate-600 max-w-2xl mx-auto">
                Kami merancang setiap modul untuk menjawab tantangan nyata di lantai produksi. Dari pelacakan aset hingga kepatuhan regulasi.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              <FeatureCard 
                icon={<ClipboardList size={28} />}
                title="Work Order Management"
                description="Siklus lengkap WO: Buat, Tugaskan, Lacak, dan Selesaikan. Mendukung tipe Corrective dan Preventive dengan status real-time."
                color="#2563EB" // Blue
              />
              <FeatureCard 
                icon={<Warehouse size={28} />}
                title="Integrasi Gudang Cerdas"
                description="Stok komponen berkurang otomatis saat WO selesai. Hubungkan komponen spesifik ke mesin tertentu (BOM) untuk akurasi 100%."
                color="#059669" // Green
              />
              <FeatureCard 
                icon={<Activity size={28} />}
                title="Penjadwalan Otomatis"
                description="Jangan pernah lewatkan jadwal servis. Buat jadwal berulang berdasarkan waktu dan dapatkan notifikasi sebelum jatuh tempo."
                color="#D97706" // Amber
              />
              <FeatureCard 
                icon={<BarChart3 size={28} />}
                title="Analitik & Laporan"
                description="Dashboard visual yang memukau. Ekspor laporan kinerja aset ke PDF dan CSV untuk rapat manajemen."
                color="#7C3AED" // Violet
              />
              <FeatureCard 
                icon={<ShieldCheck size={28} />}
                title="Kalibrasi & Regulasi"
                description="Pastikan aset memenuhi standar ISO dan regulasi industri. Catat dan pantau status kalibrasi dengan mudah."
                color="#DC2626" // Red
              />
              <FeatureCard 
                icon={<Users size={28} />}
                title="Role-Based Access"
                description="Keamanan tingkat tinggi dengan pembagian peran yang jelas: Admin (Full), Manager (Pengawas), dan Technician (Eksekutor)."
                color="#0891B2" // Cyan
              />
            </div>
          </div>
        </section>

        {/* --- VALUE PROPOSITION --- */}
        <section className="py-24 bg-slate-50 border-y border-slate-200">
          <div className="max-w-6xl mx-auto px-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
              
              {/* Left: Text */}
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-xs font-bold uppercase mb-6">
                  <Zap size={14} /> Efisiensi Tinggi
                </div>
                <h2 className="text-4xl font-bold text-slate-900 mb-6">
                  Ubah Pemeliharaan Reaktif Menjadi Strategis
                </h2>
                <p className="text-lg text-slate-600 mb-8 leading-relaxed">
                  Seringkali mesin rusak di saat yang paling tidak tepat, dan suku cadang ternyata kosong di gudang. Maint-Track Pro menghilangkan ketidakpastian ini.
                </p>
                
                <ul className="space-y-4">
                  {[
                    "Cegah kerusakan fatal dengan jadwal preventif.",
                    "Lacak riwayat perbaikan setiap mesin secara detail.",
                    "Kontrol inventaris suku cadang agar tidak pernah kehabisan.",
                    "Tingkatkan akuntabilitas tim dengan log aktivitas."
                  ].map((item, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <CheckCircle className="text-green-500 flex-shrink-0 mt-0.5" size={20} />
                      <span className="text-slate-700">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Right: Visual/Card */}
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-2xl transform rotate-3 opacity-20 blur-lg"></div>
                <div className="relative bg-white p-8 rounded-2xl shadow-2xl border border-slate-100">
                  <div className="flex items-center gap-4 mb-8 border-b border-slate-100 pb-6">
                    <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                      <Database className="text-blue-600" size={24} />
                    </div>
                    <div>
                      <h4 className="text-lg font-bold text-slate-900">Pusat Data Aset</h4>
                      <p className="text-sm text-slate-500">Status Terkini: Semua Sistem Normal</p>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    {/* Mock Item */}
                    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-3">
                            <div className="w-2 h-2 rounded-full bg-green-500"></div>
                            <span className="text-sm font-medium text-slate-700">Hydraulic Pump A1</span>
                        </div>
                        <span className="text-xs font-semibold text-green-600 bg-green-100 px-2 py-1 rounded">Running</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-3">
                            <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
                            <span className="text-sm font-medium text-slate-700">Conveyor Belt M2</span>
                        </div>
                        <span className="text-xs font-semibold text-yellow-600 bg-yellow-100 px-2 py-1 rounded">Maintenance</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-3">
                            <div className="w-2 h-2 rounded-full bg-red-500"></div>
                            <span className="text-sm font-medium text-slate-700">Motor Sensor X</span>
                        </div>
                        <span className="text-xs font-semibold text-red-600 bg-red-100 px-2 py-1 rounded">Stok Habis</span>
                    </div>
                  </div>

                  <div className="mt-8 pt-6 border-t border-slate-100 text-center">
                    <p className="text-sm text-slate-500">Data diperbarui secara real-time</p>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </section>

        {/* --- TECH STACK --- */}
        <section className="py-20 bg-white">
          <div className="max-w-4xl mx-auto px-6 text-center">
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-8">Didukung Oleh Teknologi Modern</h3>
            <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16 grayscale opacity-70 hover:grayscale-0 hover:opacity-100 transition-all duration-500">
                <div className="flex items-center gap-2">
                    <Code size={32} className="text-blue-500" />
                    <span className="text-xl font-bold text-slate-700">React JS</span>
                </div>
                <div className="flex items-center gap-2">
                    <Settings size={32} className="text-yellow-500" />
                    <span className="text-xl font-bold text-slate-700">Python Flask</span>
                </div>
                <div className="flex items-center gap-2">
                    <Database size={32} className="text-green-500" />
                    <span className="text-xl font-bold text-slate-700">MongoDB</span>
                </div>
            </div>
          </div>
        </section>

        {/* --- CTA FOOTER --- */}
        <section className="py-24 bg-blue-600 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-full bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10"></div>
          <div className="relative max-w-4xl mx-auto px-6 text-center text-white">
            <h2 className="text-4xl md:text-5xl font-extrabold mb-6">Siap Mentransformasi Pabrik Anda?</h2>
            <p className="text-blue-100 text-xl mb-10 max-w-2xl mx-auto">
              Bergabunglah sekarang. Buat akun Admin pertama Anda dan rasakan kemudahan manajemen aset yang sesungguhnya.
            </p>
            <Link to="/register">
              <button className="px-10 py-4 bg-white text-blue-600 text-lg font-bold rounded-full shadow-2xl hover:bg-blue-50 transition-transform hover:-translate-y-1">
                Buat Akun Admin Gratis
              </button>
            </Link>
            <p className="mt-6 text-sm text-blue-200 opacity-80">
              Tidak perlu kartu kredit • Setup dalam 5 menit
            </p>
          </div>
        </section>
      </main>

      {/* --- FOOTER --- */}
      <footer className="bg-slate-900 text-slate-400 py-12 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center">
          <div className="flex items-center gap-2 mb-4 md:mb-0">
             <div className="bg-slate-800 p-1 rounded">
                <img src={LogoImage} alt="Logo" className="w-6 h-6 object-contain filter grayscale invert" />
             </div>
             <span className="text-lg font-bold text-slate-200">Maint-Track Pro</span>
          </div>
          

        </div>
      </footer>

    </div>
  );
}