# /cmms-backend/app/api/ml_routes.py
from flask import Blueprint, jsonify, request

from app.ml_service import CompressorPredictor, COMPONENTS
from app.ml_registry import get_predictor
from app.models import Asset, SensorData


ml_bp = Blueprint("ml_bp", __name__)
# Default predictor untuk endpoint yang tidak spesifik per-asset (compressor)
predictor = CompressorPredictor()


def _error_response(message, status_code=400, **extra):
    payload = {"error": message}
    payload.update(extra)
    return jsonify(payload), status_code


def _sensor_to_payload(sensor_data):
    payload = {}
    for column in predictor.feature_columns:
        payload[column] = getattr(sensor_data, column, None)
    payload["demo_mode"] = getattr(sensor_data, "demo_mode", None)
    return payload


def _run_prediction(payload):
    try:
        result = predictor.predict(payload)
    except FileNotFoundError as exc:
        return _error_response(str(exc), 503)
    except Exception as exc:
        return _error_response(str(exc), 500)

    if not result["ok"]:
        return _error_response(
            "Input fitur compressor belum lengkap atau tidak valid",
            400,
            missing_features=result["missing_features"],
            invalid_features=result["invalid_features"],
            required_features=result["required_features"],
        )

    return jsonify(result), 200


@ml_bp.route("/compressor/features", methods=["GET"])
def get_compressor_features():
    """Daftar fitur yang harus dikirim ke endpoint prediksi compressor."""
    try:
        return jsonify({
            "targets": COMPONENTS,
            "required_features": predictor.feature_columns,
            "model_ready": predictor.is_ready(),
            "missing_model_files": predictor.missing_model_files(),
        }), 200
    except Exception as exc:
        return _error_response(str(exc), 500)


@ml_bp.route("/compressor/predict", methods=["POST"])
def predict_compressor_payload():
    """Prediksi langsung dari payload 20 fitur compressor."""
    data = request.get_json(silent=True) or {}
    return _run_prediction(data)


@ml_bp.route("/predict/<machine_id>", methods=["POST"])
def predict_maintenance(machine_id):
    """Prediksi berdasarkan data sensor terbaru milik asset (model dipilih dari registry)."""
    asset = Asset.objects(machine_id=machine_id).first()
    if not asset:
        return _error_response("Asset not found", 404)

    # Pilih predictor berdasarkan machine_id asset
    asset_predictor = get_predictor(asset.machine_id)
    if not asset_predictor:
        return _error_response(
            f"Mesin '{asset.machine_id}' belum memiliki model ML yang terdaftar.", 404
        )

    latest_sensor = SensorData.objects(asset=asset).order_by("-timestamp").first()
    if not latest_sensor:
        return _error_response("No sensor data available for this asset", 404)

    # Bangun payload sesuai feature_columns predictor mesin ini
    payload = {col: getattr(latest_sensor, col, None) for col in asset_predictor.feature_columns}

    try:
        result = asset_predictor.predict(payload)
    except FileNotFoundError as exc:
        return _error_response(str(exc), 503)
    except Exception as exc:
        return _error_response(str(exc), 500)

    if not result["ok"]:
        return _error_response(
            "Input fitur belum lengkap atau tidak valid", 400,
            missing_features=result["missing_features"],
            invalid_features=result["invalid_features"],
            required_features=result["required_features"],
        )

    result.update({
        "asset_id": str(asset.id),
        "asset_name": asset.name,
        "sensor_data_id": str(latest_sensor.id),
        "sensor_timestamp": latest_sensor.timestamp.isoformat(),
    })
    return jsonify(result), 200


@ml_bp.route("/predictions", methods=["GET"])
def get_all_predictions():
    """Prediksi compressor untuk semua asset yang memiliki data sensor lengkap."""
    predictions = []
    skipped = []

    for asset in Asset.objects():
        latest_sensor = SensorData.objects(asset=asset).order_by("-timestamp").first()
        if not latest_sensor:
            skipped.append({
                "asset_id": str(asset.id),
                "asset_name": asset.name,
                "reason": "No sensor data",
            })
            continue

        try:
            result = predictor.predict(_sensor_to_payload(latest_sensor))
        except Exception as exc:
            skipped.append({
                "asset_id": str(asset.id),
                "asset_name": asset.name,
                "reason": str(exc),
            })
            continue

        if not result["ok"]:
            skipped.append({
                "asset_id": str(asset.id),
                "asset_name": asset.name,
                "reason": "Incomplete compressor features",
                "missing_features": result["missing_features"],
                "invalid_features": result["invalid_features"],
            })
            continue

        result.update({
            "asset_id": str(asset.id),
            "asset_name": asset.name,
            "sensor_data_id": str(latest_sensor.id),
            "sensor_timestamp": latest_sensor.timestamp.isoformat(),
        })
        predictions.append(result)

    return jsonify({
        "predictions": predictions,
        "skipped": skipped,
    }), 200


