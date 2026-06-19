import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
    Activity, AlertTriangle, Power, Pause, Wrench, AlertOctagon, Zap, 
    RefreshCw, Filter, Grid, List, Edit2, Check, X, Loader2 
} from 'lucide-react';
import LoadingState from '../components/LoadingState.jsx';
import ErrorState from '../components/ErrorState.jsx';

const API_BASE_URL = 'http://localhost:5000/api';

// Status configuration
const STATUS_CONFIG = {
    running: {
        label: 'Berjalan',
        color: 'bg-green-100',
        textColor: 'text-green-700',
        borderColor: 'border-green-300',
        icon: Activity,
        bgColor: '#DCFCE7',
        dotColor: '#22C55E'
    },
    idle: {
        label: 'Menganggur',
        color: 'bg-blue-100',
        textColor: 'text-blue-700',
        borderColor: 'border-blue-300',
        icon: Pause,
        bgColor: '#DBEAFE',
        dotColor: '#3B82F6'
    },
    breakdown: {
        label: 'Rusak',
        color: 'bg-red-100',
        textColor: 'text-red-700',
        borderColor: 'border-red-300',
        icon: AlertOctagon,
        bgColor: '#FEE2E2',
        dotColor: '#EF4444'
    },
    off: {
        label: 'Mati',
        color: 'bg-slate-100',
        textColor: 'text-slate-700',
        borderColor: 'border-slate-300',
        icon: Power,
        bgColor: '#F1F5F9',
        dotColor: '#64748B'
    },
    maintenance: {
        label: 'Perawatan',
        color: 'bg-amber-100',
        textColor: 'text-amber-700',
        borderColor: 'border-amber-300',
        icon: Wrench,
        bgColor: '#FEF3C7',
        dotColor: '#F59E0B'
    },
    warning: {
        label: 'Peringatan',
        color: 'bg-orange-100',
        textColor: 'text-orange-700',
        borderColor: 'border-orange-300',
        icon: AlertTriangle,
        bgColor: '#FFEDD5',
        dotColor: '#F97316'
    }
};

// --- STAT CARD ---
const StatCard = ({ status, count, color, icon: Icon }) => (
    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition">
        <div className="flex items-center justify-between">
            <div>
                <p className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">
                    {STATUS_CONFIG[status]?.label || status}
                </p>
                <p className="text-3xl font-bold text-slate-800">{count}</p>
            </div>
            <div 
                className="p-3 rounded-lg"
                style={{ backgroundColor: STATUS_CONFIG[status]?.bgColor }}
            >
                <Icon 
                    size={24} 
                    style={{ color: STATUS_CONFIG[status]?.dotColor }}
                />
            </div>
        </div>
    </div>
);

// --- MACHINE CARD (Grid View) ---
const MachineCard = ({ machine, onStatusChange, isUpdating }) => {
    const config = STATUS_CONFIG[machine.status] || STATUS_CONFIG.running;
    const Icon = config.icon;
    
    const [isEditing, setIsEditing] = useState(false);
    const [newStatus, setNewStatus] = useState(machine.status);
    
    const handleStatusSubmit = async () => {
        await onStatusChange(machine.id, newStatus);
        setIsEditing(false);
    };
    
    return (
        <div className={`bg-white rounded-xl border-2 ${config.borderColor} p-4 shadow-sm hover:shadow-lg transition-all duration-300`}>
            {/* Header dengan Status Dot */}
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                    <div 
                        className="w-4 h-4 rounded-full animate-pulse"
                        style={{ backgroundColor: config.dotColor }}
                    />
                    <span className={`text-xs font-bold px-2 py-1 rounded-full ${config.color}`}>
                        {config.label}
                    </span>
                </div>
                {machine.pending_wo_count > 0 && (
                    <div className="bg-red-100 text-red-700 text-xs font-bold px-2 py-1 rounded-full">
                        {machine.pending_wo_count} WO
                    </div>
                )}
            </div>
            
            {/* Machine Image atau Placeholder */}
            <div className={`w-full h-40 rounded-lg mb-3 flex items-center justify-center ${config.color} border-2 ${config.borderColor}`}>
                {machine.image ? (
                    <img src={machine.image} alt={machine.name} className="w-full h-full object-cover rounded-lg" />
                ) : (
                    <Icon size={48} style={{ color: config.dotColor }} opacity="0.5" />
                )}
            </div>
            
            {/* Machine Info */}
            <div className="mb-3">
                <h3 className="font-bold text-slate-800 text-sm mb-0.5 line-clamp-1">{machine.name}</h3>
                <p className="text-xs text-slate-500 mb-2">ID: {machine.machine_id}</p>
                <p className="text-xs text-slate-600"><span className="font-semibold">Lokasi:</span> {machine.location || 'N/A'}</p>
            </div>
            
            {/* Status Selector */}
            {isEditing ? (
                <div className="mb-3 space-y-2">
                    <select 
                        value={newStatus} 
                        onChange={(e) => setNewStatus(e.target.value)}
                        className="w-full px-2 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        {Object.entries(STATUS_CONFIG).map(([key, val]) => (
                            <option key={key} value={key}>{val.label}</option>
                        ))}
                    </select>
                    <div className="flex gap-1.5">
                        <button 
                            onClick={handleStatusSubmit}
                            disabled={isUpdating}
                            className="flex-1 bg-green-600 text-white text-xs font-bold py-1.5 rounded hover:bg-green-700 disabled:bg-slate-300 flex items-center justify-center gap-1"
                        >
                            {isUpdating ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />} Simpan
                        </button>
                        <button 
                            onClick={() => setIsEditing(false)}
                            className="flex-1 bg-slate-300 text-slate-700 text-xs font-bold py-1.5 rounded hover:bg-slate-400 flex items-center justify-center gap-1"
                        >
                            <X size={12} /> Batal
                        </button>
                    </div>
                </div>
            ) : (
                <button 
                    onClick={() => setIsEditing(true)}
                    className="w-full bg-blue-600 text-white text-xs font-bold py-1.5 rounded hover:bg-blue-700 flex items-center justify-center gap-1"
                >
                    <Edit2 size={12} /> Ubah Status
                </button>
            )}
        </div>
    );
};

