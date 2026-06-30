// src/components/MLNotificationDetailModal.jsx
import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom';
import api from '../services/api';
import {
  Activity, AlertTriangle, CheckCircle2, Loader2, X,
} from 'lucide-react';

const RISK_COLORS = {
  critical: 'text-rose-700 bg-rose-50 border-rose-200',
  high:     'text-red-700 bg-red-50 border-red-200',
  medium:   'text-orange-700 bg-orange-50 border-orange-200',
  low:      'text-yellow-700 bg-yellow-50 border-yellow-200',
  very_low: 'text-green-700 bg-green-50 border-green-200',
};

const RISK_LABELS = {
  critical: 'Kritis', high: 'Tinggi', medium: 'Sedang',
  low: 'Rendah', very_low: 'Sangat Rendah',
};

const COMPONENT_LABELS = {
  bearings: 'Bearing',
};

const SENSOR_FIELDS = [
  { key: 'noise_db',    label: 'Kebisingan',         unit: 'dB' },
  { key: 'water_flow',  label: 'Aliran Air',          unit: 'L/min' },
  { key: 'air_flow',    label: 'Aliran Udara',        unit: 'm³/h' },
  { key: 'gaccx',       label: 'G-Axis Akselerasi X', unit: 'g' },
  { key: 'outlet_temp', label: 'Suhu Outlet',         unit: '°C' },
];

function formatDue(iso) {
  if (!iso) return '-';
  return new Date(iso).toLocaleDateString('id-ID', {
    day: '2-digit', month: 'short', year: 'numeric',
  });
}

function formatVal(v) {
  if (v === null || v === undefined) return '-';
  const n = parseFloat(v);
  return isNaN(n) ? '-' : n.toLocaleString('id-ID', { maximumFractionDigits: 3 });
}

function ComponentCard({ comp }) {
  const isOk    = comp.prediction === 'Ok' || comp.prediction === 'Clean';
  const riskCls = RISK_COLORS[comp.risk_level] || RISK_COLORS.very_low;
  const hsPct   = Math.round((comp.health_score ?? 0) * 100);

  return (
    <div className={`rounded-lg border p-3 ${isOk ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-bold text-slate-700">
          {COMPONENT_LABELS[comp.key] || comp.label || comp.key}
        </span>
        <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold border ${riskCls}`}>
          {RISK_LABELS[comp.risk_level] || comp.risk_level}
        </span>
      </div>
      <div className="flex justify-between text-[11px] mb-1">
        <span className={`font-semibold ${isOk ? 'text-green-700' : 'text-red-700'}`}>{comp.status}</span>
        <span className="text-slate-500">{comp.prediction}</span>
      </div>
      <div className="flex justify-between text-[11px] mb-1">
        <span className="text-slate-500">Health Score</span>
        <span className={`font-bold ${hsPct >= 70 ? 'text-green-700' : 'text-red-700'}`}>{hsPct}%</span>
      </div>
      <div className="flex justify-between text-[11px] mb-1">
        <span className="text-slate-500">Prob. Fault</span>
        <span className="font-medium text-slate-700">
          {Math.round((comp.failure_probability ?? 0) * 100)}%
        </span>
      </div>
      <div className="flex justify-between text-[11px] mb-0.5">
        <span className="text-slate-500">Tenggat</span>
        <span className="font-medium text-slate-700">
          {comp.predicted_days === 0 ? 'Segera' : `${comp.predicted_days} hari`}
        </span>
      </div>
      <div className="flex justify-between text-[10px]">
        <span className="text-slate-400">Due date</span>
        <span className="text-slate-500">{formatDue(comp.due_date)}</span>
      </div>
    </div>
  );
}

