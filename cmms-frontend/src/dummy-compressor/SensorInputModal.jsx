import React, { useEffect, useState } from 'react';
import api from '../services/api';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  Loader2,
  RotateCcw,
  Send,
  Trash2,
  X,
} from 'lucide-react';
import { SENSOR_TEMPLATES, SENSOR_FIELD_GROUPS } from './compressorSensorGenerator.js';

const ALL_KEYS   = SENSOR_FIELD_GROUPS.flatMap(g => g.fields.map(f => f.key));
const EMPTY_FORM = Object.fromEntries(ALL_KEYS.map(k => [k, '']));

function toFormStrings(data) {
  return Object.fromEntries(ALL_KEYS.map(k => [k, data[k] !== undefined ? String(data[k]) : '']));
}

// ── Warna risk ──────────────────────────────────────────────────────────────
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
  wpump:    'Water Pump',
  radiator: 'Radiator',
  exvalve:  'Exhaust Valve',
};

// ── Warna badge template ────────────────────────────────────────────────────
const TEMPLATE_BADGE = {
  green:  'border-green-200 bg-green-50 text-green-700',
  purple: 'border-purple-200 bg-purple-50 text-purple-700',
  blue:   'border-blue-200 bg-blue-50 text-blue-700',
  orange: 'border-orange-200 bg-orange-50 text-orange-700',
  red:    'border-red-200 bg-red-50 text-red-700',
  slate:  'border-slate-200 bg-slate-50 text-slate-700',
};

function formatDue(iso) {
  if (!iso) return '-';
  return new Date(iso).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' });
}

// ── ComponentBadge ──────────────────────────────────────────────────────────
function ComponentBadge({ comp }) {
  const isOk    = comp.prediction === 'Ok' || comp.prediction === 'Clean';
  const riskCls = RISK_COLORS[comp.risk_level] || RISK_COLORS.very_low;
  const hsPct   = Math.round((comp.health_score ?? 0) * 100);
  return (
    <div className={`rounded-lg border p-3 ${isOk ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-bold text-slate-700">{comp.name}</span>
        <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold border ${riskCls}`}>
          {RISK_LABELS[comp.risk_level] || comp.risk_level}
        </span>
      </div>
      <div className="flex items-center justify-between text-[11px] mb-1">
        <span className={`font-semibold ${isOk ? 'text-green-700' : 'text-red-700'}`}>{comp.status}</span>
        <span className="text-slate-500 font-medium">{comp.prediction}</span>
      </div>
      <div className="flex items-center justify-between text-[11px] mb-1">
        <span className="text-slate-500">Health Score</span>
        <span className={`font-bold ${hsPct >= 70 ? 'text-green-700' : 'text-red-700'}`}>{hsPct}%</span>
      </div>
      <div className="flex items-center justify-between text-[11px] mb-1">
        <span className="text-slate-500">Prob. Fault</span>
        <span className="font-medium text-slate-700">
          {Math.round((comp.failure_probability ?? 0) * 100)}%
        </span>
      </div>
      <div className="flex items-center justify-between text-[11px] mb-0.5">
        <span className="text-slate-500">Tenggat</span>
        <span className="font-medium text-slate-700">
          {comp.predicted_days === 0 ? 'Segera' : `${comp.predicted_days} hari`}
        </span>
      </div>
      <div className="flex items-center justify-between text-[10px]">
        <span className="text-slate-400">Due date</span>
        <span className="text-slate-500">{formatDue(comp.due_date)}</span>
      </div>
    </div>
  );
}

