// src/pages/ReportPage.jsx
import React, { useState, useEffect } from 'react';
import api, { BASE_URL } from '../services/api';
import { FileWarning, FileText, FileDown, BarChart2 } from 'lucide-react';
import LoadingState from '../components/LoadingState.jsx';
import ErrorState from '../components/ErrorState.jsx';

const EXPORT_CSV_API = `${BASE_URL}/workorders/report/export/csv`;
const EXPORT_PDF_API = `${BASE_URL}/workorders/report/export/pdf`;

export default function ReportPage() {
  const [reportData, setReportData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Ambil data laporan
  useEffect(() => {
    const fetchReport = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get('/workorders/report/asset_stats');
        setReportData(response.data); 
      } catch (err) {
        if (err.response) {
          setError(`Gagal mengambil data laporan: ${err.response.status} ${err.response.statusText}`);
        } else if (err.request) {
          setError("Gagal memuat data. Pastikan server Flask berjalan.");
        } else {
          setError(`Error: ${err.message}`);
        }
        console.error(err);
      }
      setLoading(false);
    };

    fetchReport();
  }, []);

  // --- LOGIKA EKSPOR ---
  const handleExport = (format) => {
    let url;
    if (format === 'CSV') {
        url = EXPORT_CSV_API;
    } else if (format === 'PDF') {
        url = EXPORT_PDF_API;
    } else {
        return;
    }
    window.open(url, '_blank');
  };

  if (error) {
    return <ErrorState message={error} />;
  }

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
        <div>
            <h1 className="text-3xl font-bold text-slate-800">Laporan Kinerja</h1>
            <p className="text-slate-500 mt-1">Analisis detail performa work order berdasarkan aset.</p>
        </div>
        
        {/* Tombol Ekspor */}
        <div className="flex gap-3">
          <button
            onClick={() => handleExport('CSV')}
            disabled={loading || reportData.length === 0}
            className="inline-flex items-center px-4 py-2 bg-white border border-slate-300 text-sm font-medium rounded-lg text-slate-700 hover:bg-slate-50 shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FileDown size={18} className="mr-2 text-green-600" /> Export CSV
          </button>
          <button
            onClick={() => handleExport('PDF')}
            disabled={loading || reportData.length === 0}
            className="inline-flex items-center px-4 py-2 bg-white border border-slate-300 text-sm font-medium rounded-lg text-slate-700 hover:bg-slate-50 shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FileText size={18} className="mr-2 text-red-600" /> Export PDF
          </button>
        </div>
      </div>
      
      {/* Card Tabel Laporan */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-2">
            <BarChart2 size={20} className="text-blue-600"/>
            <h2 className="text-lg font-semibold text-slate-800">Statistik Work Order per Mesin</h2>
        </div>

        {loading && <LoadingState />}
        
        {!loading && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50/50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Nama Mesin (Aset)</th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Open</th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">In Progress</th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Completed</th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-slate-900 uppercase tracking-wider">Total WO</th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Completion Rate</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-100">
                {reportData.length === 0 ? (
                   <tr>
                     <td colSpan="6" className="px-6 py-12 text-center text-slate-500">
                       <div className="flex flex-col items-center gap-3">
                         <div className="p-3 bg-slate-100 rounded-full">
                             <FileWarning size={32} className="text-slate-400" />
                         </div>
                         <p className="font-medium">Belum ada data Work Order untuk dianalisis.</p>
                       </div>
                     </td>
                   </tr>
                ) : (
                    reportData.map(item => {
                        // Hitung persentase penyelesaian
                        const completionRate = item.total_wo > 0 
                            ? Math.round((item.completed / item.total_wo) * 100) 
                            : 0;
                        
                        return (
                          <tr key={item.asset_id} className="hover:bg-slate-50 transition-colors group">
                            <td className="px-6 py-4 whitespace-nowrap">
                                <span className="text-sm font-bold text-slate-800 group-hover:text-blue-600 transition-colors">
                                    {item.asset_name}
                                </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-center">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${item.open > 0 ? 'bg-red-100 text-red-700' : 'text-slate-400 bg-slate-100'}`}>
                                    {item.open}
                                </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-center">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${item.in_progress > 0 ? 'bg-amber-100 text-amber-700' : 'text-slate-400 bg-slate-100'}`}>
                                    {item.in_progress}
                                </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-center">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${item.completed > 0 ? 'bg-green-100 text-green-700' : 'text-slate-400 bg-slate-100'}`}>
                                    {item.completed}
                                </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-center">
                                <span className="text-sm font-bold text-slate-900">{item.total_wo}</span>
                            </td>
                            
                            {/* Kolom Baru: Completion Rate Progress Bar */}
                            <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center gap-2 justify-center">
                                    <div className="w-16 bg-slate-200 rounded-full h-2 overflow-hidden">
                                        <div 
                                            className={`h-full rounded-full ${completionRate === 100 ? 'bg-green-500' : 'bg-blue-500'}`} 
                                            style={{ width: `${completionRate}%` }}
                                        ></div>
                                    </div>
                                    <span className="text-xs font-medium text-slate-600">{completionRate}%</span>
                                </div>
                            </td>
                          </tr>
                        );
                    })
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}