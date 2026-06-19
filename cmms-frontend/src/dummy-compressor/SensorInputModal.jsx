import React, { useEffect, useState } from 'react';
import api from '../services/api';
import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  RotateCcw,
  Send,
  Trash2,
  X,
} from 'lucide-react';
import { SENSOR_FIELD_GROUPS } from './compressorSensorGenerator.js';

const ALL_KEYS = SENSOR_FIELD_GROUPS.flatMap((g) => g.fields.map((f) => f.key));

const EMPTY_FORM = Object.fromEntries(ALL_KEYS.map((k) => [k, '']));

function stringifyValues(data) {
  return Object.fromEntries(ALL_KEYS.map((k) => [k, data[k] !== undefined ? String(data[k]) : '']));
}

const RISK_COLORS = {
  critical: 'text-rose-700 bg-rose-50 border-rose-200',
  high: 'text-red-700 bg-red-50 border-red-200',
  medium: 'text-orange-700 bg-orange-50 border-orange-200',
  low: 'text-yellow-700 bg-yellow-50 border-yellow-200',
  very_low: 'text-green-700 bg-green-50 border-green-200',
};

export default function SensorInputModal({
  isOpen,
  onClose,
  initialData,
  mode,
  modeLabel,
  assetId,
  onPredictionResult,
}) {
  const [formData, setFormData] = useState({ ...EMPTY_FORM });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setFormData(initialData ? stringifyValues(initialData) : { ...EMPTY_FORM });
      setPrediction(null);
      setError(null);
    }
  }, [isOpen, initialData]);

  const handleChange = (key, value) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const handleReset = () => {
    if (initialData) setFormData(stringifyValues(initialData));
  };

  const handleClear = () => {
    setFormData({ ...EMPTY_FORM });
    setPrediction(null);
    setError(null);
  };

  const handleSubmit = async () => {
    const emptyKeys = ALL_KEYS.filter((k) => formData[k] === '');
    if (emptyKeys.length > 0) {
      setError(`Harap isi semua field sensor. ${emptyKeys.length} field masih kosong.`);
      return;
    }

    if (!assetId) {
      setError('Aset belum siap. Tunggu sebentar lalu coba lagi.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const numeric = Object.fromEntries(ALL_KEYS.map((k) => [k, parseFloat(formData[k])]));
      const payload = {
        asset_id: assetId,
        demo_mode: mode || 'manual',
        demo_stage: modeLabel || 'Manual Input',
        demo_expected_risk: 'manual',
        demo_expected_action: 'manual',
        temperature: numeric.outlet_temp,
        vibration: numeric.gaccz,
        pressure: numeric.outlet_pressure_bar,
        ...numeric,
      };

      const response = await api.post('/ml/sensor-data', payload);
      const pred = response.data.prediction;
      setPrediction(pred);
      if (onPredictionResult) onPredictionResult(pred);
    } catch (err) {
      setError('Gagal mengirim data sensor. Pastikan backend berjalan.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const riskColor = prediction ? (RISK_COLORS[prediction.risk_level] || RISK_COLORS.very_low) : '';
  const isOk = prediction?.prediction === 'Ok';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="flex h-[92vh] w-full max-w-3xl flex-col rounded-xl bg-white shadow-2xl">

        {/* Header */}
        <div className="flex shrink-0 items-center justify-between border-b border-slate-100 px-6 py-4">
          <div>
            <h2 className="text-base font-bold text-slate-800">Input Data Sensor</h2>
            <p className="text-xs text-slate-500">{modeLabel || 'Input Manual'}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          >
            <X size={18} />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-5">

          {/* Prediction result */}
          {prediction && (
            <div className={`rounded-lg border p-4 ${isOk ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
              <div className="mb-2 flex items-center gap-2">
                {isOk
                  ? <CheckCircle2 size={16} className="text-green-600" />
                  : <AlertTriangle size={16} className="text-red-600" />}
                <span className="text-sm font-bold text-slate-800">Hasil Prediksi</span>
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
                <div>
                  <span className="text-slate-500">Status: </span>
                  <span className="font-semibold">{prediction.prediction}</span>
                </div>
                <div>
                  <span className="text-slate-500">Risk Level: </span>
                  <span className={`rounded px-1.5 py-0.5 text-[11px] font-bold border ${riskColor}`}>
                    {prediction.risk_level}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">Prob. Kegagalan: </span>
                  <span className="font-semibold">{Math.round(prediction.failure_probability * 100)}%</span>
                </div>
                <div>
                  <span className="text-slate-500">Health Score: </span>
                  <span className="font-semibold">{Math.round((prediction.health_score ?? 0) * 100)}%</span>
                </div>
                {prediction.predicted_days !== undefined && (
                  <div className="col-span-2">
                    <span className="text-slate-500">Prediksi Kegagalan: </span>
                    <span className="font-semibold">
                      {prediction.predicted_days === 0 ? 'Segera' : `${prediction.predicted_days} hari`}
                    </span>
                  </div>
                )}
                {prediction.recommendation && (
                  <div className="col-span-2 mt-1 rounded bg-white/70 px-3 py-2 text-slate-600 italic">
                    {prediction.recommendation}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Error */}
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
                      {label}{' '}
                      <span className="font-normal text-slate-400">({unit})</span>
                    </label>
                    <input
                      type="number"
                      step="any"
                      value={formData[key]}
                      onChange={(e) => handleChange(key, e.target.value)}
                      className="w-full rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-800 placeholder-slate-300 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-100"
                      placeholder="0.000"
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="flex shrink-0 items-center justify-between border-t border-slate-100 px-6 py-4">
          <div className="flex gap-2">
            {initialData && (
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
              {isSubmitting
                ? <Loader2 size={13} className="animate-spin" />
                : <Send size={13} />}
              {isSubmitting ? 'Mengirim...' : 'Kirim Data Sensor'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
