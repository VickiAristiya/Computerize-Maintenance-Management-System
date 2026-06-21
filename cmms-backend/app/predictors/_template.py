"""
TEMPLATE predictor untuk mesin baru.

Cara pakai:
  1. Salin file ini → predictors/<nama_mesin>.py
  2. Ganti semua nilai placeholder (NAMA_MESIN, COMPONENTS, dst)
  3. Simpan model ke: machine-learning filtered data/<nama_mesin>/models/
  4. Daftarkan di ml_registry.py
"""
from datetime import datetime, timedelta
import warnings

import joblib
import numpy as np
import tensorflow as tf

from .base import BasePredictor


# ── Konfigurasi mesin (sesuaikan) ───────────────────────────────────────────

# Nama subfolder di machine-learning filtered data/
MACHINE_FOLDER = "nama_mesin"

# Komponen yang diprediksi (sesuaikan dengan komponen mesin)
COMPONENTS = ["komponen_1", "komponen_2"]

# Label kondisi per komponen {"fault": "label fault", "ok": "label normal"}
COMPONENT_LABELS = {
    "komponen_1": {"fault": "Fault", "ok": "Normal"},
    "komponen_2": {"fault": "Fault", "ok": "Normal"},
}

# Nama tampilan per komponen (untuk rekomendasi teks)
COMPONENT_NAME_ID = {
    "komponen_1": "Nama Komponen 1",
    "komponen_2": "Nama Komponen 2",
}

_RISK_ORDER = ["very_low", "low", "medium", "high", "critical"]

# ────────────────────────────────────────────────────────────────────────────


