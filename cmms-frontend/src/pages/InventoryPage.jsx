// src/pages/InventoryPage.jsx
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { FileWarning, Plus, Loader2, Edit, Trash2, PackagePlus, Save, Box, MapPin, Tag, Search, ArrowUpDown } from 'lucide-react';
import LoadingState from '../components/LoadingState.jsx';
import ErrorState from '../components/ErrorState.jsx';
import Modal from '../components/Modal.jsx';

// --- Komponen Form (digunakan untuk Create dan Edit) ---
function InventoryForm({ onSave, initialData, onClose }) {
    const isEditMode = !!initialData;
    const [name, setName] = useState(initialData?.name || '');
    const [partNumber, setPartNumber] = useState(initialData?.part_number || '');
    const [stock, setStock] = useState(initialData?.stock_quantity || 0);
    const [location, setLocation] = useState(initialData?.location || 'Gudang Utama');
    
    const [error, setError] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setIsSubmitting(true);

        const payload = { 
            name, 
            part_number: partNumber, 
            stock_quantity: parseInt(stock, 10), 
            location 
        };
        
        try {
            let response;
            if (isEditMode) {
                // PATCH (Update)
                response = await api.patch(`/inventory/components/${initialData.id}`, payload);
            } else {
                // POST (Create)
                response = await api.post('/inventory/components', payload);
            }
            onSave(response.data); // Panggil callback
            onClose(); // Tutup modal/form
        } catch (err) {
            setError(err.response?.data?.error || "Gagal menyimpan komponen.");
            console.error(err); 
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {error && <div className="p-3 bg-red-100 text-red-700 rounded-md">{error}</div>}
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label htmlFor="compName" className="block text-sm font-medium text-slate-700 mb-1">Nama Komponen *</label>
                    <input type="text" id="compName" value={name} onChange={e => setName(e.target.value)} required className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-blue-500 focus:border-blue-500 transition-colors"/>
                </div>
                <div>
                    <label htmlFor="compPartNum" className="block text-sm font-medium text-slate-700 mb-1">Part Number</label>
                    <input type="text" id="compPartNum" value={partNumber} onChange={e => setPartNumber(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-blue-500 focus:border-blue-500 transition-colors"/>
                </div>
                <div>
                    <label htmlFor="compStock" className="block text-sm font-medium text-slate-700 mb-1">Kuantitas Stok *</label>
                    <input type="number" id="compStock" value={stock} onChange={e => setStock(e.target.value)} min="0" required className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-blue-500 focus:border-blue-500 transition-colors"/>
                </div>
                <div>
                    <label htmlFor="compLocation" className="block text-sm font-medium text-slate-700 mb-1">Lokasi di Gudang</label>
                    <input type="text" id="compLocation" value={location} onChange={e => setLocation(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-blue-500 focus:border-blue-500 transition-colors"/>
                </div>
            </div>
            <div className="text-right pt-4 flex justify-end gap-3">
                <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors">Batal</button>
                <button type="submit" disabled={isSubmitting} className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-all transform hover:-translate-y-0.5">
                    {isSubmitting ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : isEditMode ? (
                        <Save className="mr-2 h-4 w-4" /> 
                    ) : (
                        <Plus className="mr-2 h-4 w-4" />
                    )}
                    {isSubmitting ? 'Menyimpan...' : (isEditMode ? 'Simpan Perubahan' : 'Tambah Komponen')}
                </button>
            </div>
        </form>
    );
}

// --- Halaman Utama Inventaris ---
export default function InventoryPage() {
    const [components, setComponents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // State untuk Modal Create/Edit
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingComponent, setEditingComponent] = useState(null);

    // Search, Sort & Filter
    const [searchTerm, setSearchTerm] = useState('');
    const [sortKey, setSortKey] = useState('name_asc');
    const [stockFilter, setStockFilter] = useState('all');

    useEffect(() => {
        const fetchComponents = async () => {
            setLoading(true);
            setError(null);
            try {
                const response = await api.get('/inventory/components');
                setComponents(response.data);
            } catch (err) {
                setError("Gagal memuat data inventaris.");
                console.error("Fetch components error:", err); 
            }
            setLoading(false);
        };

        fetchComponents();
    }, []);

    // Handler Create (setelah form disubmit)
    const handleComponentCreated = (newComponent) => {
        setComponents([newComponent, ...components]);
        setIsModalOpen(false);
    };

    // Handler Update (setelah form disubmit)
    const handleComponentUpdated = (updatedComponent) => {
        setComponents(components.map(c => c.id === updatedComponent.id ? updatedComponent : c));
        setIsModalOpen(false);
        setEditingComponent(null);
    };

    // Handler Delete
    const handleDeleteComponent = async (componentId, componentName) => {
        if (!window.confirm(`Yakin hapus komponen "${componentName}" dari gudang?`)) return;

        try {
            await api.delete(`/inventory/components/${componentId}`);
            setComponents(components.filter(c => c.id !== componentId));
        } catch (err) {
            alert("Gagal menghapus komponen.");
            console.error("Delete component error:", err); 
        }
    };
    
    const openCreateModal = () => {
        setEditingComponent(null);
        setIsModalOpen(true);
    };

    const openEditModal = (component) => {
        setEditingComponent(component);
        setIsModalOpen(true);
    };

    // Helper untuk warna stok
    const getStockBadgeClass = (qty) => {
        if (qty === 0) return 'bg-red-100 text-red-700 border-red-200';
        if (qty < 5) return 'bg-amber-100 text-amber-700 border-amber-200';
        return 'bg-green-100 text-green-700 border-green-200';
    };

    if (error) {
        return <ErrorState message={error} />;
    }

    const displayedComponents = components
      .filter(item => {
        const q = searchTerm.toLowerCase();
        const matchSearch = item.name.toLowerCase().includes(q) ||
          (item.part_number || '').toLowerCase().includes(q) ||
          (item.location || '').toLowerCase().includes(q);
        const matchStock = stockFilter === 'all' ||
          (stockFilter === 'empty' && item.stock_quantity === 0) ||
          (stockFilter === 'low' && item.stock_quantity > 0 && item.stock_quantity < 5) ||
          (stockFilter === 'available' && item.stock_quantity >= 5);
        return matchSearch && matchStock;
      })
      .sort((a, b) => {
        if (sortKey === 'name_asc') return a.name.localeCompare(b.name);
        if (sortKey === 'name_desc') return b.name.localeCompare(a.name);
        if (sortKey === 'stock_asc') return a.stock_quantity - b.stock_quantity;
        if (sortKey === 'stock_desc') return b.stock_quantity - a.stock_quantity;
        return 0;
      });

    return (
        <div>
            {/* Header & Action */}
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800">Gudang & Inventaris</h1>
                    <p className="text-slate-500 mt-1">Kelola stok komponen dan spare part mesin.</p>
                </div>
                <div className="flex gap-3">
                    {/* (Opsional: Search Bar bisa ditambahkan di sini nanti) */}
                    <button
                        onClick={openCreateModal}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 transition-all transform hover:-translate-y-0.5"
                    >
                        <PackagePlus size={18} className="mr-2" /> Tambah Komponen
                    </button>
                </div>
            </div>
            
            {/* Search & Filter Bar */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 mb-4">
              <div className="flex flex-wrap gap-3 items-center">
                <div className="relative flex-1 min-w-[200px]">
                  <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Cari nama, part number, atau lokasi..."
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  />
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <ArrowUpDown size={15} className="text-slate-400" />
                  <select
                    value={sortKey}
                    onChange={e => setSortKey(e.target.value)}
                    className="text-sm border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none bg-white"
                  >
                    <option value="name_asc">Nama A→Z</option>
                    <option value="name_desc">Nama Z→A</option>
                    <option value="stock_desc">Stok Terbanyak</option>
                    <option value="stock_asc">Stok Tersedikit</option>
                  </select>
                </div>
                <select
                  value={stockFilter}
                  onChange={e => setStockFilter(e.target.value)}
                  className="text-sm border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none bg-white shrink-0"
                >
                  <option value="all">Semua Stok</option>
                  <option value="available">Tersedia (≥5)</option>
                  <option value="low">Stok Rendah (1–4)</option>
                  <option value="empty">Habis (0)</option>
                </select>
              </div>
            </div>

            {/* Tabel Inventaris */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                {loading && <LoadingState />}
                
                {!loading && (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-slate-200">
                            <thead className="bg-slate-50">
                                <tr>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                                        <div className="flex items-center gap-2"><Box size={14}/> Nama Komponen</div>
                                    </th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                                        <div className="flex items-center gap-2"><Tag size={14}/> Part Number</div>
                                    </th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Stok</th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                                        <div className="flex items-center gap-2"><MapPin size={14}/> Lokasi</div>
                                    </th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Opsi</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-slate-200">
                                {displayedComponents.length === 0 && (
                                    <tr>
                                        <td colSpan="5" className="px-6 py-12 text-center text-slate-500">
                                            <div className="flex flex-col items-center gap-3">
                                                <div className="p-3 bg-slate-100 rounded-full">
                                                    <FileWarning size={32} className="text-slate-400" />
                                                </div>
                                                {components.length === 0 ? (
                                                  <>
                                                    <p className="font-medium">Gudang kosong.</p>
                                                    <p className="text-sm">Mulai dengan menambahkan komponen baru.</p>
                                                  </>
                                                ) : (
                                                  <p className="font-medium">Tidak ada hasil untuk pencarian ini.</p>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                )}
                                {displayedComponents.map(item => (
                                    <tr key={item.id} className="hover:bg-slate-50 transition-colors group">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-slate-900">{item.name}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 font-mono">{item.part_number || '-'}</td>
                                        
                                        <td className="px-6 py-4 whitespace-nowrap text-center">
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold border ${getStockBadgeClass(item.stock_quantity)}`}>
                                                {item.stock_quantity} Unit
                                            </span>
                                        </td>
                                        
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">{item.location}</td>
                                        
                                        <td className="px-6 py-4 whitespace-nowrap text-center">
                                            <div className="flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button 
                                                    onClick={() => openEditModal(item)}
                                                    className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition" 
                                                    title="Edit Komponen">
                                                    <Edit size={18} />
                                                </button>
                                                <button 
                                                    onClick={() => handleDeleteComponent(item.id, item.name)}
                                                    className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition" 
                                                    title="Hapus Komponen">
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
                    title={editingComponent ? "Edit Komponen" : "Tambah Komponen Baru"}
                >
                    <InventoryForm
                        initialData={editingComponent}
                        onSave={editingComponent ? handleComponentUpdated : handleComponentCreated}
                        onClose={() => setIsModalOpen(false)}
                    />
                </Modal>
            )}
        </div>
    );
}