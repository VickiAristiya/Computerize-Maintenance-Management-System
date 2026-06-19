// src/pages/UserPage.jsx
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { FileWarning, Plus, Loader2, UserPlus, Mail, Shield, User, Trash2, Edit, Lock } from 'lucide-react';
import LoadingState from '../components/LoadingState.jsx';
import ErrorState from '../components/ErrorState.jsx';
import Modal from '../components/Modal.jsx'; 

const ROLES = ['admin', 'manager', 'technician'];

// --- Komponen Form Pengguna Baru/Edit ---
function UserForm({ onUserCreated, initialData, onUserUpdated, onClose }) {
    const isEditMode = !!initialData;

    const [name, setName] = useState(initialData?.name || '');
    const [email, setEmail] = useState(initialData?.email || '');
    const [password, setPassword] = useState(''); 
    const [role, setRole] = useState(initialData?.role || ROLES[2]); 
    
    const [error, setError] = useState(null);
    // PERBAIKAN: Hapus state 'success' karena modal langsung ditutup
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setIsSubmitting(true);

        const isPasswordRequired = !isEditMode; 
        if (isPasswordRequired && !password) {
            setError("Password wajib diisi untuk pengguna baru.");
            setIsSubmitting(false);
            return;
        }
        
        let userData = { name, email, role };
        if (password) userData.password = password; 

        try {
            let response;
            if (isEditMode) {
                // PATCH (Update Role/Name/Password)
                response = await api.patch(`/users/${initialData.id}`, userData);
                onUserUpdated(response.data); 
                onClose(); 
            } else {
                // POST (Create New User)
                response = await api.post('/users', userData);
                onUserCreated(response.data);
                onClose(); // Tutup modal setelah create
            }
        } catch (err) {
            if (err.response && err.response.data && err.response.data.error) {
                setError(err.response.data.error);
            } else {
                setError(`Gagal ${isEditMode ? 'mengupdate' : 'membuat'} pengguna. Cek koneksi server.`);
            }
            console.error(err);
        }
        setIsSubmitting(false);
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {error && <div className="p-3 bg-red-100 text-red-700 rounded-md text-sm">{error}</div>}
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Nama */}
                <div>
                    <label htmlFor="name" className="block text-sm font-medium text-slate-700 mb-1">Nama Lengkap</label>
                    <div className="relative">
                        <User size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
                        <input type="text" id="name" value={name} onChange={e => setName(e.target.value)} required className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-md focus:ring-blue-500 focus:border-blue-500" placeholder="Contoh: Budi Santoso"/>
                    </div>
                </div>
                
                {/* Email */}
                <div>
                    <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                    <div className="relative">
                        <Mail size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
                        <input type="email" id="email" value={email} onChange={e => setEmail(e.target.value)} required={!isEditMode} disabled={isEditMode} className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-md disabled:bg-slate-100 focus:ring-blue-500 focus:border-blue-500" placeholder="budi@cmms.com"/>
                    </div>
                </div>

                {/* Role */}
                <div>
                    <label htmlFor="role" className="block text-sm font-medium text-slate-700 mb-1">Role/Peran</label>
                    <div className="relative">
                        <Shield size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
                        <select id="role" value={role} onChange={e => setRole(e.target.value)} required className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-md focus:ring-blue-500 focus:border-blue-500">
                            {ROLES.map(r => (
                                <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* Password */}
                <div>
                    <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-1">
                        Password {isEditMode ? '(Opsional)' : '*'}
                    </label>
                    <div className="relative">
                        <Lock size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
                        <input type="password" id="password" value={password} onChange={e => setPassword(e.target.value)} required={!isEditMode} className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-md focus:ring-blue-500 focus:border-blue-500" placeholder={isEditMode ? 'Biarkan kosong' : 'Minimal 6 karakter'}/>
                    </div>
                </div>
            </div>

            <div className="text-right pt-4 flex justify-end gap-3">
                <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors">Batal</button>
                <button type="submit" disabled={isSubmitting} className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 transition-all transform hover:-translate-y-0.5">
                    {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : (isEditMode ? <Edit className="mr-2 h-4 w-4"/> : <Plus className="mr-2 h-4 w-4" />)}
                    {isSubmitting ? 'Menyimpan...' : isEditMode ? 'Simpan Perubahan' : 'Tambah Pengguna'}
                </button>
            </div>
        </form>
    );
}

