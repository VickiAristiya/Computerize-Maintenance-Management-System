"""
Penghalus (smoothing) health score hasil prediksi ML.

Masalah yang diselesaikan
-------------------------
Model hybrid DNN-SVM memutuskan per SATU titik data. Satu pembacaan sensor
yang melenceng (spike) bisa membuat fault probability langsung ~1.0, sehingga
health score jatuh dari 100% ke 0% hanya karena satu kali kirim data. Padahal
kondisi mesin nyata memburuk perlahan — yang berubah mendadak biasanya
sensor/transmisinya, bukan mesinnya.

Cara kerja (tiga lapis, semuanya di backend)
--------------------------------------------
  1. Filter median (window 3)
     Spike tunggal ditelan habis: satu pembacaan aneh yang diapit dua
     pembacaan normal tidak menggeser health score sama sekali.

  2. EMA / exponential moving average (alpha 0.3)
     Sisa perubahan diserap bertahap — health score bergerak mulus mendekati
     nilai model, bukan meloncat ke sana.

  3. Rate limiter
     Berapa pun besar lonjakannya, health score maksimal TURUN 10 poin dan
     NAIK 5 poin per pembacaan. Naik dibuat lebih pelan daripada turun supaya
     mesin yang sempat bermasalah tidak langsung dianggap sehat lagi.

Fault yang benar-benar persisten tetap sampai ke health score rendah — hanya
butuh beberapa pembacaan, dan penurunannya terlihat sebagai tren, bukan
sebagai satu garis vertikal.

Risk level, priority, predicted_days, status, dan rekomendasi DIHITUNG ULANG
dari health score yang sudah halus, supaya dashboard/notifikasi tetap
konsisten (tidak ada "health 95% tapi risiko critical") dan alert real-time
tidak meletup gara-gara satu spike. Nilai asli model tetap disimpan di
key raw_* untuk keperluan audit/perbandingan.

Parameter bisa diubah lewat env var tanpa menyentuh kode:
  HEALTH_SMOOTHING_ENABLED    1/0   (default 1; 0 = pakai nilai model apa adanya)
  HEALTH_SMOOTHING_ALPHA      0..1  (default 0.3)
  HEALTH_SMOOTHING_MAX_DROP   0..1  (default 0.10 = 10 poin per pembacaan)
  HEALTH_SMOOTHING_MAX_RISE   0..1  (default 0.05 = 5 poin per pembacaan)
  HEALTH_SMOOTHING_MEDIAN     ganjil(default 3; 1 = filter median dimatikan)
  HEALTH_SMOOTHING_STALE_MIN  menit (default 720; jeda data lebih lama dari ini
                                     mengosongkan riwayat filter median — health
                                     score terakhir tetap jadi titik awal)

Contoh untuk demo cepat (health turun 20 poin per pembacaan):
    $env:HEALTH_SMOOTHING_MAX_DROP = "0.2"
"""
import os
from datetime import datetime
from statistics import median

from app.predictors.base import RISK_ORDER

# Ambang label fault (status "Fault Detected") — sama dengan batas keputusan
# predict_proba model.
FAULT_THRESHOLD = 0.5

# Ambang komponen ikut disebut di teks rekomendasi — disamakan dengan ambang
# notifikasi predictive maintenance di dashboard (fault_prob > 0.3), supaya
# notifikasi yang muncul tidak berisi kalimat "kondisi baik".
WARN_THRESHOLD = 0.3


def _env_float(name, default, lo=0.0, hi=1.0):
    try:
        value = float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
    return min(hi, max(lo, value))


def _env_int(name, default, lo, hi):
    try:
        value = int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
    return min(hi, max(lo, value))


ENABLED = os.environ.get("HEALTH_SMOOTHING_ENABLED", "1").strip() not in ("0", "false", "False")
ALPHA = _env_float("HEALTH_SMOOTHING_ALPHA", 0.3, 0.01, 1.0)
MAX_DROP = _env_float("HEALTH_SMOOTHING_MAX_DROP", 0.10, 0.01, 1.0)
MAX_RISE = _env_float("HEALTH_SMOOTHING_MAX_RISE", 0.05, 0.01, 1.0)
MEDIAN_WINDOW = _env_int("HEALTH_SMOOTHING_MEDIAN", 3, 1, 9)
STALE_MINUTES = _env_int("HEALTH_SMOOTHING_STALE_MIN", 720, 1, 100000)


def _clamp01(value):
    return min(1.0, max(0.0, float(value)))


def _previous_state(previous, now):
    """State smoothing sebelumnya: (components, raw_history).

    Kalau jeda dari pembacaan terakhir terlalu lama (mesin mati/offline),
    riwayat filter median dikosongkan — pembacaan kemarin tidak relevan untuk
    menilai spike hari ini. Health score terakhir TETAP dipakai sebagai titik
    awal, supaya pembacaan pertama setelah jeda pun tidak bisa menjatuhkan
    health score sekaligus.
    """
    if previous is None:
        return {}, {}

    components = previous.components or {}
    history = previous.raw_history or {}

    computed_at = getattr(previous, "computed_at", None)
    if isinstance(computed_at, datetime):
        gap_minutes = (now - computed_at).total_seconds() / 60
        if gap_minutes < 0 or gap_minutes > STALE_MINUTES:
            return components, {}

    return components, history