@ml_bp.route("/sensor-history/<machine_id>", methods=["GET"])
def get_sensor_history(machine_id):
    """Riwayat data sensor untuk satu asset, diurutkan terbaru dulu."""
    asset = Asset.objects(machine_id=machine_id).first()
    if not asset:
        return _error_response("Asset not found", 404)

    limit = min(int(request.args.get("limit", 50)), 200)
    records = SensorData.objects(asset=asset).order_by("-timestamp").limit(limit)

    SENSOR_FIELDS = [
        "noise_db", "water_flow", "air_flow", "gaccx", "outlet_temp",
    ]

    history = []
    available_fields = set()

    for r in records:
        row = {
            "id": str(r.id),
            "timestamp": r.timestamp.isoformat(),
            "health_score": r.health_score,
            "failure_probability": r.failure_probability,
            "predicted_failure_days": r.predicted_failure_days,
        }
        for f in SENSOR_FIELDS:
            val = getattr(r, f, None)
            if val is not None:
                row[f] = val
                available_fields.add(f)
        history.append(row)

    return jsonify({
        "machine_id": machine_id,
        "asset_name": asset.name,
        "total": len(history),
        "available_fields": sorted(available_fields),
        "history": history,
    }), 200


@ml_bp.route("/sensor-data", methods=["POST"])
def add_sensor_data():
    """Simpan data sensor dan jalankan prediksi jika 20 fitur compressor lengkap."""
    data = request.get_json(silent=True) or {}

    if "machine_id" not in data:
        return _error_response("Missing required field: machine_id", 400)

    asset = Asset.objects(machine_id=data["machine_id"]).first()
    if not asset:
        return _error_response("Asset not found", 404)

    sensor_data = SensorData(asset=asset)
    string_fields = [
        "demo_mode",
        "demo_stage",
        "demo_expected_risk",
        "demo_expected_action",
    ]

    for field in string_fields:
        if data.get(field) is not None:
            setattr(sensor_data, field, str(data[field]))

    numeric_fields = [
        "temperature",
        "vibration",
        "pressure",
        "current",
        "voltage",
        "rpm",
        "motor_power",
        "torque",
        "outlet_pressure_bar",
        "air_flow",
        "noise_db",
        "outlet_temp",
        "wpump_outlet_press",
        "water_inlet_temp",
        "water_outlet_temp",
        "wpump_power",
        "water_flow",
        "oilpump_power",
        "oil_tank_temp",
        "gaccx",
        "gaccy",
        "gaccz",
        "haccx",
        "haccy",
        "haccz",
    ]

    invalid_fields = []
    for field in numeric_fields:
        if field not in data or data[field] is None:
            continue
        try:
            setattr(sensor_data, field, float(data[field]))
        except (TypeError, ValueError):
            invalid_fields.append(field)

    if invalid_fields:
        return _error_response(
            "Ada field sensor yang bukan angka",
            400,
            invalid_fields=invalid_fields,
        )

    prediction = None
    try:
        payload = {field: data.get(field) for field in predictor.feature_columns}
        payload["demo_mode"] = data.get("demo_mode")
        result = predictor.predict(payload)
        if result["ok"]:
            sensor_data.health_score = result["health_score"]
            sensor_data.predicted_failure_days = result["predicted_days"]
            sensor_data.failure_probability = result["failure_probability"]
            prediction = result
    except Exception as exc:
        prediction = {
            "ok": False,
            "warning": f"Sensor data saved, but ML prediction failed: {exc}",
        }

    sensor_data.save()

    return jsonify({
        "message": "Sensor data added successfully",
        "sensor_data": sensor_data.to_json(),
        "prediction": prediction,
    }), 201
