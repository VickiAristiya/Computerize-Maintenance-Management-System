"""
Pengujian Rata-rata Waktu Respons Endpoint API CMMS
Version 2 — termasuk endpoint sensor bearing dan prediksi ML.
Cara pakai: python test_response_time.py
"""

import requests
import time
import statistics

BASE_URL = "https://cmms-test-domain.duckdns.org"
N = 10  # jumlah pengulangan per endpoint

# ── Login untuk dapat token ───────────────────────────────────────────────────
print("Melakukan login...")
try:
    login_resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@cmms.com", "password": "123456"},
        timeout=15,
        verify=False,
    )
    body  = login_resp.json()
    token = body.get("access_token") or body.get("token", "")
except Exception as e:
    print(f"Gagal terhubung ke server: {e}")
    exit(1)

if not token:
    print("Token tidak ditemukan. Cek email/password.")
    print(f"Response: {login_resp.text[:300]}")
    exit(1)

print("Login berhasil.\n")

HEADERS = {"Authorization": f"Bearer {token}"}

# Payload sensor bearing untuk uji endpoint POST
SENSOR_PAYLOAD = {
    "machine_id":  "CMP-DUMMY-001",
    "noise_db":    51.50,
    "water_flow":  58.11,
    "air_flow":    600.0,
    "gaccx":       0.5768,
    "outlet_temp": 118.28,
}

# ── Daftar endpoint yang diuji ────────────────────────────────────────────────
ENDPOINTS = [
    ("Login",                     "POST", "/api/auth/login",
        {"email": "admin@cmms.com", "password": "123456"}, False),
    ("Dashboard Stats",           "GET",  "/api/dashboard/stats",                None, True),
    ("Daftar Aset",               "GET",  "/api/assets",                         None, True),
    ("Monitoring Mesin",          "GET",  "/api/assets/monitoring/dashboard",    None, True),
    ("Daftar Work Order",         "GET",  "/api/workorders",                     None, True),
    ("Histori Work Order",        "GET",  "/api/workorders/history",             None, True),
    ("Laporan Statistik Aset",    "GET",  "/api/workorders/report/asset_stats",  None, True),
    ("Daftar Inventori",          "GET",  "/api/inventory/components",           None, True),
    ("Hasil Prediksi ML",         "GET",  "/api/ml/predictions",                 None, True),
    ("Histori Sensor Bearing",    "GET",  "/api/ml/sensor-history/CMP-DUMMY-001", None, True),
    ("Kirim Sensor Bearing",      "POST", "/api/ml/sensor-data",   SENSOR_PAYLOAD, True),
    ("Prediksi Bearing",          "POST", "/api/ml/predict/CMP-DUMMY-001", None, True),
    ("Fitur Model ML",            "GET",  "/api/ml/compressor/features",         None, True),
]

# ── Jalankan pengujian ────────────────────────────────────────────────────────
results = []

print(f"{'No':<4} {'Endpoint':<32} {'Method':<6} {'Min':>8} {'Max':>8} {'Avg':>8}  Status")
print("-" * 80)

for idx, (name, method, path, body, use_auth) in enumerate(ENDPOINTS, 1):
    times       = []
    last_status = "-"
    headers     = HEADERS if use_auth else {}

    for _ in range(N):
        try:
            t0 = time.perf_counter()
            if method == "GET":
                r = requests.get(f"{BASE_URL}{path}", headers=headers, timeout=15, verify=False)
            else:
                r = requests.post(f"{BASE_URL}{path}", json=body, headers=headers, timeout=15, verify=False)
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1000)
            last_status = r.status_code
        except Exception:
            last_status = "ERR"
            break

    if times:
        avg = statistics.mean(times)
        mn  = min(times)
        mx  = max(times)
        results.append((name, method, mn, mx, avg, last_status))
        print(f"{idx:<4} {name:<32} {method:<6} {mn:>6.0f}ms {mx:>6.0f}ms {avg:>6.0f}ms  {last_status}")
    else:
        results.append((name, method, 0, 0, 0, last_status))
        print(f"{idx:<4} {name:<32} {method:<6} {'GAGAL':>8} {'GAGAL':>8} {'GAGAL':>8}  {last_status}")

# ── Ringkasan ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("  RINGKASAN HASIL PENGUJIAN WAKTU RESPONS API")
print(f"  Server  : {BASE_URL}")
print(f"  Iterasi : {N}x per endpoint")
print("=" * 80)
print(f"{'No':<4} {'Endpoint':<32} {'Method':<6} {'Rata-rata':>10}  Keterangan")
print("-" * 80)

for idx, (name, method, mn, mx, avg, status) in enumerate(results, 1):
    if avg == 0:
        ket = "GAGAL"
    elif avg < 300:
        ket = "Baik"
    elif avg < 800:
        ket = "Cukup"
    else:
        ket = "Lambat"
    avgs = f"{avg:.0f} ms" if avg else "GAGAL"
    print(f"{idx:<4} {name:<32} {method:<6} {avgs:>10}  {ket}")

print("=" * 80)
print("Keterangan: Baik < 300ms | Cukup 300–800ms | Lambat > 800ms")
