// src/pages/WorkOrderForm.jsx
import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Plus, Loader2, Save, FileText, Settings, Image as ImageIcon } from 'lucide-react'; 
import { useAuth } from '../context/useAuth.js';

const API_BASE_URL = 'http://localhost:5000/api';

export default function WorkOrderForm({ assets, onWorkOrderCreated, initialData, onWOUpdated, onClose }) {
  const { user } = useAuth(); 
  const isEditMode = !!initialData;
  
  const [title, setTitle] = useState(initialData?.title || '');
  const [description, setDescription] = useState(initialData?.description || '');
  const [assetId, setAssetId] = useState(initialData?.asset_id || ''); 
  const [componentId, setComponentId] = useState(initialData?.component_id || '');
  const [type, setType] = useState(initialData?.type || 'corrective');
  const [priority, setPriority] = useState(initialData?.priority || 'medium');
  const [initialImage, setInitialImage] = useState(initialData?.initial_image || '');

  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const availableComponents = useMemo(() => {
    if (assetId) {
      const selectedAsset = assets.find(a => a.id === assetId);
      return selectedAsset?.components || []; 
    }
    return []; 
  }, [assetId, assets]);

  useEffect(() => {
    if (!isEditMode) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setComponentId('');
    }
  }, [assetId, isEditMode]);

  const handleImageChange = (e) => {
      const file = e.target.files[0];
      if (file) {
          const reader = new FileReader();
          reader.onloadend = () => {
              setInitialImage(reader.result);
          };
          reader.readAsDataURL(file);
      }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    let finalTitle = title;
    if (type === 'corrective' && componentId && !title) {
        const selectedComp = availableComponents.find(c => c.id === componentId);
        finalTitle = `Perbaikan: ${selectedComp?.name || 'Komponen'}`;
    }

    if (!assetId || !type) {
      setError("Mesin dan Tipe WO wajib diisi.");
      return;
    }
    if (!finalTitle) {
        setError("Judul WO wajib diisi.");
        return;
    }
    // Validasi Foto Awal Wajib saat Create
    if (!isEditMode && !initialImage) {
        setError("Wajib menyertakan foto bagian yang bermasalah/perlu dicek.");
        return;
    }

    setError(null);
    setSuccess(null);
    setIsSubmitting(true);

    const payload = {
      title: finalTitle,
      description: description,
      asset_id: assetId,
      component_id: componentId || null, 
      type: type,
      priority: priority,
      initial_image: initialImage,
      created_by_role: user?.role || 'technician' // Penting untuk logika approval di backend
    };

    try {
      let response;
      if (isEditMode) {
        response = await axios.patch(`${API_BASE_URL}/workorders/${initialData.id}`, payload);
        onWOUpdated(response.data); 
        onClose(); 
      } else {
        response = await axios.post(`${API_BASE_URL}/workorders`, payload);
        onWorkOrderCreated(response.data); 
        setSuccess(`Work Order berhasil dibuat.`);
        setTitle(''); setDescription(''); setAssetId(''); setComponentId(''); setType('corrective'); setPriority('medium'); setInitialImage('');
      }
    } catch (err) {
      setError(err.response?.data?.error || `Gagal ${isEditMode ? 'mengupdate' : 'membuat'} WO.`);
    }
    setIsSubmitting(false);
  };

  return (
      <form onSubmit={handleSubmit} className="space-y-5">
        {error && <div className="p-3 bg-red-100 text-red-700 rounded-md text-sm">{error}</div>}
        {success && !isEditMode && <div className="p-3 bg-green-100 text-green-700 rounded-md text-sm">{success}</div>}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Pilih Mesin (Aset) *</label>
            <div className="relative">
                <select
                value={assetId}
                onChange={e => setAssetId(e.target.value)} 
                required
                disabled={isEditMode} 
                className="w-full pl-3 pr-10 py-2.5 border border-slate-300 rounded-lg focus:ring-blue-500 disabled:bg-slate-100"
                >
                <option value="">-- Pilih Mesin --</option>
                {assets.map(asset => (
                    <option key={asset.id} value={asset.id}>{asset.name} (ID: {asset.machine_id})</option>
                ))}
                </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Tipe Pekerjaan *</label>
            <select
              value={type}
              onChange={e => setType(e.target.value)}
              required
              className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-blue-500"
            >
              <option value="corrective">Corrective (Perbaikan)</option>
              <option value="preventive">Preventive (Pencegahan)</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Komponen Terkait</label>
            <div className="relative">
                <Settings size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"/>
                <select
                value={componentId}
                onChange={e => setComponentId(e.target.value)}
                disabled={!assetId || type !== 'corrective'} 
                className="w-full pl-9 pr-10 py-2.5 border border-slate-300 rounded-lg focus:ring-blue-500 disabled:bg-slate-100"
                >
                <option value="">-- Opsional --</option>
                {availableComponents.map(comp => (
                    <option key={comp.id} value={comp.id}>{comp.name} (Stok: {comp.stock_quantity})</option>
                ))}
                </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Prioritas</label>
            <select
              value={priority}
              onChange={e => setPriority(e.target.value)}
              className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-blue-500"
            >
              <option value="low">Low (Rendah)</option>
              <option value="medium">Medium (Sedang)</option>
              <option value="high">High (Tinggi - Mendesak)</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Judul Work Order *</label>
          <div className="relative">
             <FileText size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"/>
             <input
               type="text"
               value={title}
               onChange={e => setTitle(e.target.value)}
               placeholder="Contoh: Pengecekan Rutin"
               required={type === 'preventive' || (type === 'corrective' && !componentId)}
               className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-lg focus:ring-blue-500"
             />
          </div>
        </div>

        <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
                Foto Bagian Masalah/Pencegahan { !isEditMode && <span className="text-red-500">*</span> }
            </label>
            <div className="border border-slate-300 rounded-lg p-3 bg-slate-50">
                <div className="flex items-center gap-3">
                    <div className="shrink-0">
                         {initialImage ? (
                             <img src={initialImage} alt="Preview" className="h-16 w-16 object-cover rounded-md border border-slate-200"/>
                         ) : (
                             <div className="h-16 w-16 bg-slate-200 rounded-md flex items-center justify-center text-slate-400">
                                 <ImageIcon size={24} />
                             </div>
                         )}
                    </div>
                    <input 
                        type="file" 
                        accept="image/*"
                        onChange={handleImageChange}
                        required={!isEditMode}
                        className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                </div>
            </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Deskripsi Detail (Opsional)</label>
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            rows={3}
            className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-blue-500 resize-none"
          ></textarea>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
          {isEditMode && (
              <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50">
                  Batal
              </button>
          )}
          <button 
            type="submit" 
            disabled={isSubmitting}
            className={`inline-flex items-center px-6 py-2.5 border border-transparent text-sm font-bold rounded-lg shadow-md text-white ${
              isEditMode ? 'bg-green-600 hover:bg-green-700' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : isEditMode ? <Save className="mr-2 h-4 w-4" /> : <Plus className="mr-2 h-4 w-4" />}
            {isSubmitting ? 'Memproses...' : isEditMode ? 'Simpan Perubahan' : 'Simpan Work Order'}
          </button>
        </div>
      </form>
  );
}