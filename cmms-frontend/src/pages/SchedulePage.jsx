// src/pages/SchedulePage.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FileWarning, Trash2, CalendarPlus, Calendar, HardDrive, Repeat, Edit, AlertTriangle, Clock, CheckCircle } from 'lucide-react';
import LoadingState from '../components/LoadingState.jsx';
import ErrorState from '../components/ErrorState.jsx';
import ScheduleForm from './ScheduleForm.jsx';
import Modal from '../components/Modal.jsx';

const API_BASE_URL = 'http://localhost:5000/api';

export default function SchedulePage() {
  const [schedules, setSchedules] = useState([]);
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // State untuk Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState(null);

  // Fungsi untuk mengambil data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [scheduleResponse, assetResponse] = await Promise.all([
          axios.get(`${API_BASE_URL}/schedules`),
          axios.get(`${API_BASE_URL}/assets`)
        ]);
        
        setSchedules(scheduleResponse.data);
        setAssets(assetResponse.data);
      } catch (err) {
        if (err.response) {
          setError(`Gagal mengambil data: ${err.response.status} ${err.response.statusText}`);
        } else if (err.request) {
          setError("Gagal memuat data. Pastikan server Flask berjalan.");
        } else {
          setError(`Error: ${err.message}`);
        }
        console.error(err);
      }
      setLoading(false);
    };

    fetchData();
  }, []); 

  // CRUD Handlers
  const handleScheduleCreated = (newSchedule) => {
    setSchedules([...schedules, newSchedule].sort((a, b) => new Date(a.next_due_date) - new Date(b.next_due_date)));
    setIsModalOpen(false);
  };
  
  const handleScheduleUpdated = (updatedSchedule) => {
      setSchedules(schedules.map(s => s.id === updatedSchedule.id ? updatedSchedule : s).sort((a, b) => new Date(a.next_due_date) - new Date(b.next_due_date)));
      setIsModalOpen(false);
      setEditingSchedule(null);
  };

  const handleCompleteSchedule = async (scheduleId, taskName, frequencyDays) => {
    if (!window.confirm(`Tandai "${taskName}" sebagai selesai? Jadwal berikutnya akan diset ${frequencyDays} hari dari sekarang.`)) return;
    try {
      const response = await axios.post(`${API_BASE_URL}/schedules/${scheduleId}/complete`);
      setSchedules(schedules.map(s => s.id === scheduleId ? response.data : s).sort((a, b) => new Date(a.next_due_date) - new Date(b.next_due_date)));
    } catch (err) {
      alert("Gagal menyelesaikan jadwal.");
    }
  };

  const handleDeleteSchedule = async (scheduleId, taskName) => {
    if (!window.confirm(`Hapus jadwal rutin "${taskName}"?`)) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/schedules/${scheduleId}`);
      setSchedules(schedules.filter(s => s.id !== scheduleId));
    } catch (err) {
      console.error("Gagal menghapus jadwal:", err);
      alert("Gagal menghapus jadwal.");
    }
  };

  // Modal Triggers
  const openCreateModal = () => {
      setEditingSchedule(null);
      setIsModalOpen(true);
  };

  const openEditModal = (schedule) => {
      setEditingSchedule(schedule);
      setIsModalOpen(true);
  };

  // --- FITUR BARU: FORMAT WAKTU INDONESIA (WIB) ---
  const formatDateWIB = (isoString) => {
    if (!isoString) return '-';
    const date = new Date(isoString);
    return new Intl.DateTimeFormat('id-ID', {
      weekday: 'long', 
      day: 'numeric', 
      month: 'long', 
      year: 'numeric',
      timeZone: 'Asia/Jakarta', // Force WIB
    }).format(date);
  };

  // --- FITUR BARU: ALERT 7 HARI ---
  const getDueStatus = (dateString) => {
      if (!dateString) return null;
      const today = new Date();
      const dueDate = new Date(dateString);
      
      // Hitung selisih dalam milidetik
      const diffTime = dueDate - today;
      // Konversi ke hari (Math.ceil agar pembulatan ke atas)
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

      if (diffDays < 0) {
          return {
              type: 'overdue',
              label: `Terlewat ${Math.abs(diffDays)} hari`,
              className: 'bg-red-100 text-red-700 border-red-200'
          };
      } else if (diffDays <= 7) {
          return {
              type: 'warning',
              label: diffDays === 0 ? 'Hari ini!' : `${diffDays} hari lagi`,
              className: 'bg-amber-100 text-amber-700 border-amber-200 animate-pulse'
          };
      }
      
      return null; // Masih aman
  };

  if (error) return <ErrorState message={error} />;

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
            <h1 className="text-3xl font-bold text-slate-800">Penjadwalan Perawatan</h1>
            <p className="text-slate-500 mt-1">Atur jadwal preventive maintenance untuk aset Anda.</p>
        </div>
        <button
            onClick={openCreateModal}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg shadow-md hover:bg-blue-700 transition-all transform hover:-translate-y-0.5"
        >
            <CalendarPlus size={18} className="mr-2" /> Buat Jadwal Baru
        </button>
      </div>

      {/* Tabel Daftar Jadwal */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {loading && <LoadingState />}
        
        {!loading && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider w-1/4">
                      Tugas & Deskripsi
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                    <div className="flex items-center gap-1"><HardDrive size={14}/> Mesin (Aset)</div>
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                    <div className="flex items-center gap-1"><Repeat size={14}/> Frekuensi</div>
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                    <div className="flex items-center gap-1"><Calendar size={14}/> Jadwal Berikutnya</div>
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Opsi</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {schedules.length === 0 && (
                  <tr>
                    <td colSpan="5" className="px-6 py-12 text-center text-slate-500">
                      <div className="flex flex-col items-center gap-3">
                        <div className="p-3 bg-slate-100 rounded-full">
                            <FileWarning size={32} className="text-slate-400" />
                        </div>
                        <p className="font-medium">Belum ada jadwal perawatan.</p>
                        <p className="text-sm">Buat jadwal baru untuk memulai preventive maintenance.</p>
                      </div>
                    </td>
                  </tr>
                )}
                {schedules.map(s => {
                    const dueStatus = getDueStatus(s.next_due_date);
                    
                    return (
                      <tr key={s.id} className="hover:bg-slate-50 transition-colors group">
                        
                        {/* Tugas */}
                        <td className="px-6 py-4">
                            <div className="text-sm font-bold text-slate-900">{s.task_name}</div>
                            {s.description_template && (
                                <div className="text-xs text-slate-500 mt-0.5 line-clamp-1">{s.description_template}</div>
                            )}
                        </td>
                        
                        {/* Nama Aset */}
                        <td className="px-6 py-4 whitespace-nowrap">
                             <div className="text-sm font-medium text-slate-800">{s.asset_name}</div>
                             {s.component && (
                                 <span className="text-xs bg-slate-100 px-1.5 py-0.5 rounded text-slate-600 border border-slate-200">
                                     {s.component}
                                 </span>
                             )}
                        </td>
                        
                        {/* Frekuensi */}
                        <td className="px-6 py-4 whitespace-nowrap">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100">
                                <Clock size={12} className="mr-1"/> {s.frequency}
                            </span>
                        </td>
                        
                        {/* Jadwal Berikutnya (Dengan Alert) */}
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">
                            <div className="flex items-center gap-2">
                                <span>{formatDateWIB(s.next_due_date)}</span>
                                {dueStatus && (
                                    <span className={`flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold border ${dueStatus.className}`}>
                                        <AlertTriangle size={10} /> {dueStatus.label}
                                    </span>
                                )}
                            </div>
                        </td>

                        {/* Opsi */}
                        <td className="px-6 py-4 whitespace-nowrap text-center">
                          <div className="flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                    onClick={() => handleCompleteSchedule(s.id, s.task_name, s.frequency_days)}
                                    className="p-1.5 text-slate-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                                    title="Tandai Selesai (Maju ke Siklus Berikutnya)"
                                >
                                    <CheckCircle size={18} />
                                </button>
                                <button
                                    onClick={() => openEditModal(s)}
                                    className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                    title="Edit Jadwal"
                                >
                                    <Edit size={18} />
                                </button>
                                <button
                                    onClick={() => handleDeleteSchedule(s.id, s.task_name)}
                                    className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                    title="Hapus Jadwal"
                                >
                                    <Trash2 size={18} />
                                </button>
                          </div>
                        </td>
                      
                      </tr>
                    );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* MODAL CREATE / EDIT */}
      {isModalOpen && (
        <Modal 
            isOpen={isModalOpen} 
            onClose={() => setIsModalOpen(false)} 
            title={editingSchedule ? "Edit Jadwal" : "Buat Jadwal Baru"}
        >
            <ScheduleForm 
                assets={assets} 
                initialData={editingSchedule}
                onScheduleCreated={handleScheduleCreated}
                onScheduleUpdated={handleScheduleUpdated}
                onClose={() => setIsModalOpen(false)}
            />
        </Modal>
      )}

    </div>
  );
}