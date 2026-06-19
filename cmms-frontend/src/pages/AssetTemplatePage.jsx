// src/pages/AssetTemplatePage.jsx
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { FileWarning, Plus, Loader2, Trash2, ListPlus, Edit, Save } from 'lucide-react'; // Tambah Edit & Save
import LoadingState from '../components/LoadingState.jsx';
import ErrorState from '../components/ErrorState.jsx';
import Modal from '../components/Modal.jsx';

// --- Komponen Form (digunakan untuk Create & Edit Template) ---
function TemplateForm({ onSave, onClose, allComponents, initialData }) {
    const isEditMode = !!initialData;
    
    // State Nama
    const [name, setName] = useState(initialData?.name || '');
    
    // State Checkbox (Set ID)
    const [selectedComponentIds, setSelectedComponentIds] = useState(() => {
        if (initialData && initialData.component_ids) {
            return new Set(initialData.component_ids);
        }
        return new Set();
    });
    
    const [error, setError] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Handler untuk checkbox
    const handleComponentChange = (componentId) => {
        setSelectedComponentIds(prevIds => {
            const newIds = new Set(prevIds);
            if (newIds.has(componentId)) {
                newIds.delete(componentId);
            } else {
                newIds.add(componentId);
            }
            return newIds;
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setIsSubmitting(true);

        const payload = { 
            name, 
            component_ids: Array.from(selectedComponentIds) 
        };
        
        try {
            let response;
            if (isEditMode) {
                // PATCH (Update)
                response = await api.patch(`/templates/${initialData.id}`, payload);
            } else {
                // POST (Create)
                response = await api.post('/templates', payload);
            }
            onSave(response.data); // Panggil callback
            onClose(); // Tutup modal
        } catch (err) {
            setError(err.response?.data?.error || "Gagal menyimpan template.");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {error && <div className="p-3 bg-red-100 text-red-700 rounded-md">{error}</div>}
            
            {/* Nama Template */}
            <div>
                <label htmlFor="templateName" className="block text-sm font-medium text-slate-700 mb-1">Nama Tipe Aset (Template) *</label>
                <input type="text" id="templateName" value={name} onChange={e => setName(e.target.value)} required placeholder="Contoh: Wheel Balancing Machine" className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-blue-500 focus:border-blue-500"/>
            </div>

            {/* Pilihan Komponen */}
            <div className="pt-2">
                <label className="block text-sm font-medium text-slate-700 mb-2">Pilih Komponen Standar (BOM) *</label>
                {allComponents.length === 0 ? (
                    <p className="text-sm text-slate-500">Data komponen di gudang kosong. Silakan isi data di halaman Gudang.</p>
                ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-64 overflow-y-auto p-2 border rounded-md bg-slate-50">
                    {allComponents.map(comp => (
                        <label key={comp.id} className="flex items-center space-x-2 p-2 rounded hover:bg-white hover:shadow-sm transition-all cursor-pointer">
                        <input
                            type="checkbox"
                            checked={selectedComponentIds.has(comp.id)}
                            onChange={() => handleComponentChange(comp.id)}
                            className="h-4 w-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm text-slate-700">{comp.name}</span>
                        </label>
                    ))}
                    </div>
                )}
                <p className="text-xs text-slate-500 mt-1">Total dipilih: {selectedComponentIds.size}</p>
            </div>
            
            <div className="text-right pt-4 flex justify-end gap-3">
                <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50">Batal</button>
                <button type="submit" disabled={isSubmitting || allComponents.length === 0} className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50">
                    {isSubmitting ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : isEditMode ? (
                        <Save className="mr-2 h-4 w-4" />
                    ) : (
                        <Plus className="mr-2 h-4 w-4" />
                    )}
                    {isSubmitting ? 'Menyimpan...' : isEditMode ? 'Simpan Perubahan' : 'Simpan Template'}
                </button>
            </div>
        </form>
    );
}

// --- Halaman Utama Template ---
export default function AssetTemplatePage() {
    const [templates, setTemplates] = useState([]);
    const [allComponents, setAllComponents] = useState([]); // Master list komponen
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // State untuk Modal
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingTemplate, setEditingTemplate] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                // Ambil data template dan data komponen gudang secara bersamaan
                const [templateRes, componentRes] = await Promise.all([
                    api.get('/templates'),
                    api.get('/inventory/components')
                ]);
                setTemplates(templateRes.data);
                setAllComponents(componentRes.data);
            } catch (err) {
                setError("Gagal memuat data. Pastikan server berjalan.");
                console.error(err);
            }
            setLoading(false);
        };

        fetchData();
    }, []);

    // Handler Create
    const handleTemplateCreated = (newTemplate) => {
        setTemplates([newTemplate, ...templates]);
        setIsModalOpen(false);
    };

    // Handler Update
    const handleTemplateUpdated = (updatedTemplate) => {
        setTemplates(templates.map(t => t.id === updatedTemplate.id ? updatedTemplate : t));
        setIsModalOpen(false);
        setEditingTemplate(null);
    };

    // Handler Delete
    const handleDeleteTemplate = async (templateId, templateName) => {
        if (!window.confirm(`Yakin hapus template "${templateName}"?`)) return;

        try {
            await api.delete(`/templates/${templateId}`);
            setTemplates(templates.filter(t => t.id !== templateId));
        } catch (err) {
            alert("Gagal menghapus template.");
            console.error(err);
        }
    };

    // Fungsi Buka Modal Create
    const openCreateModal = () => {
        setEditingTemplate(null);
        setIsModalOpen(true);
    };

    // Fungsi Buka Modal Edit
    const openEditModal = (template) => {
        setEditingTemplate(template);
        setIsModalOpen(true);
    };

    if (error) {
        return <ErrorState message={error} />;
    }

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800">Manajemen Tipe Aset (Template)</h1>
                    <p className="text-slate-500 mt-1">Buat resep komponen (BOM) standar untuk mempercepat pendaftaran aset.</p>
                </div>
                <button
                    onClick={openCreateModal}
                    disabled={loading || allComponents.length === 0}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 transition-transform hover:-translate-y-0.5"
                >
                    <ListPlus size={18} className="mr-2" /> Buat Template Baru
                </button>
            </div>
            
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
                    <h2 className="text-lg font-semibold text-slate-800">Daftar Template Tersedia</h2>
                </div>

                {loading && <LoadingState />}
                
                {!loading && (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-slate-200">
                            <thead className="bg-slate-50">
                                <tr>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Nama Template</th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Jumlah Komponen</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Opsi</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-slate-200">
                                {templates.length === 0 && (
                                    <tr>
                                        <td colSpan="3" className="px-6 py-12 text-center text-slate-500">
                                            <div className="flex flex-col items-center gap-2">
                                                <FileWarning size={40} className="text-slate-400" />
                                                <span>Belum ada template yang dibuat.</span>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                                {templates.map(item => (
                                    <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-slate-900">{item.name}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                {item.component_ids.length} item
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
                                            <div className="flex items-center justify-center gap-2">
                                                <button 
                                                    onClick={() => openEditModal(item)}
                                                    className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition" 
                                                    title="Edit Template"
                                                >
                                                    <Edit size={18} />
                                                </button>
                                                <button 
                                                    onClick={() => handleDeleteTemplate(item.id, item.name)}
                                                    className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition" 
                                                    title="Hapus Template"
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
            
            {/* Modal untuk Create/Edit */}
            {isModalOpen && (
                <Modal 
                    isOpen={isModalOpen} 
                    onClose={() => setIsModalOpen(false)} 
                    title={editingTemplate ? "Edit Template Aset" : "Buat Template Aset Baru"}
                >
                    <TemplateForm
                        allComponents={allComponents}
                        initialData={editingTemplate}
                        onSave={editingTemplate ? handleTemplateUpdated : handleTemplateCreated}
                        onClose={() => setIsModalOpen(false)}
                    />
                </Modal>
            )}
        </div>
    );
}