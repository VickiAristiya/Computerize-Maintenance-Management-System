"""
Pengujian Beban (Load Testing) API CMMS
Version 2 — endpoint sensor bearing dan prediksi ML.
Cara pakai: python test_load.py
"""

import requests
import threading
import time
import statistics
import warnings
warnings.filterwarnings("ignore")

BASE_URL  = "https://cmms-test-domain.duckdns.org"
EMAIL     = "admin@cmms.com"
PASSWORD  = "123456"

# Skenario jumlah virtual user
USER_SCENARIOS = [10, 50, 100, 200]

# Endpoint yang diuji
ENDPOINT_METHOD = "POST"
ENDPOINT_PATH   = "/api/ml/sensor-data"
ENDPOINT_NAME   = "Kirim Sensor Bearing (ML Predict)"

# Payload sensor bearing
SENSOR_PAYLOAD = {
    "machine_id":  "CMP-DUMMY-001",
    "noise_db":    51.50,
    "water_flow":  58.11,
    "air_flow":    600.0,
    "gaccx":       0.5768,
    "outlet_temp": 118.28,
}

# ── Ambil token ───────────────────────────────────────────────────────────────
def get_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=15, verify=False,
    )
    return r.json().get("access_token") or r.json().get("token", "")

print("Login untuk mendapatkan token...")
TOKEN = get_token()
if not TOKEN:
    print("Gagal login.")
    exit(1)
print("Login berhasil.\n")

HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# ── Fungsi satu request ───────────────────────────────────────────────────────
def do_request(results, idx):
    try:
        t0 = time.perf_counter()
        r  = requests.request(
            ENDPOINT_METHOD,
            f"{BASE_URL}{ENDPOINT_PATH}",
            json=SENSOR_PAYLOAD,
            headers=HEADERS, timeout=20, verify=False,
        )
        elapsed = (time.perf_counter() - t0) * 1000
        results[idx] = {
            "ms":   elapsed,
            "ok":   r.status_code == 200,
            "code": r.status_code,
        }
    except Exception:
        results[idx] = {"ms": None, "ok": False, "code": "ERR"}

# ── Jalankan skenario ─────────────────────────────────────────────────────────
print(f"Endpoint diuji : {ENDPOINT_NAME} [{ENDPOINT_METHOD} {ENDPOINT_PATH}]")
print(f"Skenario       : {USER_SCENARIOS} concurrent users\n")

print(f"{'Pengguna Virtual':>18} {'Throughput (req/s)':>20} {'Avg Response (ms)':>20} {'Error Rate (%)':>16}")
print("-" * 80)

summary = []

for n_users in USER_SCENARIOS:
    results = [None] * n_users
    threads = [
        threading.Thread(target=do_request, args=(results, i))
        for i in range(n_users)
    ]

    t_start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    t_total = time.perf_counter() - t_start

    times     = [r["ms"] for r in results if r and r["ms"] is not None]
    n_success = sum(1 for r in results if r and r["ok"])
    n_error   = n_users - n_success

    avg_ms     = statistics.mean(times) if times else 0
    throughput = n_users / t_total if t_total > 0 else 0
    error_rate = (n_error / n_users) * 100

    summary.append((n_users, throughput, avg_ms, error_rate))
    print(f"{n_users:>18} {throughput:>19.2f} {avg_ms:>19.0f} {error_rate:>15.1f}")

# ── Ringkasan ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("  RINGKASAN HASIL PENGUJIAN BEBAN")
print(f"  Endpoint : {ENDPOINT_NAME} — {BASE_URL}{ENDPOINT_PATH}")
print("=" * 80)
print(f"{'Pengguna Virtual':>18} {'Throughput (req/s)':>20} {'Avg Response (ms)':>20} {'Error Rate (%)':>16}")
print("-" * 80)

for n_users, tput, avg, err in summary:
    if err > 10:
        ket = " [Tidak Stabil]"
    elif avg > 2000:
        ket = " [Lambat]"
    elif avg > 800:
        ket = " [Cukup]"
    else:
        ket = " [Baik]"
    print(f"{n_users:>18} {tput:>19.2f} {avg:>19.0f} {err:>15.1f}{ket}")

print("=" * 80)
