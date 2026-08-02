"""
Konfigurasi form simulasi input data sensor.
Version 2 — 5 sensor untuk komponen Bearing.
"""

import os

# URL backend CMMS (Flask) yang sudah di-hosting. Override lewat env var
# CMMS_API_BASE bila perlu (misal untuk tes ke localhost:5000/api).
CMMS_API_BASE = os.environ.get("CMMS_API_BASE", " https://cmms-polmanbandung.site//api")

# Machine ID target (sesuai field machine_id di database aset)
MACHINE_ID = "CMP-DUMMY-001"

# Aset dummy yang dipakai untuk uji coba model ML — dibuat otomatis kalau
# belum ada di database, sama seperti yang sebelumnya dilakukan front-end.
DUMMY_ASSET = {
    "name": "Dummy Compressor ML Test Rig",
    "machine_id": MACHINE_ID,
    "location": "Area Produksi - Simulasi ML",
    "status": "running",
}

# key, label, unit, nilai default
SENSOR_FIELDS = [
    ("noise_db",    "Kebisingan",              "dB",    51.50),
    ("water_flow",  "Aliran Air",              "L/min", 58.11),
    ("air_flow",    "Aliran Udara",            "m3/h",  600.0),
    ("gaccx",       "G-Axis Akselerasi X",     "g",     0.5768),
    ("outlet_temp", "Suhu Outlet",             "C",     118.28),
]

# Template nilai sensor berdasarkan hasil eksplorasi model ML (dipindahkan
# dari cmms-frontend/src/dummy-compressor/compressorSensorGenerator.js).
PRESETS = [
    {
        "id": "manual",
        "label": "Input Manual",
        "description": "Isi nilai sensor secara manual",
        "data": None,
    },
    {
        "id": "normal",
        "label": "Normal — Bearing OK",
        "description": "Bearing sehat — fault probability ~0% (very low risk)",
        "data": {
            "noise_db": 51.50, "water_flow": 58.11, "air_flow": 600.0,
            "gaccx": 0.5768, "outlet_temp": 118.28,
        },
    },
    {
        "id": "bearing_low",
        "label": "Bearing — Risiko Ringan",
        "description": "Bearing mulai tidak normal — fault probability ~11% (low risk)",
        "data": {
            "noise_db": 57.50, "water_flow": 58.11, "air_flow": 600.0,
            "gaccx": 0.5768, "outlet_temp": 118.28,
        },
    },
    {
        "id": "bearing_medium",
        "label": "Bearing — Risiko Sedang",
        "description": "Bearing terindikasi fault — fault probability ~37% (medium risk)",
        "data": {
            "noise_db": 58.00, "water_flow": 58.11, "air_flow": 600.0,
            "gaccx": 0.5768, "outlet_temp": 118.28,
        },
    },
    {
        "id": "bearing_high",
        "label": "Bearing — Risiko Tinggi",
        "description": "Bearing fault signifikan — fault probability ~70% (high risk)",
        "data": {
            "noise_db": 57.00, "water_flow": 58.11, "air_flow": 650.0,
            "gaccx": 0.5768, "outlet_temp": 118.28,
        },
    },
    {
        "id": "bearing_critical",
        "label": "Bearing — Kritis",
        "description": "Bearing kritis — fault probability ~99% (critical risk)",
        "data": {
            "noise_db": 58.00, "water_flow": 58.11, "air_flow": 700.0,
            "gaccx": 0.5768, "outlet_temp": 118.28,
        },
    },
]
