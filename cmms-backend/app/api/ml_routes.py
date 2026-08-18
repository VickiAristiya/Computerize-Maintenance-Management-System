# /cmms-backend/app/api/ml_routes.py
from flask import Blueprint, jsonify, request

from app import socketio
from app.health_smoothing import smooth_prediction
from app.ml_service import CompressorPredictor, COMPONENTS
from app.ml_registry import get_predictor, registry_field_aliases
from app.models import Asset, SensorData, AssetHealthStatus

# risk_level yang dianggap cukup penting untuk memicu alert real-time
ALERT_RISK_LEVELS = {"high", "critical"}


ml_bp = Blueprint("ml_bp", __name__)
# Default predictor untuk endpoint yang tidak spesifik per-asset (compressor)
predictor = CompressorPredictor()

# Field numerik bertipe eksplisit di SensorData (lih. models.py). Dipakai
# bersama oleh endpoint simpan (add_sensor_data) dan riwayat (get_sensor_history)
# supaya keduanya selalu sinkron.
NUMERIC_FIELDS = [
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
    "active_power_w",
    "current_a",
    "energy_kwh",
    "temp_c",
    "voltage_v",
    "tekanan_bar",
    "vx",
    "vy",
    "vz",
]

# Alias nama field: beberapa perangkat/simulator sensor mengirim nama field
# yang beda dari nama kolom canonical yang dipakai schema & model ML (mis.
# sensor Induksi mengirim "temp", padahal model dilatih dengan kolom "temp_c").
# key = nama canonical (dipakai schema/model), value = daftar nama alternatif.
FIELD_ALIASES = {
    "temp_c": ["temp"],
    # Sensor Forging mengirim tekanan hidrolik sebagai "pressure"/"tekanan",
    # sedangkan model dilatih dengan kolom "tekanan_bar" (dari CSV training).
    "tekanan_bar": ["tekanan", "pressure"],
}

# Mesin baru mendaftarkan aliasnya lewat MACHINES di ml_registry.py, supaya
# menambah mesin cukup menyentuh satu file.
for _canonical, _aliases in registry_field_aliases().items():
    FIELD_ALIASES.setdefault(_canonical, [])
    FIELD_ALIASES[_canonical].extend(
        a for a in _aliases if a not in FIELD_ALIASES[_canonical]
    )


def _apply_field_aliases(data):
    """Isi field canonical dari alias-nya kalau field canonical belum ada/None.

    Alias yang sudah dipakai dibuang dari payload supaya nilainya tidak
    tersimpan dua kali (mis. "pressure" + "tekanan_bar") dan tidak muncul
    sebagai dua kolom/grafik kembar di halaman Monitoring Sensor.
    """
    for canonical, aliases in FIELD_ALIASES.items():
        if data.get(canonical) is not None:
            continue
        for alias in aliases:
            if data.get(alias) is not None:
                data[canonical] = data.pop(alias)
                break


class _PreOverrideView:
    """Kondisi kesehatan mesin SEBELUM health score-nya di-override mode demo.

    Dipakai sebagai acuan smoothing saat slider demo sedang menyala. Tanpa ini,
    pembacaan sensor yang masuk akan dihaluskan terhadap angka slider — health
    score pada riwayat sensor jadi ikut tertarik ke nilai buatan, padahal
    riwayat itu harus tetap murni hasil model.

    raw_history sengaja diambil apa adanya dari dokumen aslinya: mode demo tidak
    pernah menyentuh field itu, jadi isinya masih riwayat pembacaan sensor asli.
    """

    def __init__(self, status):
        self.components = (status.pre_override or {}).get("components") or {}
        self.raw_history = status.raw_history or {}
        self.computed_at = status.computed_at


def _error_response(message, status_code=400, **extra):
    payload = {"error": message}
    payload.update(extra)
    return jsonify(payload), status_code


def _sensor_value(sensor_data, column):
    """Ambil nilai satu fitur dari SensorData.

    Field mesin baru belum tentu punya kolom resmi di models.py — nilainya
    tersimpan di raw_readings. Helper ini menutup kedua kasus, sehingga model
    mesin baru bisa dipakai tanpa menambah field di SensorData.
    """
    value = getattr(sensor_data, column, None)
    if value is None:
        value = (sensor_data.raw_readings or {}).get(column)
    return value


def _sensor_to_payload(sensor_data):
    payload = {}
    for column in predictor.feature_columns:
        payload[column] = _sensor_value(sensor_data, column)
    return payload


def _get_latest_valid_sensor(asset, feature_columns=None):
    """Cari sensor data terbaru yang memiliki semua feature lengkap (tidak None)."""
    cols = feature_columns if feature_columns is not None else predictor.feature_columns
    for sensor in SensorData.objects(asset=asset).order_by("-timestamp").limit(50):
        if all(_sensor_value(sensor, col) is not None for col in cols):
            return sensor
    return None