// --- Halaman Utama UserPage ---
export default function UserPage() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // State untuk Modal Create/Edit
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingUser, setEditingUser] = useState(null);

    useEffect(() => {
        const fetchUsers = async () => {
            setLoading(true);
            setError(null);
            try {
                const response = await api.get('/users');
                setUsers(response.data);
            } catch (err) {
                if (err.request) {
                    setError("Gagal memuat data pengguna. Pastikan server Flask berjalan.");
                } else {
                    setError(`Error: ${err.message}`);
                }
                console.error(err);
            }
            setLoading(false);
        };
        fetchUsers();
    }, []);

    const handleUserCreated = (newUser) => {
        setUsers([newUser, ...users]);
        setIsModalOpen(false);
    };

    const handleUserUpdated = (updatedUser) => {
        setUsers(users.map(u => u.id === updatedUser.id ? updatedUser : u));
        setIsModalOpen(false);
        setEditingUser(null);
    };
    
    const openCreateModal = () => {
        setEditingUser(null);
        setIsModalOpen(true);
    };

    const openEditModal = (user) => {
        setEditingUser(user);
        setIsModalOpen(true);
    };

    const handleDeleteUser = async (userId, userName) => {
        if (!window.confirm(`Yakin hapus pengguna "${userName}"?`)) return;

        try {
            await api.delete(`/users/${userId}`);
            setUsers(users.filter(u => u.id !== userId));
        } catch (err) {
            alert(`Gagal menghapus ${userName}. Cek konsol.`);
            console.error(err);
        }
    };


    const getRoleClass = (role) => {
        switch (role) {
            case 'admin':
                return 'bg-red-100 text-red-800 border-red-200';
            case 'manager':
                return 'bg-blue-100 text-blue-800 border-blue-200';
            case 'technician':
                return 'bg-green-100 text-green-800 border-green-200';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    if (error) {
        return <ErrorState message={error} />;
    }

    return (
        <div>
            {/* Header & Action */}
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800">Manajemen Pengguna</h1>
                    <p className="text-slate-500 mt-1">Kelola akses dan peran pengguna sistem.</p>
                </div>
                <button
                    onClick={openCreateModal}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 transition-all transform hover:-translate-y-0.5"
                >
                    <UserPlus size={18} className="mr-2" /> Tambah Pengguna
                </button>
            </div>
            
            {/* Tabel Pengguna */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                
                {loading && <LoadingState />}
                
                {!loading && (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-slate-200">
                            <thead className="bg-slate-50">
                                <tr>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Nama Lengkap</th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Email</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Peran (Role)</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Opsi</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-slate-200">
                                {users.length === 0 && (
                                    <tr>
                                        <td colSpan="4" className="px-6 py-12 text-center text-slate-500">
                                            <div className="flex flex-col items-center gap-3">
                                                <div className="p-3 bg-slate-100 rounded-full">
                                                    <FileWarning size={32} className="text-slate-400" />
                                                </div>
                                                <p className="font-medium">Belum ada pengguna terdaftar.</p>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                                {users.map(user => (
                                    <tr key={user.id} className="hover:bg-slate-50 transition-colors group">
                                        
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <div className="flex-shrink-0 h-10 w-10 bg-slate-100 rounded-full flex items-center justify-center text-slate-500 font-bold border border-slate-200">
                                                    {user.name.charAt(0).toUpperCase()}
                                                </div>
                                                <div className="ml-4">
                                                    <div className="text-sm font-medium text-slate-900">{user.name}</div>
                                                </div>
                                            </div>
                                        </td>
                                        
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                                            {user.email}
                                        </td>
                                        
                                        <td className="px-6 py-4 whitespace-nowrap text-center">
                                            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border ${getRoleClass(user.role)}`}>
                                                {user.role.toUpperCase()}
                                            </span>
                                        </td>
                                        
                                        <td className="px-6 py-4 whitespace-nowrap text-center">
                                            <div className="flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button 
                                                    onClick={() => openEditModal(user)}
                                                    className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                                                    title="Edit Role & Reset Password"
                                                >
                                                    <Edit size={18} />
                                                </button>
                                                <button 
                                                    onClick={() => handleDeleteUser(user.id, user.name)}
                                                    className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                                                    title="Hapus Pengguna"
                                                >
                                                    <Trash2 size={18} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* MODAL CREATE/EDIT */}
            {isModalOpen && (
                <Modal 
                    isOpen={isModalOpen} 
                    onClose={() => setIsModalOpen(false)} 
                    title={editingUser ? `Edit Pengguna: ${editingUser.name}` : "Tambah Pengguna Baru"}
                >
                    <UserForm
                        initialData={editingUser}
                        onUserCreated={handleUserCreated}
                        onUserUpdated={handleUserUpdated}
                        onClose={() => setIsModalOpen(false)}
                    />
                </Modal>
            )}
        </div>
    );
}