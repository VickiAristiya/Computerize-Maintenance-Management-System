// src/pages/CompliancePage.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FileWarning, CheckCircle, Clock, RefreshCw, AlertTriangle, ShieldCheck, Plus, Calendar } from 'lucide-react';
import LoadingState from '../components/LoadingState.jsx';
import ErrorState from '../components/ErrorState.jsx';
import ComplianceForm from './ComplianceForm.jsx';
import Modal from '../components/Modal.jsx'; // <-- Impor Modal

const API_BASE_URL = 'http://localhost:5000/api';
const LOGS_API = `${API_BASE_URL}/compliance/logs`;
const ASSETS_API = `${API_BASE_URL}/assets`;

export default function CompliancePage() {
  const [logs, setLogs] = useState([]);
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // State untuk Modal
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
        const [logResponse, assetResponse] = await Promise.all([
            axios.get(LOGS_API),
            axios.get(ASSETS_API)
        ]);
        
        setLogs(logResponse.data);
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

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchData();
  }, []);

  const handleLogCreated = (newLog) => {
    setLogs([newLog, ...logs]);
    setIsModalOpen(false); // Tutup modal
  };
  
  // FUNGSI UPDATE STATUS
  const handleUpdateStatus = async (logId, newStatus) => {
    const originalLogs = [...logs];
    
    // Optimistic Update
    setLogs(logs.map(log =>
        log.id === logId ? { ...log, status: newStatus } : log
    ));

    try {
        await axios.patch(`${LOGS_API}/${logId}`, { status: newStatus });
        const updatedLogs = await axios.get(LOGS_API);
        setLogs(updatedLogs.data);
    } catch (err) {
        console.error("Gagal update status kepatuhan:", err);
        setLogs(originalLogs);
        alert(`Gagal mengubah status. Cek konsol untuk info.`);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleDateString('id-ID', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });
  };
  
  const getStatusInfo = (status) => {
    switch (status) {
      case 'pending':
        return { text: 'Pending', class: 'bg-amber-100 text-amber-700 border-amber-200', icon: Clock };
      case 'compliant':
        return { text: 'Compliant', class: 'bg-green-100 text-green-700 border-green-200', icon: CheckCircle };
      case 'overdue':
        return { text: 'Overdue', class: 'bg-red-100 text-red-700 border-red-200', icon: AlertTriangle };
      default:
        return { text: status, class: 'bg-gray-100 text-gray-700 border-gray-200', icon: AlertTriangle };
    }
  };

  if (error) return <ErrorState message={error} />;

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
            <h1 className="text-3xl font-bold text-slate-800">Manajemen Kalibrasi & Regulasi</h1>
            <p className="text-slate-500 mt-1">Monitor status kalibrasi dan regulasi aset.</p>
        </div>
        <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg shadow-md hover:bg-blue-700 transition-all transform hover:-translate-y-0.5"
        >
            <Plus size={18} className="mr-2" /> Catat Log Baru
        </button>
      </div>

      {/* Tabel Daftar Log */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {loading && <LoadingState />}
        
        {!loading && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                    <div className="flex items-center gap-2"><ShieldCheck size={14}/> Regulasi / Standar</div>
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Mesin (Aset)</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                    <div className="flex items-center gap-2"><Calendar size={14}/> Jatuh Tempo</div>
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Tindakan</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {logs.length === 0 && (
                  <tr>
                    <td colSpan="5" className="px-6 py-12 text-center text-slate-500">
                      <div className="flex flex-col items-center gap-3">
                        <div className="p-3 bg-slate-100 rounded-full">
                            <FileWarning size={32} className="text-slate-400" />
                        </div>
                        <p className="font-medium">Belum ada log kepatuhan.</p>
                        <p className="text-sm">Catat log baru untuk memulai pelacakan.</p>
                      </div>
                    </td>
                  </tr>
                )}
                {logs.map(log => {
                    const statusInfo = getStatusInfo(log.status);
                    const IconComponent = statusInfo.icon;
                    return (
                        <tr key={log.id} className="hover:bg-slate-50 transition-colors group">
                            
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-slate-900">
                                {log.regulation_name}
                            </td>
                            
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600 font-medium">
                                {log.asset_name}
                            </td>
                            
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold border ${statusInfo.class}`}>
                                <IconComponent size={12} className="mr-1.5" />
                                {statusInfo.text}
                              </span>
                            </td>
                            
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">
                                {formatDate(log.next_check_due)}
                            </td>
                            
                            <td className="px-6 py-4 whitespace-nowrap text-center">
                                <div className="flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                    {(log.status === 'pending' || log.status === 'overdue') && (
                                        <button 
                                            onClick={() => handleUpdateStatus(log.id, 'compliant')}
                                            title="Tandai Selesai (Compliant)" 
                                            className="p-2 text-slate-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition"
                                        >
                                            <CheckCircle size={18} />
                                        </button>
                                    )}
                                    {log.status === 'compliant' && (
                                        <button 
                                            onClick={() => handleUpdateStatus(log.id, 'pending')}
                                            title="Reset ke Pending" 
                                            className="p-2 text-slate-400 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition"
                                        >
                                            <RefreshCw size={18} />
                                        </button>
                                    )}
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

      {/* MODAL CREATE */}
      {isModalOpen && (
        <Modal 
            isOpen={isModalOpen} 
            onClose={() => setIsModalOpen(false)} 
            title="Catat Log Kepatuhan Baru"
        >
            <ComplianceForm 
                assets={assets} 
                onLogCreated={handleLogCreated} 
                // Tambahkan prop onClose jika ComplianceForm mendukungnya, atau biarkan form menanganinya
            />
        </Modal>
      )}
    </div>
  );
}