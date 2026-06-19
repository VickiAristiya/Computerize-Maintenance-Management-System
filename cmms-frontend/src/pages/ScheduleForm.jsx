// src/pages/ScheduleForm.jsx
import React, { useState, useEffect, useMemo } from 'react';
import api from '../services/api';
import { CalendarPlus, Loader2, Repeat, Calendar, Save } from 'lucide-react';

export default function ScheduleForm({ assets, onScheduleCreated, initialData, onScheduleUpdated, onClose }) {
  const isEditMode = !!initialData;

  const [assetId, setAssetId] = useState(initialData?.asset_id || '');
  const [taskName, setTaskName] = useState(initialData?.task_name || '');
  const [component, setComponent] = useState(initialData?.component || ''); 
  const [frequencyDays, setFrequencyDays] = useState(initialData?.frequency_days || 30);
  const [description, setDescription] = useState(initialData?.description_template || '');
  
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
  
  // Reset component jika asset berubah, TAPI jangan reset saat inisialisasi edit mode
  useEffect(() => {
    if (!isEditMode) {
        setComponent(''); 
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assetId]);

  const resetForm = () => {
    setAssetId(''); setTaskName(''); setComponent(''); setFrequencyDays(30); setDescription('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const finalTaskName = taskName || (component ? `Perawatan: ${component}` : '');
    
    if (!assetId || !frequencyDays) { setError("Mesin dan Frekuensi wajib diisi."); return; }
    if (!finalTaskName) { setError("Nama Tugas wajib diisi."); return; }

    setError(null);
    setSuccess(null);
    setIsSubmitting(true);
    
    const payload = {
        asset_id: assetId,
        task_name: finalTaskName, 
        component: component,
        frequency_days: Number(frequencyDays),
        frequency: `Setiap ${frequencyDays} hari`,
        description_template: description,
    };

    try {
      let response;
      if (isEditMode) {
          // EDIT MODE
          response = await api.patch(`/schedules/${initialData.id}`, payload);
          if (onScheduleUpdated) onScheduleUpdated(response.data);
          if (onClose) onClose();
      } else {
          // CREATE MODE
          response = await api.post('/schedules', payload);
          if (onScheduleCreated) onScheduleCreated(response.data);
          setSuccess(`Jadwal "${response.data.task_name}" berhasil dibuat.`);
          resetForm();
      }
      
    } catch (err) {
      setError(err.response?.data?.error || `Gagal ${isEditMode ? 'mengupdate' : 'membuat'} jadwal.`);
    }
    setIsSubmitting(false);
  };

  return (
      <form onSubmit={handleSubmit} className="space-y-5">
        {error && <div className="p-3 bg-red-100 text-red-700 rounded-md text-sm">{error}</div>}
        {success && <div className="p-3 bg-green-100 text-green-700 rounded-md text-sm">{success}</div>}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Mesin */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-700 mb-1">Pilih Mesin (Aset) *</label>
            <select
              value={assetId}
              onChange={e => setAssetId(e.target.value)}
              required
              className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">-- Pilih Mesin --</option>
              {assets.map(asset => (
                <option key={asset.id} value={asset.id}>{asset.name} (ID: {asset.machine_id})</option>
              ))}
            </select>
          </div>

          {/* Komponen */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-700 mb-1">Komponen (Opsional)</label>
            <select
              value={component}
              onChange={e => setComponent(e.target.value)}
              disabled={!assetId} 
              className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 disabled:bg-slate-100"
            >
              <option value="">-- Pilih Komponen --</option>
              {availableComponents.map(comp => (
                <option key={comp.id} value={comp.name}>{comp.name}</option>
              ))}
            </select>
          </div>

          {/* Nama Tugas */}
          <div className="md:col-span-3">
            <label className="block text-sm font-medium text-slate-700 mb-1">Nama Tugas *</label>
            <div className="relative">
                <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16}/>
                <input
                type="text"
                value={taskName}
                onChange={e => setTaskName(e.target.value)}
                placeholder={component ? `Otomatis: Perawatan ${component}` : "Contoh: Ganti Oli Rutin"}
                className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
            </div>
          </div>

          {/* Frekuensi */}
          <div className="md:col-span-1">
            <label className="block text-sm font-medium text-slate-700 mb-1">Frekuensi (Hari) *</label>
            <div className="relative">
                <Repeat className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16}/>
                <input
                type="number"
                value={frequencyDays}
                onChange={e => setFrequencyDays(e.target.value)}
                min="1"
                required
                className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
            </div>
          </div>
        </div>

        {/* Deskripsi */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Deskripsi (Template)</label>
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            rows={2}
            placeholder="Instruksi singkat..."
            className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 resize-none"
          ></textarea>
        </div>

        <div className="flex justify-end gap-3 pt-2 border-t border-slate-100">
            {isEditMode && (
                <button 
                    type="button" 
                    onClick={onClose}
                    className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50"
                >
                    Batal
                </button>
            )}
          <button 
            type="submit" 
            disabled={isSubmitting}
            className="inline-flex items-center px-6 py-2.5 border border-transparent text-sm font-bold rounded-lg shadow-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-transform hover:-translate-y-0.5"
          >
            {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : isEditMode ? <Save className="mr-2 h-4 w-4" /> : <CalendarPlus className="mr-2 h-4 w-4" />}
            {isSubmitting ? 'Memproses...' : isEditMode ? 'Simpan Perubahan' : 'Simpan Jadwal'}
          </button>
        </div>
      </form>
  );
}