from datetime import datetime, timedelta
from pathlib import Path
import warnings

import joblib
import numpy as np
import tensorflow as tf


DEMO_RISK_OVERRIDES = {
    "maintenance_low": {
        "failure_probability": 0.2,
        "prediction": "Ok",
    },
    "maintenance_medium": {
        "failure_probability": 0.4,
        "prediction": "Noisy",
    },
    "maintenance_high": {
        "failure_probability": 0.65,
        "prediction": "Noisy",
    },
    "maintenance_critical": {
        "failure_probability": 0.85,
        "prediction": "Noisy",
    },
}


class CompressorPredictor:
    """Loads the trained compressor hybrid DNN-SVM model and runs inference."""

    _bundle = None
    _feature_extractor = None

    def __init__(self):
        backend_dir = Path(__file__).resolve().parents[1]
        project_dir = backend_dir.parent
        self.models_dir = project_dir / "machine-learning" / "models"
        self.bundle_path = self.models_dir / "hybrid_model.pkl"
        self.feature_extractor_path = self.models_dir / "dnn_feature_extractor.keras"

    @property
    def feature_columns(self):
        self._ensure_loaded()
        return list(self._bundle["feature_columns"])

    def is_ready(self):
        return self.bundle_path.exists() and self.feature_extractor_path.exists()

    def missing_model_files(self):
        missing = []
        if not self.bundle_path.exists():
            missing.append(str(self.bundle_path))
        if not self.feature_extractor_path.exists():
            missing.append(str(self.feature_extractor_path))
        return missing

    def validate_payload(self, payload):
        self._ensure_loaded()
        missing = [column for column in self.feature_columns if column not in payload]
        invalid = []

        values = {}
        for column in self.feature_columns:
            if column not in payload:
                continue
            try:
                values[column] = float(payload[column])
            except (TypeError, ValueError):
                invalid.append(column)

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

        ordered_values = [values[column] for column in self.feature_columns]
        x = np.array([ordered_values], dtype=float)

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="X does not have valid feature names",
                category=UserWarning,
            )
            scaled = self._bundle["scaler"].transform(x)
        latent = self._feature_extractor.predict(scaled, verbose=0)

        svm = self._bundle["svm"]
        prediction_value = int(svm.predict(latent)[0])
        probabilities = svm.predict_proba(latent)[0]
        noisy_probability = float(probabilities[1])
        ok_probability = float(probabilities[0])

        prediction = "Noisy" if prediction_value == 1 else "Ok"
        demo_mode = payload.get("demo_mode")
        if demo_mode in DEMO_RISK_OVERRIDES:
            demo_override = DEMO_RISK_OVERRIDES[demo_mode]
            noisy_probability = demo_override["failure_probability"]
            ok_probability = 1 - noisy_probability
            prediction = demo_override["prediction"]

        recommendation = self._build_recommendation(noisy_probability, prediction)

        return {
            "ok": True,
            "demo_mode": demo_mode,
            "target": self._bundle.get("target_column", "bearings"),
            "prediction": prediction,
            "status": "Fault Detected" if prediction == "Noisy" else "Normal",
            "confidence": max(ok_probability, noisy_probability),
            "probability": {
                "Ok": ok_probability,
                "Noisy": noisy_probability,
            },
            "health_score": 1 - noisy_probability,
            "failure_probability": noisy_probability,
            "predicted_days": recommendation["predicted_days"],
            "risk_level": recommendation["risk_level"],
            "priority": recommendation["priority"],
            "recommendation": recommendation["message"],
            "due_date": recommendation["due_date"],
            "input_features": values,
        }

    def _ensure_loaded(self):
        if not self.is_ready():
            raise FileNotFoundError(
                "Compressor model files are missing: "
                + ", ".join(self.missing_model_files())
            )

        if CompressorPredictor._bundle is None:
            CompressorPredictor._bundle = joblib.load(self.bundle_path)

        if CompressorPredictor._feature_extractor is None:
            CompressorPredictor._feature_extractor = tf.keras.models.load_model(
                self.feature_extractor_path
            )

        self._bundle = CompressorPredictor._bundle
        self._feature_extractor = CompressorPredictor._feature_extractor

    def _build_recommendation(self, noisy_probability, prediction):
        if noisy_probability >= 0.8:
            risk_level = "critical"
            priority = "critical"
            days = 0
            message = (
                "Bearing terindikasi Noisy. Lakukan pemeriksaan dan maintenance segera."
            )
        elif noisy_probability >= 0.5:
            risk_level = "high"
            priority = "high"
            days = 7
            message = (
                "Mesin masih dapat beroperasi, tetapi risiko bearing tinggi. "
                "Disarankan pemeriksaan dalam 7 hari ke depan."
            )
        elif noisy_probability >= 0.3:
            risk_level = "medium"
            priority = "medium"
            days = 30
            message = (
                "Mesin masih berfungsi dengan baik, tetapi ada indikasi risiko sedang. "
                "Disarankan pemeriksaan dalam 30 hari ke depan."
            )
        elif noisy_probability >= 0.1:
            risk_level = "low"
            priority = "low"
            days = 60
            message = (
                "Mesin dalam kondisi normal dengan risiko rendah. "
                "Disarankan pemeriksaan rutin dalam 60 hari ke depan."
            )
        else:
            risk_level = "very_low"
            priority = "low"
            days = 90
            message = (
                "Mesin dalam kondisi baik. Lanjutkan operasi dan lakukan maintenance "
                "rutin dalam 90 hari ke depan."
            )

        due_date = (datetime.utcnow() + timedelta(days=days)).isoformat()
        return {
            "risk_level": risk_level,
            "priority": priority,
            "predicted_days": days,
            "due_date": due_date,
            "message": message,
        }
