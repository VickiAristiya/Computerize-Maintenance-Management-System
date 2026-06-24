import React, { useState } from 'react';
import { KeyRound, Loader2, Eye, EyeOff } from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/useAuth.js';
import Modal from './Modal.jsx';

export default function ChangePasswordModal({ isOpen, onClose }) {
    const { user } = useAuth();
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showOld, setShowOld] = useState(false);
    const [showNew, setShowNew] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);

    const handleClose = () => {
        setOldPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setError(null);
        setSuccess(false);
        onClose();
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);

        if (newPassword !== confirmPassword) {
            setError('Password baru dan konfirmasi tidak cocok.');
            return;
        }
        if (newPassword.length < 6) {
            setError('Password baru minimal 6 karakter.');
            return;
        }

        setIsSubmitting(true);
        try {
            await api.post('/auth/change-password', {
                user_id: user.id,
                old_password: oldPassword,
                new_password: newPassword,
            });
            setSuccess(true);
        } catch (err) {
            setError(err.response?.data?.error || 'Gagal mengubah password.');
        }
        setIsSubmitting(false);
    };

    return (
        <Modal isOpen={isOpen} onClose={handleClose} title="Ganti Password">
            {success ? (
                <div className="text-center py-6">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <KeyRound size={28} className="text-green-600" />
                    </div>
                    <p className="text-lg font-bold text-slate-800 mb-1">Password Berhasil Diubah</p>
                    <p className="text-sm text-slate-500 mb-6">Gunakan password baru Anda saat login berikutnya.</p>
                    <button
                        onClick={handleClose}
                        className="px-6 py-2.5 bg-blue-600 text-white text-sm font-bold rounded-lg hover:bg-blue-700"
                    >
                        Tutup
                    </button>
                </div>
            ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm border border-red-100">
                            {error}
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Password Lama</label>
                        <div className="relative">
                            <input
                                type={showOld ? 'text' : 'password'}
                                value={oldPassword}
                                onChange={e => setOldPassword(e.target.value)}
                                required
                                placeholder="Masukkan password lama"
                                className="w-full px-3 py-2.5 pr-10 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                            />
                            <button
                                type="button"
                                onClick={() => setShowOld(!showOld)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                            >
                                {showOld ? <EyeOff size={16} /> : <Eye size={16} />}
                            </button>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Password Baru</label>
                        <div className="relative">
                            <input
                                type={showNew ? 'text' : 'password'}
                                value={newPassword}
                                onChange={e => setNewPassword(e.target.value)}
                                required
                                placeholder="Minimal 6 karakter"
                                className="w-full px-3 py-2.5 pr-10 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                            />
                            <button
                                type="button"
                                onClick={() => setShowNew(!showNew)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                            >
                                {showNew ? <EyeOff size={16} /> : <Eye size={16} />}
                            </button>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Konfirmasi Password Baru</label>
                        <input
                            type="password"
                            value={confirmPassword}
                            onChange={e => setConfirmPassword(e.target.value)}
                            required
                            placeholder="Ulangi password baru"
                            className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                        />
                    </div>

                    <div className="flex justify-end gap-3 pt-2">
                        <button
                            type="button"
                            onClick={handleClose}
                            className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50"
                        >
                            Batal
                        </button>
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="inline-flex items-center px-5 py-2 bg-blue-600 text-white text-sm font-bold rounded-lg hover:bg-blue-700 disabled:opacity-60"
                        >
                            {isSubmitting ? <Loader2 size={16} className="mr-2 animate-spin" /> : <KeyRound size={16} className="mr-2" />}
                            {isSubmitting ? 'Memproses...' : 'Simpan Password'}
                        </button>
                    </div>
                </form>
            )}
        </Modal>
    );
}