class NamaMesinPredictor(BasePredictor):
    """Predictor untuk mesin <NamaMesin>."""

    _bundles: dict = {}
    _extractors: dict = {}

    def __init__(self):
        # Otomatis menunjuk ke machine-learning filtered data/<MACHINE_FOLDER>/models/
        self.models_dir = self._ML_ROOT / MACHINE_FOLDER / "models"

    @property
    def feature_columns(self):
        self._ensure_loaded()
        return list(self._bundles[COMPONENTS[0]]["feature_columns"])

    def is_ready(self):
        return all(
            (self.models_dir / f"hybrid_model_{c}.pkl").exists()
            and (self.models_dir / f"dnn_extractor_{c}.keras").exists()
            for c in COMPONENTS
        )

    def missing_model_files(self):
        missing = []
        for c in COMPONENTS:
            for fname in [f"hybrid_model_{c}.pkl", f"dnn_extractor_{c}.keras"]:
                p = self.models_dir / fname
                if not p.exists():
                    missing.append(str(p))
        return missing

    def validate_payload(self, payload):
        self._ensure_loaded()
        missing = [col for col in self.feature_columns if col not in payload]
        invalid = []
        values = {}
        for col in self.feature_columns:
            if col not in payload:
                continue
            try:
                values[col] = float(payload[col])
            except (TypeError, ValueError):
                invalid.append(col)
        return values, missing, invalid

    def predict(self, payload):
        self._ensure_loaded()
        values, missing, invalid = self.validate_payload(payload)

        if missing or invalid:
            return {
                "ok": False,
                "missing_features": missing,
                "invalid_features": invalid,
                "required_features": self.feature_columns,
            }

        ordered = [values[col] for col in self.feature_columns]
        x = np.array([ordered], dtype=float)

        components = {}
        health_scores = []
        faulty_components = []

        for component in COMPONENTS:
            bundle = self._bundles[component]
            extractor = self._extractors[component]

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="X does not have valid feature names", category=UserWarning)
                scaled = bundle["scaler"].transform(x)

            latent = extractor.predict(scaled, verbose=0)
            svm = bundle["svm"]
            pred_value = int(svm.predict(latent)[0])
            proba = svm.predict_proba(latent)[0]
            fault_prob = float(proba[1])
            ok_prob = float(proba[0])

            labels = COMPONENT_LABELS[component]
            prediction = labels["fault"] if pred_value == 1 else labels["ok"]
            risk = self._build_component_risk(fault_prob)
            comp_health = 1 - fault_prob

            components[component] = {
                "prediction": prediction,
                "status": "Fault Detected" if pred_value == 1 else "Normal",
                "confidence": max(ok_prob, fault_prob),
                "probability": {labels["ok"]: ok_prob, labels["fault"]: fault_prob},
                "health_score": comp_health,
                "failure_probability": fault_prob,
                "predicted_days": risk["predicted_days"],
                "risk_level": risk["risk_level"],
                "priority": risk["priority"],
                "due_date": risk["due_date"],
            }
            health_scores.append(comp_health)
            if pred_value == 1:
                faulty_components.append(component)

        overall_health = sum(health_scores) / len(health_scores)
        worst = self._worst_risk(components)
        first_comp = components[COMPONENTS[0]]

        return {
            "ok": True,
            "prediction": first_comp["prediction"],
            "status": first_comp["status"],
            "confidence": first_comp["confidence"],
            "probability": first_comp["probability"],
            "health_score": first_comp["health_score"],
            "failure_probability": first_comp["failure_probability"],
            "predicted_days": worst["predicted_days"],
            "risk_level": worst["risk_level"],
            "priority": worst["priority"],
            "recommendation": self._build_recommendation(faulty_components, components),
            "due_date": worst["due_date"],
            "components": components,
            "overall_health_score": overall_health,
            "input_features": values,
        }

    def _ensure_loaded(self):
        if not self.is_ready():
            raise FileNotFoundError("Model files missing: " + ", ".join(self.missing_model_files()))

        cls = type(self)
        for component in COMPONENTS:
            if component not in cls._bundles:
                cls._bundles[component] = joblib.load(self.models_dir / f"hybrid_model_{component}.pkl")
            if component not in cls._extractors:
                cls._extractors[component] = tf.keras.models.load_model(
                    self.models_dir / f"dnn_extractor_{component}.keras"
                )
        self._bundles = cls._bundles
        self._extractors = cls._extractors

    def _build_component_risk(self, fault_prob):
        if fault_prob >= 0.8:
            risk_level, priority, days = "critical", "critical", 0
        elif fault_prob >= 0.5:
            risk_level, priority, days = "high", "high", 7
        elif fault_prob >= 0.3:
            risk_level, priority, days = "medium", "medium", 30
        elif fault_prob >= 0.1:
            risk_level, priority, days = "low", "low", 60
        else:
            risk_level, priority, days = "very_low", "low", 90
        return {"risk_level": risk_level, "priority": priority,
                "predicted_days": days,
                "due_date": (datetime.utcnow() + timedelta(days=days)).isoformat()}

    def _build_recommendation(self, faulty_components, components):
        if not faulty_components:
            return "Semua komponen dalam kondisi baik. Lanjutkan operasi dan jadwalkan maintenance rutin."
        names = [COMPONENT_NAME_ID.get(c, c) for c in faulty_components]
        label = " dan ".join(names) if len(names) <= 2 else f"{', '.join(names[:-1])}, dan {names[-1]}"
        worst_risk = max(
            (components[c]["risk_level"] for c in faulty_components),
            key=lambda r: _RISK_ORDER.index(r) if r in _RISK_ORDER else 0,
        )
        action = (
            "Hentikan operasi dan lakukan pemeriksaan segera." if worst_risk == "critical"
            else "Disarankan pemeriksaan dalam 7 hari ke depan." if worst_risk == "high"
            else "Disarankan pemeriksaan dalam 30 hari ke depan."
        )
        return f"Komponen {label} terindikasi fault. {action}"

    def _worst_risk(self, components):
        worst = max(
            components.values(),
            key=lambda c: _RISK_ORDER.index(c["risk_level"]) if c["risk_level"] in _RISK_ORDER else 0,
        )
        return {k: worst[k] for k in ("risk_level", "priority", "predicted_days", "due_date")}
