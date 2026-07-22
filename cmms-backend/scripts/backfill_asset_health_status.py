# /cmms-backend/scripts/backfill_asset_health_status.py
"""
Isi awal (backfill) koleksi AssetHealthStatus dari data sensor yang sudah ada.

Dipakai SEKALI setelah deploy perubahan precompute-at-ingest, supaya asset yang
sudah punya data sensor lama (sebelum perubahan ini) langsung tampil di
notifikasi predictive maintenance dashboard, tanpa harus menunggu data sensor
baru masuk lagi lewat simulator.

Jalankan dari folder cmms-backend:
    python -m scripts.backfill_asset_health_status
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import Asset, SensorData, AssetHealthStatus
from app.ml_service import CompressorPredictor

predictor = CompressorPredictor()


def _get_latest_valid_sensor(asset):
    for sensor in SensorData.objects(asset=asset).order_by('-timestamp').limit(50):
        if all(getattr(sensor, col, None) is not None for col in predictor.feature_columns):
            return sensor
    return None


def run():
    app = create_app()
    with app.app_context():
        if not predictor.is_ready():
            print("Model ML compressor belum siap (file model tidak ditemukan) — backfill dibatalkan.")
            return

        updated, skipped = 0, 0
        for asset in Asset.objects():
            latest_sensor = _get_latest_valid_sensor(asset)
            if not latest_sensor:
                skipped += 1
                continue

            payload = {col: getattr(latest_sensor, col, None) for col in predictor.feature_columns}
            result = predictor.predict(payload)
            if not result.get("ok"):
                skipped += 1
                continue

            AssetHealthStatus.objects(asset=asset).update_one(
                set__asset=asset,
                set__machine_id=asset.machine_id,
                set__asset_name=asset.name,
                set__overall_health_score=result.get("overall_health_score"),
                set__health_score=result.get("health_score"),
                set__failure_probability=result.get("failure_probability"),
                set__predicted_days=result.get("predicted_days"),
                set__risk_level=result.get("risk_level"),
                set__priority=result.get("priority"),
                set__recommendation=result.get("recommendation"),
                set__due_date=result.get("due_date"),
                set__components=result.get("components") or {},
                set__computed_at=latest_sensor.timestamp,
                upsert=True,
            )
            updated += 1
            print(f"OK  {asset.machine_id} ({asset.name}) -> risk={result.get('risk_level')}")

        print(f"\nBackfill selesai: {updated} asset ter-update, {skipped} asset dilewati (tidak ada data sensor lengkap).")


if __name__ == "__main__":
    run()