// --- MACHINE ROW (List View) ---
const MachineRow = ({ machine, onStatusChange, isUpdating }) => {
    const config = STATUS_CONFIG[machine.status] || STATUS_CONFIG.running;
    const Icon = config.icon;
    
    const [isEditing, setIsEditing] = useState(false);
    const [newStatus, setNewStatus] = useState(machine.status);
    
    const handleStatusSubmit = async () => {
        await onStatusChange(machine.id, newStatus);
        setIsEditing(false);
    };
    
    return (
        <tr className="hover:bg-slate-50 transition-colors border-b">
            <td className="px-6 py-4">
                <div className="flex items-center gap-2">
                    <div 
                        className="w-3 h-3 rounded-full animate-pulse"
                        style={{ backgroundColor: config.dotColor }}
                    />
                    <span className={`text-xs font-bold px-2 py-1 rounded-full ${config.color}`}>
                        {config.label}
                    </span>
                </div>
            </td>
            <td className="px-6 py-4">
                <div>
                    <p className="font-semibold text-slate-800 text-sm">{machine.name}</p>
                    <p className="text-xs text-slate-500">ID: {machine.machine_id}</p>
                </div>
            </td>
            <td className="px-6 py-4 text-sm text-slate-600">
                {machine.location || 'N/A'}
            </td>
            <td className="px-6 py-4 text-center">
                {machine.pending_wo_count > 0 ? (
                    <div className="bg-red-100 text-red-700 text-xs font-bold px-2 py-1 rounded-full inline-block">
                        {machine.pending_wo_count} WO
                    </div>
                ) : (
                    <span className="text-xs text-slate-400">-</span>
                )}
            </td>
            <td className="px-6 py-4">
                {isEditing ? (
                    <div className="flex gap-1.5">
                        <select 
                            value={newStatus} 
                            onChange={(e) => setNewStatus(e.target.value)}
                            className="px-2 py-1 text-xs border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            {Object.entries(STATUS_CONFIG).map(([key, val]) => (
                                <option key={key} value={key}>{val.label}</option>
                            ))}
                        </select>
                        <button 
                            onClick={handleStatusSubmit}
                            disabled={isUpdating}
                            className="bg-green-600 text-white px-2 py-1 text-xs font-bold rounded hover:bg-green-700 disabled:bg-slate-300"
                        >
                            {isUpdating ? <Loader2 size={12} className="animate-spin inline" /> : 'Simpan'}
                        </button>
                        <button 
                            onClick={() => setIsEditing(false)}
                            className="bg-slate-300 text-slate-700 px-2 py-1 text-xs font-bold rounded hover:bg-slate-400"
                        >
                            Batal
                        </button>
                    </div>
                ) : (
                    <button 
                        onClick={() => setIsEditing(true)}
                        className="bg-blue-600 text-white px-3 py-1 text-xs font-bold rounded hover:bg-blue-700 flex items-center gap-1"
                    >
                        <Edit2 size={12} /> Edit
                    </button>
                )}
            </td>
        </tr>
    );
};