export default function MLNotificationDetailModal({ notification, onClose }) {
  // Sensor readings fetch (lightweight — hanya query DB, tanpa ML)
  const [sensors, setSensors]             = useState(null);
  const [sensorLoading, setSensorLoading] = useState(false);
  const [sensorTimestamp, setSensorTimestamp] = useState(null);
  const [sensorError, setSensorError]     = useState(null);

  useEffect(() => {
    if (!notification?.machine_id) {
      setSensorError(`machine_id tidak tersedia (id: ${notification?.id})`);
      return;
    }
    setSensorLoading(true);
    setSensors(null);
    setSensorError(null);

    api.get(`/ml/sensor-history/${notification.machine_id}?limit=1`)
      .then(res => {
        const latest = res.data?.history?.[0];
        if (latest) {
          setSensors(latest);
          setSensorTimestamp(latest.timestamp);
        } else {
          setSensorError('Belum ada data sensor tersimpan untuk mesin ini.');
        }
      })
      .catch(err => {
        const msg = err.response?.data?.error || err.message || 'Gagal memuat data sensor';
        setSensorError(msg);
        console.error('[MLModal] sensor-history error:', err);
      })
      .finally(() => setSensorLoading(false));
  }, [notification?.machine_id]);

  if (!notification) return null;

  const overallHealth = Math.round((notification.overall_health_score ?? notification.health_score ?? 0) * 100);
  const isHealthy     = overallHealth >= 70;
  const riskCls       = RISK_COLORS[notification.risk_level] || RISK_COLORS.very_low;
  const components    = notification.faulty_components || [];

  return ReactDOM.createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 p-4">
      <div className="flex h-[94vh] w-full max-w-3xl flex-col rounded-xl bg-white shadow-2xl">

        {/* Header */}
        <div className="flex shrink-0 items-center justify-between border-b border-slate-100 px-6 py-4">
          <div className="flex items-center gap-2">
            <Activity size={18} className="text-blue-600" />
            <div>
              <h2 className="text-base font-bold text-slate-800 leading-tight">
                Detail Prediksi Kondisi Mesin
              </h2>
              <p className="text-xs text-slate-500">{notification.asset_name}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-5">

          {/* ── Ringkasan Kondisi ── */}
          <div className={`rounded-lg border p-4 ${isHealthy ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {isHealthy
                  ? <CheckCircle2 size={18} className="text-green-600" />
                  : <AlertTriangle size={18} className="text-red-600" />}
                <span className="text-sm font-bold text-slate-800">
                  {isHealthy ? 'Mesin dalam kondisi baik' : 'Mesin memerlukan perhatian'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`rounded px-2 py-0.5 text-xs font-bold border ${riskCls}`}>
                  {RISK_LABELS[notification.risk_level] || notification.risk_level}
                </span>
                <span className={`text-sm font-bold ${isHealthy ? 'text-green-700' : 'text-red-700'}`}>
                  Health {overallHealth}%
                </span>
              </div>
            </div>
            {notification.recommendation && (
              <p className="mt-2 text-xs text-slate-700 leading-relaxed">
                {notification.recommendation}
              </p>
            )}
          </div>

          {/* ── Kondisi per Komponen ── */}
          {components.length > 0 && (
            <div>
              <h3 className="mb-2.5 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Komponen Bermasalah
              </h3>
              <div className="grid grid-cols-1 gap-2">
                {components.map((comp, i) => (
                  <ComponentCard key={comp.key || i} comp={comp} />
                ))}
              </div>
            </div>
          )}

          {/* ── Metadata Prediksi ── */}
          <div className="rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
            <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs text-slate-500">
              <div className="flex justify-between">
                <span>Predicted Days</span>
                <span className="font-medium text-slate-700">
                  {notification.predicted_days === 0 ? 'Segera' : `${notification.predicted_days} hari`}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Prob. Failure</span>
                <span className="font-medium text-slate-700">
                  {Math.round((notification.failure_probability ?? 0) * 100)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span>Due Date</span>
                <span className="font-medium text-slate-700">{formatDue(notification.date)}</span>
              </div>
              {sensorTimestamp && (
                <div className="flex justify-between">
                  <span>Timestamp Sensor</span>
                  <span className="font-medium text-slate-700">
                    {new Date(sensorTimestamp).toLocaleString('id-ID')}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* ── Nilai Sensor (lazy load) ── */}
          <div>
            <h3 className="mb-2.5 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Sensor Bearing (Terbaru)
            </h3>
            {sensorLoading ? (
              <div className="flex items-center gap-2 text-xs text-slate-400 py-2">
                <Loader2 size={14} className="animate-spin" />
                Memuat nilai sensor...
              </div>
            ) : sensorError ? (
              <p className="text-xs text-red-400">{sensorError}</p>
            ) : sensors ? (
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {SENSOR_FIELDS.map(({ key, label, unit }) => (
                  <div
                    key={key}
                    className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5"
                  >
                    <p className="text-[10px] text-slate-400 mb-0.5">
                      {label} <span className="font-normal">({unit})</span>
                    </p>
                    <p className="text-sm font-bold text-slate-800">
                      {formatVal(sensors[key])}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400">Tidak ada data sensor.</p>
            )}
          </div>

        </div>

        {/* Footer */}
        <div className="flex shrink-0 justify-end border-t border-slate-100 px-6 py-4">
          <button
            onClick={onClose}
            className="rounded-lg border border-slate-200 px-5 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            Tutup
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