def _apply_smoothed_snapshot(result, asset, latest_sensor):
    """Ganti angka hasil model dengan snapshot health yang sudah dihaluskan.

    Endpoint prediksi read-only (mis. /predict/<machine_id>) menghitung ulang
    model dari satu pembacaan sensor terakhir — kalau ditampilkan apa adanya,
    angkanya bisa berbeda jauh dari dashboard yang memakai nilai halus. Snapshot
    AssetHealthStatus sudah berisi hasil smoothing untuk pembacaan yang sama,
    jadi dipakai kembali di sini (tanpa mengubah state smoothing).
    """
    status = AssetHealthStatus.objects(asset=asset).first()
    if not status or status.health_score is None:
        return result

    # Snapshot lebih tua dari data sensor yang dipakai di sini (mis. data lama
    # yang belum sempat diprediksi) — biarkan hasil model apa adanya.
    if status.computed_at and latest_sensor.timestamp and status.computed_at < latest_sensor.timestamp:
        return result

    components = status.components or {}
    first = next(iter(components.values()), {})

    result.update({
        "raw_health_score": result.get("health_score"),
        "raw_overall_health_score": result.get("overall_health_score"),
        "raw_failure_probability": result.get("failure_probability"),
        "raw_risk_level": result.get("risk_level"),
        "raw_status": result.get("status"),
        "health_score": status.health_score,
        "overall_health_score": status.overall_health_score,
        "failure_probability": status.failure_probability,
        "predicted_days": status.predicted_days,
        "risk_level": status.risk_level,
        "priority": status.priority,
        "due_date": status.due_date,
        "recommendation": status.recommendation or result.get("recommendation"),
        "components": components or result.get("components"),
        "smoothed": True,
    })
    if first.get("status"):
        result["status"] = first["status"]
        result["prediction"] = first.get("prediction", result.get("prediction"))

    return result


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

    latest_sensor = _get_latest_valid_sensor(asset, asset_predictor.feature_columns)
    if not latest_sensor:
        return _error_response("No complete sensor data available for this asset", 404)

    # Bangun payload sesuai feature_columns predictor mesin ini
    payload = {col: _sensor_value(latest_sensor, col) for col in asset_predictor.feature_columns}

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

    result = _apply_smoothed_snapshot(result, asset, latest_sensor)
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
        latest_sensor = _get_latest_valid_sensor(asset)
        if not latest_sensor:
            skipped.append({
                "asset_id": str(asset.id),
                "asset_name": asset.name,
                "reason": "No complete sensor data",
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


@ml_bp.route("/sensor-assets", methods=["GET"])
def get_assets_with_sensor_data():
    """Daftar asset_id yang punya minimal satu data sensor tersimpan, terlepas
    dari lengkap/tidaknya fitur untuk model ML tertentu. Dipakai front-end untuk
    menampilkan tombol 'Monitoring Sensor' pada mesin yang belum punya model ML
    terdaftar (mis. forging) tapi datanya sudah masuk."""
    asset_ids = [
        str(asset.id) for asset in Asset.objects()
        if SensorData.objects(asset=asset).first() is not None
    ]
    return jsonify({"asset_ids": asset_ids}), 200


@ml_bp.route("/sensor-history/<machine_id>", methods=["GET"])
def get_sensor_history(machine_id):
    """Riwayat data sensor untuk satu asset, diurutkan terbaru dulu."""
    asset = Asset.objects(machine_id=machine_id).first()
    if not asset:
        return _error_response("Asset not found", 404)

    raw_limit = request.args.get("limit", "50")
    query = SensorData.objects(asset=asset).order_by("-timestamp")
    if raw_limit == "all":
        # Dipakai tombol "Export Semua" — tanpa limit, ambil seluruh riwayat asset ini.
        records = query
    else:
        records = query.limit(min(int(raw_limit), 200))

    history = []
    available_fields = set()

    for r in records:
        row = {
            "id": str(r.id),
            "timestamp": r.timestamp.isoformat(),
            "health_score": r.health_score,
            "raw_health_score": r.raw_health_score,
            "failure_probability": r.failure_probability,
            "predicted_failure_days": r.predicted_failure_days,
        }
        # Field bertipe eksplisit (temperature, gaccx, dst.)
        for f in NUMERIC_FIELDS:
            val = getattr(r, f, None)
            if val is not None:
                row[f] = val
                available_fields.add(f)
        # Field mesin lain yang belum punya kolom resmi, ditampung raw_readings
        for f, val in (r.raw_readings or {}).items():
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

    _apply_field_aliases(data)

    asset = Asset.objects(machine_id=data["machine_id"]).first()
    if not asset:
        return _error_response("Asset not found", 404)

    sensor_data = SensorData(asset=asset)

    invalid_fields = []
    for field in NUMERIC_FIELDS:
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

    known_fields = {"machine_id", *NUMERIC_FIELDS}
    raw_readings = {
        field: value
        for field, value in data.items()
        if field not in known_fields and value is not None
    }
    if raw_readings:
        sensor_data.raw_readings = raw_readings

    # Pilih predictor sesuai machine_id asset (bukan selalu compressor) —
    # None kalau mesin ini belum punya model ML terdaftar (mis. forging).
    prediction = None
    raw_history = {}
    previous_status = AssetHealthStatus.objects(asset=asset).first()

    # Mode demo sedang aktif? Selama slider menyala, health score mesin ini
    # dikunci pada nilai slider — data sensor yang masuk tetap DISIMPAN dan
    # tetap diprediksi (riwayat sensor jujur apa adanya), tapi tidak boleh
    # menimpa snapshot yang dibaca dashboard. Tanpa penguncian ini, sensor yang
    # mengirim tiap beberapa detik akan menghapus nilai slider seketika.
    demo_override_active = bool(previous_status and previous_status.overridden)

    # Pembacaan ini dihaluskan terhadap kondisi SEBELUM override, bukan terhadap
    # angka slider — supaya health score pada riwayat sensor tetap mencerminkan
    # model, tidak ikut tertarik ke nilai buatan.
    smoothing_base = previous_status
    if demo_override_active:
        smoothing_base = _PreOverrideView(previous_status)

    asset_predictor = get_predictor(asset.machine_id)
    if asset_predictor:
        try:
            payload = {field: data.get(field) for field in asset_predictor.feature_columns}
            result = asset_predictor.predict(payload)
            if result["ok"]:
                # Haluskan dulu terhadap riwayat pembacaan sebelumnya, supaya
                # satu spike sensor tidak menjatuhkan health score ke 0 dan
                # tidak memicu alert palsu (lih. app/health_smoothing.py).
                result, raw_history = smooth_prediction(
                    result,
                    smoothing_base,
                    asset_predictor,
                    now=sensor_data.timestamp,
                )
                sensor_data.health_score = result["health_score"]
                sensor_data.raw_health_score = result.get("raw_health_score")
                sensor_data.predicted_failure_days = result["predicted_days"]
                sensor_data.failure_probability = result["failure_probability"]
                prediction = result
        except Exception as exc:
            prediction = {
                "ok": False,
                "warning": f"Sensor data saved, but ML prediction failed: {exc}",
            }

    sensor_data.save()

    # --- Simpan snapshot kesehatan asset (dipakai dashboard/notifikasi) ---
    # Prediksi di atas sudah dihitung sekali di sini; simpan hasilnya supaya
    # endpoint dashboard tinggal baca, tidak perlu predictor.predict() lagi.
    if prediction and prediction.get("ok") and not demo_override_active:
        AssetHealthStatus.objects(asset=asset).update_one(
            set__asset=asset,
            set__machine_id=asset.machine_id,
            set__asset_name=asset.name,
            set__overall_health_score=prediction.get("overall_health_score"),
            set__health_score=prediction.get("health_score"),
            set__failure_probability=prediction.get("failure_probability"),
            set__predicted_days=prediction.get("predicted_days"),
            set__risk_level=prediction.get("risk_level"),
            set__priority=prediction.get("priority"),
            set__recommendation=prediction.get("recommendation"),
            set__due_date=prediction.get("due_date"),
            set__components=prediction.get("components") or {},
            set__raw_history=raw_history or {},
            set__computed_at=sensor_data.timestamp,
            upsert=True,
        )

    # --- Push real-time ke frontend, agar dashboard/monitoring tidak perlu di-refresh manual ---
    update_payload = {
        "asset_id": str(asset.id),
        "machine_id": asset.machine_id,
        "asset_name": asset.name,
        "timestamp": sensor_data.timestamp.isoformat(),
        "health_score": sensor_data.health_score,
        "risk_level": prediction.get("risk_level") if prediction else None,
    }
    # Selama mode demo aktif, dashboard sedang dikendalikan slider. Mengirim
    # angka dari sensor ke sana hanya akan membuat tampilan berkedip-kedip
    # antara nilai slider dan nilai model, jadi push-nya ditahan dulu.
    if not demo_override_active:
        socketio.emit("sensor_data_update", update_payload)

        if prediction and prediction.get("ok") and prediction.get("risk_level") in ALERT_RISK_LEVELS:
            socketio.emit("machine_alert", {
                **update_payload,
                "failure_probability": prediction.get("failure_probability"),
                "predicted_days": prediction.get("predicted_days"),
                "recommendation": prediction.get("recommendation"),
            })

    return jsonify({
        "message": (
            "Sensor data added, tetapi health score mesin sedang dikunci mode demo"
            if demo_override_active else "Sensor data added successfully"
        ),
        "demo_override_active": demo_override_active,
        "sensor_data": sensor_data.to_json(),
        "prediction": prediction,
    }), 201
