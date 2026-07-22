"""
Form simulasi input data sensor — Version 2 (5 sensor komponen Bearing).

Aplikasi Flask kecil dan berdiri sendiri (terpisah dari cmms-frontend) yang
mengirim data sensor langsung ke backend CMMS lewat HTTP, persis seperti
perangkat sensor sungguhan di lapangan. Form ini SENGAJA tidak menampilkan
hasil prediksi ML — ia hanya mengirim data, bukan mengolahnya. Semua
pemrosesan ML dan tampilan health/risk tetap sepenuhnya ada di backend +
front-end CMMS, supaya jelas ML jalan di server CMMS, bukan di simulasi ini.

Jalankan:
    pip install -r requirements.txt
    python app.py

Lalu buka http://127.0.0.1:5050
"""

import requests
from flask import Flask, render_template, request

from config import CMMS_API_BASE, MACHINE_ID, DUMMY_ASSET, SENSOR_FIELDS, PRESETS

app = Flask(__name__)


def ensure_dummy_asset():
    """Pastikan aset dummy compressor sudah terdaftar di CMMS sebelum kirim data sensor."""
    try:
        res = requests.get(f"{CMMS_API_BASE}/assets", timeout=10)
        res.raise_for_status()
        if any(a.get("machine_id") == MACHINE_ID for a in res.json()):
            return None
        create = requests.post(f"{CMMS_API_BASE}/assets", json=DUMMY_ASSET, timeout=10)
        create.raise_for_status()
        return None
    except requests.exceptions.RequestException as exc:
        return str(exc)


def send_sensor_data(payload):
    """Kirim satu paket data sensor ke /api/ml/sensor-data. Return error (None jika sukses)."""
    try:
        res = requests.post(f"{CMMS_API_BASE}/ml/sensor-data", json=payload, timeout=10)
    except requests.exceptions.ConnectionError:
        return "Tidak dapat terhubung ke backend CMMS. Pastikan server Flask backend berjalan."
    except requests.exceptions.Timeout:
        return "Request timeout. Server tidak merespons dalam 10 detik."
    except requests.exceptions.RequestException as exc:
        return str(exc)

    if res.status_code >= 400:
        try:
            return res.json().get("error", f"HTTP {res.status_code}")
        except ValueError:
            return f"HTTP {res.status_code}"
    return None


@app.route("/", methods=["GET", "POST"])
def index():
    sent = False
    error = None
    machine_id = MACHINE_ID
    form_values = {key: str(default) for key, _, _, default in SENSOR_FIELDS}

    if request.method == "POST":
        machine_id = request.form.get("machine_id", MACHINE_ID).strip() or MACHINE_ID

        payload = {"machine_id": machine_id}
        invalid = []
        for key, *_ in SENSOR_FIELDS:
            raw = request.form.get(key, "").strip()
            form_values[key] = raw
            try:
                payload[key] = float(raw)
            except ValueError:
                invalid.append(key)

        if invalid:
            error = f"Field berikut harus berupa angka: {', '.join(invalid)}"
        else:
            asset_error = ensure_dummy_asset() if machine_id == MACHINE_ID else None
            if asset_error:
                error = f"Gagal menyiapkan aset di CMMS: {asset_error}"
            else:
                error = send_sensor_data(payload)
                sent = error is None

    return render_template(
        "index.html",
        fields=SENSOR_FIELDS,
        presets=PRESETS,
        machine_id=machine_id,
        form_values=form_values,
        sent=sent,
        error=error,
        api_base=CMMS_API_BASE,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
