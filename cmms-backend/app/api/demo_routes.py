# /cmms-backend/app/api/demo_routes.py
"""
Mode demo: override health score sebuah mesin secara manual.

Untuk apa
---------
Saat presentasi/sidang, menurunkan health score lewat jalur normal butuh
mengirim beberapa pembacaan sensor berturut-turut — health score sengaja
dihaluskan (lih. app/health_smoothing.py) supaya tidak meloncat. Itu benar
untuk operasi nyata, tapi merepotkan kalau tujuannya sekadar memperagakan
"health turun -> notifikasi muncul" di depan penguji.

Endpoint di sini memungkinkan slider di web simulasi menyetel health score
sebuah mesin secara langsung, seperti mengatur volume.

Yang WAJIB dipahami
-------------------
Angka yang dihasilkan endpoint ini BUKAN hasil model ML. Ini jalur peragaan
tampilan, bukan jalur prediksi. Karena itu:

  - snapshot yang di-override ditandai `overridden = True`, sehingga selalu
    bisa dibedakan dari hasil model;
  - isi snapshot sebelum di-override disimpan di `pre_override` dan
    dikembalikan utuh saat mode demo dimatikan;
  - endpoint ini tidak pernah membuat baris SensorData baru — nilai sensor
    tidak dikarang;
  - selama override aktif, data sensor yang masuk TIDAK menimpa health score
    (lih. ml_routes.add_sensor_data): snapshot dashboard dikunci pada nilai
    slider. Kalau tidak, sensor yang mengirim tiap beberapa detik akan
    menghapus nilai slider seketika.
  - baris sensor yang masuk selama override ikut memakai nilai slider pada
    kolom health_score, supaya kurva di halaman Monitoring Sensor bergerak
    seirama dengan dashboard. Hasil model yang sebenarnya untuk pembacaan itu
    TETAP tersimpan di raw_health_score, jadi kondisi asli mesin tidak hilang
    dan selisih keduanya bisa diperiksa kapan saja.

Semua efek di atas berhenti begitu mode demo dimatikan: snapshot dikembalikan
ke kondisi semula dan baris sensor berikutnya kembali memakai nilai model.

Sakelar on/off ada di web simulasi, bukan di sini — backend hanya menyediakan
endpointnya. Untuk mematikan fitur ini sepenuhnya di server, set env var
DEMO_MODE_ENABLED=0 (default: aktif).

Endpoint
--------
  GET    /api/demo/health-override/<machine_id>   status override saat ini
  POST   /api/demo/health-override                {machine_id, health_score}
  DELETE /api/demo/health-override/<machine_id>   matikan, kembalikan ke semula
"""
import os
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from app import socketio
from app.ml_registry import get_predictor
from app.models import Asset, AssetHealthStatus

demo_bp = Blueprint("demo_bp", __name__)

ENABLED = os.environ.get("DEMO_MODE_ENABLED", "1").strip() not in ("0", "false", "False")

ALERT_RISK_LEVELS = {"high", "critical"}

# Field snapshot yang ikut disimpan/dikembalikan saat override dinyalakan/dimatikan
SNAPSHOT_FIELDS = (
    "overall_health_score", "health_score", "failure_probability",
    "predicted_days", "risk_level", "priority", "recommendation",
    "due_date", "components",
)


def _error(message, status_code=400, **extra):
    return jsonify({"error": message, **extra}), status_code


def _components_of(predictor):
    """Daftar komponen sebuah predictor, tanpa memuat file model."""
    comps = getattr(predictor, "components", None)
    if comps:
        return list(comps)
    module = __import__(type(predictor).__module__, fromlist=["COMPONENTS"])
    return list(getattr(module, "COMPONENTS", None) or ["status"])


def _build_risk(predictor, fault_prob):
    """Risk level dari fault probability — pakai aturan predictor mesin ybs."""
    if predictor is not None:
        try:
            return predictor.build_risk(fault_prob)
        except Exception:
            pass
    # Fallback: ambang yang sama dengan GenericHybridPredictor
    if fault_prob >= 0.8:
        risk, priority, days = "critical", "critical", 0
    elif fault_prob >= 0.5:
        risk, priority, days = "high", "high", 7
    elif fault_prob >= 0.3:
        risk, priority, days = "medium", "medium", 30
    elif fault_prob >= 0.1:
        risk, priority, days = "low", "low", 60
    else:
        risk, priority, days = "very_low", "low", 90
    return {
        "risk_level": risk,
        "priority": priority,
        "predicted_days": days,
        "due_date": (datetime.utcnow() + timedelta(days=days)).isoformat(),
    }


def _snapshot_dict(status):
    """Isi snapshot saat ini, untuk disimpan sebelum di-override."""
    return {field: getattr(status, field, None) for field in SNAPSHOT_FIELDS}


@demo_bp.route("/health-override/<machine_id>", methods=["GET"])
def get_override(machine_id):
    asset = Asset.objects(machine_id=machine_id).first()
    if not asset:
        return _error(f"Aset dengan machine_id '{machine_id}' tidak ditemukan", 404)

    status = AssetHealthStatus.objects(asset=asset).first()
    return jsonify({
        "demo_mode_enabled": ENABLED,
        "machine_id": machine_id,
        "asset_name": asset.name,
        "overridden": bool(status and status.overridden),
        "health_score": status.health_score if status else None,
        "risk_level": status.risk_level if status else None,
        "recommendation": status.recommendation if status else None,
    }), 200