def _component_labels(raw_component):
    """Label kelas (ok, fault) diambil dari key dict probability milik model."""
    labels = list((raw_component.get("probability") or {}).keys())
    ok_label = labels[0] if labels else "Ok"
    fault_label = labels[-1] if len(labels) > 1 else "Fault"
    return ok_label, fault_label


def _raw_health(raw_component):
    value = raw_component.get("health_score")
    if value is None:
        value = 1 - (raw_component.get("failure_probability") or 0)
    return _clamp01(value)


def _smooth_one(prev_health, history):
    """Satu komponen: median → EMA → rate limiter. Return health score halus.

    history berisi nilai health mentah terakhir (paling baru di posisi akhir).
    """
    filtered = median(history)

    # Pembacaan pertama (belum punya riwayat) — tidak ada yang bisa dihaluskan.
    if prev_health is None:
        return _clamp01(filtered)

    prev_health = _clamp01(prev_health)
    step = ALPHA * (filtered - prev_health)
    step = max(-MAX_DROP, min(MAX_RISE, step))
    return _clamp01(prev_health + step)


def _worst_risk(components):
    worst = max(
        components.values(),
        key=lambda c: RISK_ORDER.index(c["risk_level"])
        if c["risk_level"] in RISK_ORDER
        else 0,
    )
    return {k: worst[k] for k in ("risk_level", "priority", "predicted_days", "due_date")}


def smooth_prediction(prediction, previous, predictor, now=None):
    """Haluskan hasil predictor.predict() memakai riwayat pembacaan sebelumnya.

    prediction : dict hasil predict() dengan ok=True
    previous   : dokumen AssetHealthStatus milik asset ini (boleh None)
    predictor  : predictor mesin ybs — dipakai menghitung ulang risk & rekomendasi
    now        : waktu pembacaan ini (default: utcnow)

    Return (prediction_halus, raw_history_baru). raw_history_baru harus
    disimpan ke AssetHealthStatus supaya filter median punya bahan di
    pembacaan berikutnya.
    """
    raw_components = prediction.get("components") or {}
    if not ENABLED or not raw_components:
        return prediction, {}

    now = now or datetime.utcnow()
    prev_components, prev_history = _previous_state(previous, now)

    components = {}
    histories = {}
    healths = []
    faulty = []

    for name, raw in raw_components.items():
        raw_health = _raw_health(raw)

        # Riwayat nilai mentah (bukan yang sudah dihaluskan) untuk filter median.
        history = (list(prev_history.get(name) or []) + [raw_health])[-MEDIAN_WINDOW:]
        histories[name] = history

        prev = prev_components.get(name) or {}
        smoothed = _smooth_one(prev.get("health_score"), history)

        fault_prob = 1 - smoothed
        is_fault = fault_prob >= FAULT_THRESHOLD
        risk = predictor.build_risk(fault_prob)
        ok_label, fault_label = _component_labels(raw)

        components[name] = {
            **raw,
            # Status & label ikut nilai halus, bukan keputusan satu titik data.
            "prediction": fault_label if is_fault else ok_label,
            "status": "Fault Detected" if is_fault else "Normal",
            "health_score": smoothed,
            "failure_probability": fault_prob,
            "predicted_days": risk["predicted_days"],
            "risk_level": risk["risk_level"],
            "priority": risk["priority"],
            "due_date": risk["due_date"],
            # Nilai asli model — tetap disimpan untuk audit/perbandingan.
            "raw_health_score": raw_health,
            "raw_failure_probability": raw.get("failure_probability"),
            "raw_status": raw.get("status"),
            "smoothed": True,
        }
        healths.append(smoothed)
        if fault_prob >= WARN_THRESHOLD:
            faulty.append(name)

    first = components[next(iter(components))]
    worst = _worst_risk(components)

    result = {
        **prediction,
        "components": components,
        "prediction": first["prediction"],
        "status": first["status"],
        "health_score": first["health_score"],
        "failure_probability": first["failure_probability"],
        "predicted_days": worst["predicted_days"],
        "risk_level": worst["risk_level"],
        "priority": worst["priority"],
        "due_date": worst["due_date"],
        "overall_health_score": sum(healths) / len(healths),
        "recommendation": predictor.build_recommendation(faulty, components)
        or prediction.get("recommendation"),
        # Hasil mentah model, sebelum dihaluskan.
        "raw_health_score": prediction.get("health_score"),
        "raw_overall_health_score": prediction.get("overall_health_score"),
        "raw_failure_probability": prediction.get("failure_probability"),
        "raw_risk_level": prediction.get("risk_level"),
        "raw_status": prediction.get("status"),
        "smoothed": True,
    }
    return result, histories