// --- MAIN PAGE ---
export default function MachineMonitoringPage() {
    const [machines, setMachines] = useState([]);
    const [statusSummary, setStatusSummary] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [viewMode, setViewMode] = useState('grid'); // grid atau list
    const [selectedStatusFilter, setSelectedStatusFilter] = useState('all');
    const [isUpdating, setIsUpdating] = useState(null);

    const fetchMonitoring = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.get(`${API_BASE_URL}/assets/monitoring/dashboard`);
            setMachines(response.data.assets);
            setStatusSummary(response.data.status_summary);
        } catch (err) {
            console.error("Fetch Error:", err);
            setError(err.response?.data?.error || "Gagal memuat data monitoring.");
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchMonitoring();
    }, []);

    const handleStatusChange = async (machineId, newStatus) => {
        setIsUpdating(machineId);
        try {
            const response = await axios.patch(
                `${API_BASE_URL}/assets/${machineId}/status`,
                { status: newStatus }
            );
            
            // Update state
            setMachines(machines.map(m => m.id === machineId ? response.data.asset : m));
            
            // Re-fetch monitoring untuk update statistik
            await fetchMonitoring();
        } catch (err) {
            console.error("Update Error:", err);
            alert(err.response?.data?.error || "Gagal mengubah status mesin.");
        }
        setIsUpdating(null);
    };

    const filteredMachines = selectedStatusFilter === 'all' 
        ? machines 
        : machines.filter(m => m.status === selectedStatusFilter);

    if (error) return <ErrorState message={error} />;

    return (
        <div>
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">Machine Monitoring</h1>
                    <p className="text-slate-500 mt-1 text-sm">Pantau status dan kondisi semua mesin secara real-time.</p>
                </div>
                <button 
                    onClick={fetchMonitoring}
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition gap-2"
                >
                    <RefreshCw size={18} /> Refresh
                </button>
            </div>

            {/* Status Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
                {Object.entries(STATUS_CONFIG).map(([status, config]) => {
                    const Icon = config.icon;
                    return (
                        <StatCard 
                            key={status}
                            status={status} 
                            count={statusSummary[status] || 0} 
                            icon={Icon}
                        />
                    );
                })}
            </div>

            {/* Filter & View Controls */}
            <div className="bg-white rounded-xl border border-slate-200 p-4 mb-6 shadow-sm">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div className="flex items-center gap-2">
                        <Filter size={20} className="text-slate-500" />
                        <span className="text-sm font-bold text-slate-700">Filter Status:</span>
                        <select 
                            value={selectedStatusFilter}
                            onChange={(e) => setSelectedStatusFilter(e.target.value)}
                            className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="all">Semua Mesin ({machines.length})</option>
                            {Object.entries(STATUS_CONFIG).map(([key, val]) => (
                                <option key={key} value={key}>
                                    {val.label} ({statusSummary[key] || 0})
                                </option>
                            ))}
                        </select>
                    </div>
                    
                    <div className="flex gap-2">
                        <button 
                            onClick={() => setViewMode('grid')}
                            className={`px-3 py-1.5 rounded-lg text-sm font-bold flex items-center gap-1.5 transition ${
                                viewMode === 'grid' 
                                    ? 'bg-blue-600 text-white' 
                                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                            }`}
                        >
                            <Grid size={16} /> Grid
                        </button>
                        <button 
                            onClick={() => setViewMode('list')}
                            className={`px-3 py-1.5 rounded-lg text-sm font-bold flex items-center gap-1.5 transition ${
                                viewMode === 'list' 
                                    ? 'bg-blue-600 text-white' 
                                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                            }`}
                        >
                            <List size={16} /> List
                        </button>
                    </div>
                </div>
            </div>

            {/* Machines Content */}
            {loading ? (
                <LoadingState />
            ) : filteredMachines.length === 0 ? (
                <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
                    <Zap size={48} className="mx-auto text-slate-300 mb-4" />
                    <p className="text-slate-600 font-medium">Tidak ada mesin untuk status ini.</p>
                </div>
            ) : viewMode === 'grid' ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {filteredMachines.map(machine => (
                        <MachineCard 
                            key={machine.id} 
                            machine={machine} 
                            onStatusChange={handleStatusChange}
                            isUpdating={isUpdating === machine.id}
                        />
                    ))}
                </div>
            ) : (
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                    <table className="min-w-full divide-y divide-slate-200">
                        <thead className="bg-slate-50">
                            <tr>
                                <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Nama Mesin</th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Lokasi</th>
                                <th className="px-6 py-4 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Work Order</th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Aksi</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200">
                            {filteredMachines.map(machine => (
                                <MachineRow 
                                    key={machine.id} 
                                    machine={machine} 
                                    onStatusChange={handleStatusChange}
                                    isUpdating={isUpdating === machine.id}
                                />
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