@demo_bp.route("/health-override", methods=["POST"])
def set_override():
    if not ENABLED:
        return _error("Mode demo dimatikan di server (DEMO_MODE_ENABLED=0)", 403)

    data = request.get_json(silent=True) or {}

    machine_id = str(data.get("machine_id") or "").strip()
    if not machine_id:
        return _error("Field 'machine_id' wajib diisi")

    try:
        health_score = float(data["health_score"])
    except (KeyError, TypeError, ValueError):
        return _error("Field 'health_score' wajib berupa angka 0..1")

    if not 0.0 <= health_score <= 1.0:
        return _error("'health_score' harus berada di rentang 0..1")

    asset = Asset.objects(machine_id=machine_id).first()
    if not asset:
        return _error(f"Aset dengan machine_id '{machine_id}' tidak ditemukan", 404)

    predictor = get_predictor(machine_id)
    fault_prob = 1.0 - health_score
    risk = _build_risk(predictor, fault_prob)
    is_fault = fault_prob >= 0.5

    components = {}
    faulty = []
    for name in (_components_of(predictor) if predictor else ["status"]):
        components[name] = {
            "prediction": "Fault" if is_fault else "Ok",
            "status": "Fault Detected" if is_fault else "Normal",
            "confidence": max(health_score, fault_prob),
            "probability": {"Ok": health_score, "Fault": fault_prob},
            "health_score": health_score,
            "failure_probability": fault_prob,
            "predicted_days": risk["predicted_days"],
            "risk_level": risk["risk_level"],
            "priority": risk["priority"],
            "due_date": risk["due_date"],
            # Penanda: nilai ini disetel manual, bukan keluaran model.
            "overridden": True,
        }
        # Ambang yang sama dengan notifikasi predictive maintenance dashboard
        if fault_prob > 0.3:
            faulty.append(name)

    recommendation = ""
    if predictor is not None:
        try:
            recommendation = predictor.build_recommendation(faulty, components) or ""
        except Exception:
            recommendation = ""
    if not recommendation:
        recommendation = (
            f"{asset.name} terindikasi fault — lakukan pemeriksaan."
            if faulty else f"{asset.name} dalam kondisi baik."
        )

    status = AssetHealthStatus.objects(asset=asset).first()

    # Simpan kondisi sebelum override HANYA saat pertama kali dinyalakan,
    # supaya menggeser slider berkali-kali tidak menimpa cadangan aslinya.
    pre_override = {}
    if status is not None and not status.overridden:
        pre_override = _snapshot_dict(status)
    elif status is not None:
        pre_override = status.pre_override or {}

    AssetHealthStatus.objects(asset=asset).update_one(
        set__asset=asset,
        set__machine_id=asset.machine_id,
        set__asset_name=asset.name,
        set__overall_health_score=health_score,
        set__health_score=health_score,
        set__failure_probability=fault_prob,
        set__predicted_days=risk["predicted_days"],
        set__risk_level=risk["risk_level"],
        set__priority=risk["priority"],
        set__recommendation=recommendation,
        set__due_date=risk["due_date"],
        set__components=components,
        set__overridden=True,
        set__pre_override=pre_override,
        set__computed_at=datetime.utcnow(),
        upsert=True,
    )

    # Push real-time — dashboard & monitoring ikut bergerak tanpa refresh manual,
    # persis seperti saat data sensor betulan masuk.
    payload = {
        "asset_id": str(asset.id),
        "machine_id": asset.machine_id,
        "asset_name": asset.name,
        "timestamp": datetime.utcnow().isoformat(),
        "health_score": health_score,
        "risk_level": risk["risk_level"],
    }
    socketio.emit("sensor_data_update", payload)
    if risk["risk_level"] in ALERT_RISK_LEVELS:
        socketio.emit("machine_alert", {
            **payload,
            "failure_probability": fault_prob,
            "predicted_days": risk["predicted_days"],
            "recommendation": recommendation,
        })

    return jsonify({
        "message": "Health score di-override (mode demo)",
        "machine_id": machine_id,
        "asset_name": asset.name,
        "overridden": True,
        "health_score": health_score,
        "failure_probability": fault_prob,
        "risk_level": risk["risk_level"],
        "priority": risk["priority"],
        "recommendation": recommendation,
        "notification_active": bool(faulty),
    }), 200


@demo_bp.route("/health-override/<machine_id>", methods=["DELETE"])
def clear_override(machine_id):
    asset = Asset.objects(machine_id=machine_id).first()
    if not asset:
        return _error(f"Aset dengan machine_id '{machine_id}' tidak ditemukan", 404)

    status = AssetHealthStatus.objects(asset=asset).first()
    if not status or not status.overridden:
        return jsonify({
            "message": "Tidak ada override aktif — tidak ada yang perlu dikembalikan",
            "machine_id": machine_id,
            "overridden": False,
        }), 200

    restored = status.pre_override or {}

    if restored.get("health_score") is None:
        # Sebelum override mesin ini memang belum punya snapshot hasil model
        # (belum pernah dikirimi data sensor) — kembalikan ke keadaan itu.
        status.delete()
        health_score = None
        risk_level = None
    else:
        for field in SNAPSHOT_FIELDS:
            setattr(status, field, restored.get(field))
        status.overridden = False
        status.pre_override = {}
        status.computed_at = datetime.utcnow()
        status.save()
        health_score = status.health_score
        risk_level = status.risk_level

    socketio.emit("sensor_data_update", {
        "asset_id": str(asset.id),
        "machine_id": asset.machine_id,
        "asset_name": asset.name,
        "timestamp": datetime.utcnow().isoformat(),
        "health_score": health_score,
        "risk_level": risk_level,
    })

    return jsonify({
        "message": "Mode demo dimatikan, health score dikembalikan ke kondisi semula",
        "machine_id": machine_id,
        "overridden": False,
        "health_score": health_score,
        "risk_level": risk_level,
    }), 200
