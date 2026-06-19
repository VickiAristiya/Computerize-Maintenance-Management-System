import React, { useEffect, useState } from 'react';
import api from '../services/api';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  Eye,
  Loader2,
  Wrench,
  X,
} from 'lucide-react';
import {
  DUMMY_COMPRESSOR,
  getTemplateData,
} from './compressorSensorGenerator.js';
import SensorInputModal from './SensorInputModal.jsx';

const RISK_OPTIONS = [
  { mode: 'maintenance_low', label: 'Rendah', className: 'border-yellow-200 bg-yellow-50 text-yellow-700' },
  { mode: 'maintenance_medium', label: 'Sedang', className: 'border-orange-200 bg-orange-50 text-orange-700' },
  { mode: 'maintenance_high', label: 'Tinggi', className: 'border-red-200 bg-red-50 text-red-700' },
  { mode: 'maintenance_critical', label: 'Kritis', className: 'border-rose-300 bg-rose-50 text-rose-700' },
];

export default function DummyCompressorSimulator() {
  const [asset, setAsset] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [status, setStatus] = useState('starting');
  const [showMaintenance, setShowMaintenance] = useState(false);
  const [isHidden, setIsHidden] = useState(
    () => localStorage.getItem('dummyCompressorWidgetHidden') === 'true'
  );
  const [modal, setModal] = useState({
    open: false,
    mode: null,
    modeLabel: null,
    initialData: null,
  });

  useEffect(() => {
    let isMounted = true;

    const ensureAsset = async () => {
      try {
        const res = await api.get('/assets');
        const existing = res.data.find((a) => a.machine_id === DUMMY_COMPRESSOR.machine_id);
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

  const openModal = (mode, modeLabel, useTemplate) => {
    setModal({
      open: true,
      mode,
      modeLabel,
      initialData: useTemplate ? getTemplateData(mode) : null,
    });
    setShowMaintenance(false);
  };

  const closeModal = () => setModal((prev) => ({ ...prev, open: false }));

  const hideWidget = () => {
    localStorage.setItem('dummyCompressorWidgetHidden', 'true');
    setIsHidden(true);
  };

  const showWidget = () => {
    localStorage.setItem('dummyCompressorWidgetHidden', 'false');
    setIsHidden(false);
  };

  const isFault = prediction?.prediction === 'Noisy' || prediction?.risk_level === 'critical';
  const isLoading = status === 'starting';
  const Icon = isLoading ? Loader2 : isFault ? AlertTriangle : CheckCircle2;

  if (isHidden) {
    return (
      <button
        type="button"
        onClick={showWidget}
        className="fixed bottom-4 right-4 z-40 inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-700 shadow-lg transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
        title="Tampilkan widget prediktif"
      >
        <Eye size={15} />
        Prediktif
      </button>
    );
  }

  return (
    <>
      <div className="fixed bottom-4 right-4 z-40 w-80 rounded-lg border border-slate-200 bg-white shadow-lg">

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
                  ? `${prediction.prediction} | Risiko ${prediction.risk_level} | ${Math.round(prediction.failure_probability * 100)}%`
                  : status === 'starting'
                    ? 'Menyiapkan aset...'
                    : 'Pilih mode untuk input data sensor'}
            </p>
          </div>
          <button
            type="button"
            onClick={hideWidget}
            className="rounded-md p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
            title="Sembunyikan widget"
          >
            <X size={16} />
          </button>
        </div>

        {/* Mode buttons */}
        <div className="flex items-center gap-1.5 border-t border-slate-100 px-3 pb-3 pt-2">
          <button
            type="button"
            onClick={() => { openModal('normal', 'Mode Normal', true); setShowMaintenance(false); }}
            className="inline-flex flex-1 items-center justify-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs font-bold text-slate-600 transition hover:border-green-200 hover:bg-green-50 hover:text-green-700"
            title="Input data sensor kondisi normal"
          >
            <CheckCircle2 size={13} />
            Normal
          </button>
          <button
            type="button"
            onClick={() => setShowMaintenance((prev) => !prev)}
            className={`inline-flex flex-1 items-center justify-center gap-1 rounded-md border px-2 py-1.5 text-xs font-bold transition ${
              showMaintenance
                ? 'border-red-200 bg-red-50 text-red-700'
                : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
            }`}
            title="Input data sensor kondisi maintenance"
          >
            <Wrench size={13} />
            Maintenance
          </button>
          <button
            type="button"
            onClick={() => { openModal('manual', 'Input Manual', false); setShowMaintenance(false); }}
            className="inline-flex flex-1 items-center justify-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs font-bold text-slate-600 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
            title="Input data sensor secara manual tanpa template"
          >
            <ClipboardList size={13} />
            Manual
          </button>
        </div>

        {/* Maintenance risk sub-options */}
        {showMaintenance && (
          <div className="grid grid-cols-4 gap-1.5 border-t border-slate-100 px-3 pb-3 pt-2">
            {RISK_OPTIONS.map((opt) => (
              <button
                key={opt.mode}
                type="button"
                onClick={() => openModal(opt.mode, `Maintenance ${opt.label}`, true)}
                className={`rounded-md border px-1.5 py-1 text-[11px] font-bold transition hover:opacity-80 ${opt.className}`}
                title={`Input data sensor maintenance risiko ${opt.label.toLowerCase()}`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        )}
      </div>

      <SensorInputModal
        isOpen={modal.open}
        onClose={closeModal}
        initialData={modal.initialData}
        mode={modal.mode}
        modeLabel={modal.modeLabel}
        assetId={asset?.id}
        onPredictionResult={(pred) => setPrediction(pred)}
      />
    </>
  );
}
