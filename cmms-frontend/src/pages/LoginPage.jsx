// src/pages/LoginPage.jsx
import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/useAuth.js'; 
import { Mail, Lock, LogIn, Loader2 } from 'lucide-react';
import LogoImage from '../assets/logo.png';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const { login, isLoading, error } = useAuth();
    const navigate = useNavigate();
    const [sessionMessage, setSessionMessage] = useState(() => sessionStorage.getItem('cmms_idle_logout_message'));
    const [loginError, setLoginError] = useState(null); 

    useEffect(() => {
        sessionStorage.removeItem('cmms_idle_logout_message');
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoginError(null);
        setSessionMessage(null);

        const success = await login(email, password);
        if (success) {
            navigate('/', { replace: true });
        } else {
            setLoginError(error);
        }
    };

    return (
        <div className="min-h-screen flex bg-slate-50">
            {/* Left Side: Decorative / Branding */}
            <div className="hidden lg:flex w-1/2 bg-gradient-to-br from-blue-900 to-slate-900 relative overflow-hidden items-center justify-center">
                <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10"></div>
                <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-blue-500 rounded-full blur-3xl opacity-20 animate-pulse"></div>
                <div className="relative z-10 text-center px-12">
                    <img src={LogoImage} alt="Logo" className="w-20 h-20 mx-auto mb-6 object-cover rounded-xl" />
                    <h2 className="text-4xl font-extrabold text-white mb-4">Selamat Datang Kembali!</h2>
                    <p className="text-blue-100 text-lg">Kelola aset dan pemeliharaan pabrik Anda dengan lebih cerdas dan efisien bersama Maint-Track Pro.</p>
                </div>
            </div>

            {/* Right Side: Form */}
            <div className="w-full lg:w-1/2 flex flex-col justify-center p-8 sm:p-12 md:p-16">
                <div className="max-w-md w-full mx-auto">
                    <div className="mb-10">
                        <h1 className="text-3xl font-bold text-slate-900">Masuk ke Akun</h1>
                        <p className="text-slate-500 mt-2">Masukkan kredensial Anda untuk mengakses dashboard.</p>
                    </div>

                    {sessionMessage && (
                        <div className="mb-6 p-4 bg-amber-50 border-l-4 border-amber-500 text-amber-700 text-sm rounded-r-md animate-fade-in">
                            <p className="font-medium">Sesi Berakhir</p>
                            <p>{sessionMessage}</p>
                        </div>
                    )}

                    {loginError && (
                        <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 text-sm rounded-r-md animate-fade-in">
                            <p className="font-medium">Login Gagal</p>
                            <p>{loginError}</p>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Mail className="h-5 w-5 text-slate-400" />
                                </div>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="pl-10 block w-full border-slate-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm py-2.5 transition-colors"
                                    placeholder="nama@perusahaan.com"
                                />
                            </div>
                        </div>

                        <div>
                            <div className="flex items-center justify-between mb-1">
                                <label className="block text-sm font-medium text-slate-700">Password</label>
                                {/* (Opsional: Link Lupa Password) */}
                                {/* <a href="#" className="text-sm font-medium text-blue-600 hover:text-blue-500">Lupa password?</a> */}
                            </div>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-slate-400" />
                                </div>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    className="pl-10 block w-full border-slate-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm py-2.5 transition-colors"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-md text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:-translate-y-0.5"
                        >
                            {isLoading ? (
                                <Loader2 className="h-5 w-5 animate-spin" />
                            ) : (
                                <>
                                    <LogIn className="h-5 w-5 mr-2" />
                                    Masuk Sekarang
                                </>
                            )}
                        </button>
                    </form>

                    <p className="mt-8 text-center text-sm text-slate-600">
                        Belum punya akun?{' '}
                        <Link to="/register" className="font-semibold text-blue-600 hover:text-blue-500 hover:underline transition-all">
                            Daftar Gratis
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
