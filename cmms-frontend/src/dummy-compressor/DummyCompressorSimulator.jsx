import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Eye,
  Loader2,
  X,
} from 'lucide-react';
import { DUMMY_COMPRESSOR } from './compressorSensorGenerator.js';
import { useSocket } from '../context/useSocket.js';

export default function DummyCompressorSimulator() {
  const navigate = useNavigate();
  const [asset, setAsset]           = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [status, setStatus]         = useState('starting');
  const [isHidden, setIsHidden]     = useState(
    () => localStorage.getItem('dummyCompressorWidgetHidden') === 'true'
  );
  const isMountedRef = useRef(true);
  const { socket } = useSocket();

  const fetchPrediction = useCallback(async (machineId) => {
    try {
      const res = await api.post(`/ml/predict/${machineId}`);
      if (isMountedRef.current) setPrediction(res.data);
    } catch {
      // Belum ada data sensor lengkap masuk — biarkan status "siap menerima".
    }
  }, []);

  // Pastikan aset dummy ada, lalu ambil prediksi kesehatan sekali. Data
  // sensornya sendiri sekarang dikirim dari luar aplikasi (lihat
  // Simulasi/Version 2/simulasi-input data), bukan lewat front-end ini.
  // Update selanjutnya murni didorong oleh WebSocket (lihat efek di bawah).
  useEffect(() => {
    isMountedRef.current = true;

    const ensureAsset = async () => {
      try {
        const res = await api.get('/assets');
        const existing = res.data.find(a => a.machine_id === DUMMY_COMPRESSOR.machine_id);
        const current = existing || (await api.post('/assets', DUMMY_COMPRESSOR)).data;
        if (!isMountedRef.current) return;

        setAsset(current);
        setStatus('ready');
        fetchPrediction(current.machine_id);
      } catch {
        if (isMountedRef.current) setStatus('error');
      }
    };

    ensureAsset();
    return () => { isMountedRef.current = false; };
  }, [fetchPrediction]);

  // Refresh instan begitu ada data sensor baru untuk mesin dummy ini. Juga
  // refresh saat socket reconnect setelah sempat putus — jaring pengaman
  // untuk update yang mungkin terlewat selama disconnect (socket.io tidak
  // me-replay event yang di-emit saat client sedang putus). Karena efek ini
  // baru terpasang setelah `asset` siap (setelah round-trip HTTP), koneksi
  // awal socket biasanya sudah terjadi lebih dulu, jadi 'connect' di sini
  // pada praktiknya hanya menangkap reconnect sungguhan.
  useEffect(() => {
    if (!socket || !asset) return;
    const handleUpdate = (payload) => {
      if (payload?.machine_id === asset.machine_id) fetchPrediction(asset.machine_id);
    };
    const handleReconnect = () => fetchPrediction(asset.machine_id);
    socket.on('sensor_data_update', handleUpdate);
    socket.on('machine_alert', handleUpdate);
    socket.on('connect', handleReconnect);
    return () => {
      socket.off('sensor_data_update', handleUpdate);
      socket.off('machine_alert', handleUpdate);
      socket.off('connect', handleReconnect);
    };
  }, [socket, asset, fetchPrediction]);

  const isFault   = prediction?.overall_health_score < 0.7
                 || prediction?.risk_level === 'critical'
                 || prediction?.risk_level === 'high';
  const isLoading = status === 'starting';
  const Icon      = isLoading ? Loader2 : isFault ? AlertTriangle : CheckCircle2;

  if (isHidden) {
    return (
      <button
        type="button"
        onClick={() => { localStorage.setItem('dummyCompressorWidgetHidden', 'false'); setIsHidden(false); }}
        className="fixed bottom-4 right-4 z-40 inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-700 shadow-lg transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
      >
        <Eye size={15} />
        Prediktif
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-40 w-72 rounded-lg border border-slate-200 bg-white shadow-lg">

      {/* Header */}
      <div className="flex items-center gap-3 p-3">
        <div className={`rounded-md p-2 ${isFault ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'}`}>
          <Icon size={18} className={isLoading ? 'animate-spin' : ''} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-sm font-bold text-slate-800">
              {asset?.name || DUMMY_COMPRESSOR.name}
            </p>
            <Activity size={13} className="shrink-0 text-blue-500" />
          </div>
          <p className="truncate text-xs text-slate-500">
            {status === 'error'
              ? 'Gagal terhubung ke server'
              : prediction
                ? `Health ${Math.round((prediction.overall_health_score ?? 0) * 100)}% | ${prediction.risk_level}`
                : status === 'starting'
                  ? 'Menyiapkan aset...'
                  : 'Menunggu data sensor eksternal...'}
          </p>
        </div>
        <button
          type="button"
          onClick={() => { localStorage.setItem('dummyCompressorWidgetHidden', 'true'); setIsHidden(true); }}
          className="rounded-md p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
        >
          <X size={16} />
        </button>
      </div>

      {/* Tombol detail */}
      <div className="border-t border-slate-100 px-3 pb-3 pt-2">
        <button
          type="button"
          onClick={() => navigate('/monitoring')}
          className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-xs font-bold text-white transition hover:bg-blue-700"
        >
          <Activity size={14} />
          Lihat Detail Monitoring
        </button>
      </div>
    </div>
  );
}