// ── TemplateSelector ────────────────────────────────────────────────────────
function TemplateSelector({ selected, onChange }) {
  const [open, setOpen] = useState(false);
  const current = SENSOR_TEMPLATES.find(t => t.id === selected) || SENSOR_TEMPLATES[0];

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="flex w-full items-center justify-between gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-left text-sm transition hover:border-blue-300 hover:bg-blue-50"
      >
        <div className="min-w-0">
          <p className="text-xs font-bold text-slate-700 truncate">{current.label}</p>
          <p className="text-[10px] text-slate-400 truncate">{current.description}</p>
        </div>
        <ChevronDown
          size={15}
          className={`shrink-0 text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div className="absolute left-0 right-0 top-full z-20 mt-1 max-h-72 overflow-y-auto rounded-lg border border-slate-200 bg-white shadow-xl">
          {SENSOR_TEMPLATES.map(t => {
            const badgeCls = TEMPLATE_BADGE[t.color] || TEMPLATE_BADGE.slate;
            const isActive = t.id === selected;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => { onChange(t.id); setOpen(false); }}
                className={`flex w-full items-start gap-3 px-3 py-2.5 text-left transition hover:bg-slate-50 ${
                  isActive ? 'bg-blue-50' : ''
                }`}
              >
                <span className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-[9px] font-bold border ${badgeCls}`}>
                  {t.data === null ? 'Manual' : t.data && Object.keys(t.data).length > 0 ? 'Template' : '?'}
                </span>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-slate-800">{t.label}</p>
                  <p className="text-[10px] text-slate-400 leading-relaxed">{t.description}</p>
                </div>
                {isActive && <CheckCircle2 size={13} className="ml-auto shrink-0 text-blue-500" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Modal utama ─────────────────────────────────────────────────────────────
export default function SensorInputModal({ isOpen, onClose, machineId, onPredictionResult }) {
  const [selectedTemplate, setSelectedTemplate] = useState('manual');
  const [formData, setFormData]   = useState({ ...EMPTY_FORM });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [prediction, setPrediction]     = useState(null);
  const [error, setError]               = useState(null);
  const bodyRef = React.useRef(null);

  // Reset saat modal dibuka
  useEffect(() => {
    if (isOpen) {
      setSelectedTemplate('manual');
      setFormData({ ...EMPTY_FORM });
      setPrediction(null);
      setError(null);
    }
  }, [isOpen]);

  // Isi form saat template berubah
  const handleTemplateChange = (templateId) => {
    setSelectedTemplate(templateId);
    setPrediction(null);
    setError(null);
    const tpl = SENSOR_TEMPLATES.find(t => t.id === templateId);
    if (tpl?.data) {
      setFormData(toFormStrings(tpl.data));
    } else {
      setFormData({ ...EMPTY_FORM });
    }
  };

  const handleChange = (key, value) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const handleReset = () => {
    const tpl = SENSOR_TEMPLATES.find(t => t.id === selectedTemplate);
    if (tpl?.data) setFormData(toFormStrings(tpl.data));
    else setFormData({ ...EMPTY_FORM });
  };

  const handleClear = () => {
    setFormData({ ...EMPTY_FORM });
    setPrediction(null);
    setError(null);
  };

  const handleSubmit = async () => {
    const emptyKeys = ALL_KEYS.filter(k => formData[k] === '');
    if (emptyKeys.length > 0) {
      setError(`Harap isi semua field sensor. ${emptyKeys.length} field masih kosong.`);
      return;
    }
    if (!machineId) {
      setError('Aset belum siap. Tunggu sebentar lalu coba lagi.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const numeric = Object.fromEntries(ALL_KEYS.map(k => [k, parseFloat(formData[k])]));
      const payload = {
        machine_id:   machineId,
        noise_db:     numeric.noise_db,
        water_flow:   numeric.water_flow,
        air_flow:     numeric.air_flow,
        gaccx:        numeric.gaccx,
        outlet_temp:  numeric.outlet_temp,
      };

      const response = await api.post('/ml/sensor-data', payload);
      const pred = response.data.prediction;
      setPrediction(pred);
      if (onPredictionResult) onPredictionResult(pred);
      setTimeout(() => bodyRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 50);
    } catch {
      setError('Gagal mengirim data sensor. Pastikan backend berjalan.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const overallHealthy = (prediction?.overall_health_score ?? 1) >= 0.7;
  const hasTemplate = SENSOR_TEMPLATES.find(t => t.id === selectedTemplate)?.data !== null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="flex h-[94vh] w-full max-w-3xl flex-col rounded-xl bg-white shadow-2xl">

        {/* ── Header ─────────────────────────────────────────────────────── */}
        <div className="flex shrink-0 items-center justify-between border-b border-slate-100 px-6 py-4">
          <div className="flex items-center gap-2">
            <ClipboardList size={18} className="text-blue-600" />
            <h2 className="text-base font-bold text-slate-800">Input Data Sensor</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          >
            <X size={18} />
          </button>
        </div>

        {/* ── Scrollable body ─────────────────────────────────────────────── */}
        <div ref={bodyRef} className="flex-1 overflow-y-auto px-6 py-4 space-y-5">

          {/* Template selector */}
          <div>
            <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-slate-400">
              Pilih Template
            </label>
            <TemplateSelector selected={selectedTemplate} onChange={handleTemplateChange} />
          </div>

          {/* Error prediksi ML */}
          {prediction && prediction.ok === false && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-700">
              <p className="font-bold mb-1">Prediksi gagal:</p>
              <p className="font-mono break-all">{prediction.warning || 'Unknown error'}</p>
            </div>
          )}

          {/* Hasil prediksi */}
          {prediction && prediction.ok !== false && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-3">
              {/* Overall health header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {overallHealthy
                    ? <CheckCircle2 size={16} className="text-green-600" />
                    : <AlertTriangle size={16} className="text-red-600" />}
                  <span className="text-sm font-bold text-slate-800">Hasil Prediksi</span>
                </div>
                <span className="text-xs text-slate-500">
                  Health Score Keseluruhan:{' '}
                  <span className={`font-bold ${overallHealthy ? 'text-green-700' : 'text-red-700'}`}>
                    {Math.round((prediction.overall_health_score ?? 0) * 100)}%
                  </span>
                </span>
              </div>

              {/* Komponen bearing */}
              <div className="grid grid-cols-1 gap-2">
                {prediction.components && Object.entries(prediction.components).map(([key, comp]) => (
                  <ComponentBadge
                    key={key}
                    comp={{ ...comp, name: COMPONENT_LABELS[key] || key }}
                  />
                ))}
              </div>

              {/* Rekomendasi agregat */}
              {prediction.recommendation && (
                <div className={`rounded-md border px-3 py-2.5 text-xs leading-relaxed ${
                  overallHealthy
                    ? 'border-green-200 bg-green-50 text-green-800'
                    : 'border-orange-200 bg-orange-50 text-orange-800'
                }`}>
                  <span className="font-bold block mb-0.5">Rekomendasi</span>
                  {prediction.recommendation}
                </div>
              )}
            </div>
          )}

          {/* Error form */}
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-700">
              {error}
            </div>
          )}

          {/* Field groups */}
          {SENSOR_FIELD_GROUPS.map(({ group, fields }) => (
            <div key={group}>
              <h3 className="mb-2.5 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                {group}
              </h3>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {fields.map(({ key, label, unit }) => (
                  <div key={key}>
                    <label className="mb-1 block text-xs font-medium text-slate-600">
                      {label} <span className="font-normal text-slate-400">({unit})</span>
                    </label>
                    <input
                      type="number"
                      step="any"
                      value={formData[key]}
                      onChange={e => handleChange(key, e.target.value)}
                      className="w-full rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-800 placeholder-slate-300 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-100"
                      placeholder="0.000"
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* ── Footer ─────────────────────────────────────────────────────── */}
        <div className="flex shrink-0 items-center justify-between border-t border-slate-100 px-6 py-4">
          <div className="flex gap-2">
            {hasTemplate && (
              <button
                type="button"
                onClick={handleReset}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50"
              >
                <RotateCcw size={13} />
                Reset Template
              </button>
            )}
            <button
              type="button"
              onClick={handleClear}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50"
            >
              <Trash2 size={13} />
              Kosongkan
            </button>
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50"
            >
              Tutup
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {isSubmitting ? <Loader2 size={13} className="animate-spin" /> : <Send size={13} />}
              {isSubmitting ? 'Mengirim...' : 'Kirim Data Sensor'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
