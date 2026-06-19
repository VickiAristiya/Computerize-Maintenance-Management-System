// src/pages/RegisterPage.jsx
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { UserPlus, Mail, Lock, Loader2, User, Shield, ArrowLeft, CheckCircle } from 'lucide-react';
import LogoImage from '../assets/logo.png'; 

const API_REGISTER_URL = 'http://localhost:5000/api/auth/register';
const ROLES = ['manager', 'technician']; 

export default function RegisterPage() {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState(ROLES[1]);
    
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [regError, setRegError] = useState(null);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setRegError(null);
        setIsSubmitting(true);

        try {
            const response = await axios.post(API_REGISTER_URL, { name, email, password, role });
            alert(`Registrasi berhasil! Role Anda: ${response.data.role.toUpperCase()}. Silakan Login.`);
            navigate('/login', { replace: true });
        } catch (err) {
            setRegError(err.response?.data?.error || "Pendaftaran gagal. Cek koneksi server.");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen flex bg-slate-50">
            {/* Left Side: Form */}
            <div className="w-full lg:w-1/2 flex flex-col justify-center p-8 sm:p-12 md:p-16 bg-white lg:shadow-xl z-10">
                <div className="max-w-md w-full mx-auto">
                    <Link to="/" className="inline-flex items-center text-sm text-slate-500 hover:text-blue-600 mb-8 transition-colors">
                        <ArrowLeft size={16} className="mr-2" /> Kembali ke Beranda
                    </Link>

                    <div className="mb-8">
                        <div className="flex items-center gap-3 mb-2">
                            <img src={LogoImage} alt="Logo" className="w-8 h-8 object-contain" />
                            <span className="text-xl font-bold text-slate-900">Maint-Track Pro</span>
                        </div>
                        <h1 className="text-3xl font-bold text-slate-900">Buat Akun Baru</h1>
                        <p className="text-slate-500 mt-2">Bergabunglah untuk mulai mengelola pemeliharaan aset Anda.</p>
                    </div>

                    {regError && (
                        <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 text-sm rounded-r-md animate-fade-in">
                            <p className="font-medium">Registrasi Gagal</p>
                            <p>{regError}</p>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {/* Nama */}
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Nama Lengkap</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <User className="h-5 w-5 text-slate-400" />
                                </div>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    required
                                    className="pl-10 block w-full border-slate-300 rounded-lg shadow-sm focus:ring-green-500 focus:border-green-500 sm:text-sm py-2.5 transition-colors"
                                    placeholder="Nama Lengkap Anda"
                                />
                            </div>
                        </div>

                        {/* Email */}
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Email Bisnis</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Mail className="h-5 w-5 text-slate-400" />
                                </div>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="pl-10 block w-full border-slate-300 rounded-lg shadow-sm focus:ring-green-500 focus:border-green-500 sm:text-sm py-2.5 transition-colors"
                                    placeholder="nama@perusahaan.com"
                                />
                            </div>
                        </div>

                        {/* Password */}
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-slate-400" />
                                </div>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    className="pl-10 block w-full border-slate-300 rounded-lg shadow-sm focus:ring-green-500 focus:border-green-500 sm:text-sm py-2.5 transition-colors"
                                    placeholder="•••••••• (Min. 6 karakter)"
                                />
                            </div>
                        </div>

                        {/* Role */}
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Peran (Role)</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Shield className="h-5 w-5 text-slate-400" />
                                </div>
                                <select 
                                    value={role} 
                                    onChange={(e) => setRole(e.target.value)} 
                                    required 
                                    className="pl-10 block w-full border-slate-300 rounded-lg shadow-sm focus:ring-green-500 focus:border-green-500 sm:text-sm py-2.5 transition-colors bg-white"
                                >
                                    {ROLES.map(r => (
                                        <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-md text-sm font-bold text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:-translate-y-0.5 mt-4"
                        >
                            {isSubmitting ? (
                                <Loader2 className="h-5 w-5 animate-spin" />
                            ) : (
                                <>
                                    <UserPlus className="h-5 w-5 mr-2" />
                                    Daftar Sekarang
                                </>
                            )}
                        </button>
                    </form>

                    <p className="mt-8 text-center text-sm text-slate-600">
                        Sudah memiliki akun?{' '}
                        <Link to="/login" className="font-semibold text-blue-600 hover:text-blue-500 hover:underline transition-all">
                            Masuk di sini
                        </Link>
                    </p>
                </div>
            </div>

            {/* Right Side: Benefits / Decorative */}
            <div className="hidden lg:flex w-1/2 bg-slate-100 relative overflow-hidden items-center justify-center p-12">
                 {/* Decorative Elements */}
                 <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-green-200 rounded-full blur-[100px] opacity-50"></div>
                 <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-200 rounded-full blur-[100px] opacity-50"></div>

                 <div className="max-w-md relative z-10">
                    <h3 className="text-3xl font-bold text-slate-800 mb-8">Bergabunglah dengan ribuan profesional manufaktur.</h3>
                    
                    <ul className="space-y-6">
                        <li className="flex items-start gap-4">
                            <div className="p-2 bg-green-100 rounded-full text-green-600">
                                <CheckCircle size={20} />
                            </div>
                            <div>
                                <h4 className="font-semibold text-slate-900">Manajemen Aset Tanpa Batas</h4>
                                <p className="text-sm text-slate-600">Lacak ribuan mesin dan komponen dengan mudah.</p>
                            </div>
                        </li>
                        <li className="flex items-start gap-4">
                            <div className="p-2 bg-blue-100 rounded-full text-blue-600">
                                <CheckCircle size={20} />
                            </div>
                            <div>
                                <h4 className="font-semibold text-slate-900">Work Order Otomatis</h4>
                                <p className="text-sm text-slate-600">Hemat waktu dengan template dan penjadwalan pintar.</p>
                            </div>
                        </li>
                        <li className="flex items-start gap-4">
                            <div className="p-2 bg-purple-100 rounded-full text-purple-600">
                                <CheckCircle size={20} />
                            </div>
                            <div>
                                <h4 className="font-semibold text-slate-900">Pelaporan Lengkap</h4>
                                <p className="text-sm text-slate-600">Dapatkan wawasan mendalam untuk keputusan bisnis yang lebih baik.</p>
                            </div>
                        </li>
                    </ul>
                 </div>
            </div>
        </div>
    );
}