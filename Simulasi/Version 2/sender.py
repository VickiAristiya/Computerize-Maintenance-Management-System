"""
Modul pengiriman data sensor ke backend API.
Version 2 — 5 sensor untuk komponen Bearing.
"""

import requests
from config import BASE_URL, MACHINE_ID


def send_sensor(payload: dict) -> dict:
    """
    Kirim satu paket data sensor ke /api/ml/sensor-data.
    Mengembalikan dict hasil prediksi atau error info.
    """
    data = {"machine_id": MACHINE_ID, **payload}
    try:
        res = requests.post(
            f"{BASE_URL}/sensor-data",
            json=data,
            timeout=10,
        )
        res.raise_for_status()
        return res.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Tidak dapat terhubung ke server. Periksa koneksi internet."}
    except requests.exceptions.Timeout:
        return {"error": "Request timeout. Server tidak merespons dalam 10 detik."}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {e.response.status_code}: {e.response.text[:100]}"}
    except Exception as e:
        return {"error": str(e)}


def print_result(index, total, payload, response):
    """Tampilkan hasil prediksi bearing ke terminal dengan format yang rapi."""
    prefix = f"[{index:02d}/{total}]" if total else f"[{index:04d}]"

    noise   = payload.get("noise_db", 0)
    af      = payload.get("air_flow", 0)
    wf      = payload.get("water_flow", 0)
    ot      = payload.get("outlet_temp", 0)

    sensor_str = (
        f"noise={noise:.1f}dB  af={af:.0f}m³/h  "
        f"wf={wf:.1f}L/m  ot={ot:.1f}°C"
    )

    if "error" in response:
        print(f"{prefix} {sensor_str}")
        print(f"         ✗ {response['error']}")
        return

    pred = response.get("prediction") or {}
    if pred and pred.get("ok"):
        health      = pred.get("health_score", 0) * 100
        fault_prob  = pred.get("failure_probability", 0) * 100
        risk        = pred.get("risk_level", "-")
        status      = pred.get("status", "-")
        print(f"{prefix} {sensor_str}")
        print(f"         ✓ Bearing: {status:<15}  Health: {health:5.1f}%  "
              f"Fault: {fault_prob:5.1f}%  Risk: {risk}")
    else:
        print(f"{prefix} {sensor_str}")
        print(f"         ✓ Terkirim (tidak ada prediksi ML)")
