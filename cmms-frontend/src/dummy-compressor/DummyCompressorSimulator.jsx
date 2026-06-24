import React, { useEffect, useState } from 'react';
import api from '../services/api';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  Eye,
  Loader2,
  X,
} from 'lucide-react';
import { DUMMY_COMPRESSOR } from './compressorSensorGenerator.js';
import SensorInputModal from './SensorInputModal.jsx';

export default function DummyCompressorSimulator() {
  const [asset, setAsset]           = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [status, setStatus]         = useState('starting');
  const [modalOpen, setModalOpen]   = useState(false);
  const [isHidden, setIsHidden]     = useState(
    () => localStorage.getItem('dummyCompressorWidgetHidden') === 'true'
  );

  useEffect(() => {
    let isMounted = true;
    const ensureAsset = async () => {
      try {
        const res = await api.get('/assets');
        const existing = res.data.find(a => a.machine_id === DUMMY_COMPRESSOR.machine_id);
        if (existing) {
          if (isMounted) { setAsset(existing); setStatus('ready'); }
          return;
        }
        const created = await api.post('/assets', DUMMY_COMPRESSOR);
        if (isMounted) { setAsset(created.data); setStatus('ready'); }
      } catch {
        if (isMounted) setStatus('error');
      }
    };
    ensureAsset();
    return () => { isMounted = false; };
  }, []);

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
    <>
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
                    : 'Siap menerima data sensor'}
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

        {/* Tombol input */}
        <div className="border-t border-slate-100 px-3 pb-3 pt-2">
          <button
            type="button"
            disabled={status !== 'ready'}
            onClick={() => setModalOpen(true)}
            className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-xs font-bold text-white transition hover:bg-blue-700 disabled:opacity-40"
          >
            <ClipboardList size={14} />
            Input Data Sensor
          </button>
        </div>
      </div>

      <SensorInputModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        machineId={asset?.machine_id}
        onPredictionResult={pred => setPrediction(pred)}
      />
    </>
  );
}
