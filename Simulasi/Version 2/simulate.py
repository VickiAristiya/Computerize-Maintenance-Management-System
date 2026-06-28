"""
Script utama simulasi pengiriman data sensor ke CMMS.
Version 2 — 5 sensor untuk komponen Bearing.

Jalankan:
    python simulate.py                      # mode default (gradual)
    python simulate.py --mode normal        # kondisi normal (Bearing OK)
    python simulate.py --mode fault         # kondisi fault (Bearing Noisy)
    python simulate.py --mode gradual       # degradasi normal → fault
    python simulate.py --mode random        # acak normal/fault
    python simulate.py --mode manual        # input nilai sendiri

    python simulate.py --mode gradual --total 30 --interval 5
"""

import argparse
import time
import sys

from config import INTERVAL_SECONDS, TOTAL_SAMPLES
from sensor_generator import (
    generate_normal,
    generate_fault,
    generate_gradual,
    generate_random,
    generate_custom,
)
from sender import send_sensor, print_result


MODES = ["normal", "fault", "gradual", "random", "manual"]


def parse_args():
    parser = argparse.ArgumentParser(description="Simulasi sensor CMMS — Bearing (Version 2)")
    parser.add_argument("--mode",     choices=MODES, default="gradual",
                        help="Mode simulasi (default: gradual)")
    parser.add_argument("--total",    type=int, default=TOTAL_SAMPLES,
                        help="Jumlah data yang dikirim (default dari config)")
    parser.add_argument("--interval", type=float, default=INTERVAL_SECONDS,
                        help="Interval antar pengiriman dalam detik")
    return parser.parse_args()


def input_manual():
    """Minta user input nilai 5 sensor bearing secara manual."""
    fields = [
        ("noise_db",    "Noise (dB)",            51.50),
        ("water_flow",  "Water flow (L/min)",     58.11),
        ("air_flow",    "Air flow (m³/h)",       600.00),
        ("gaccx",       "G-Acc X (g)",            0.5768),
        ("outlet_temp", "Outlet temp (°C)",       118.28),
    ]
    print("\nMasukkan nilai sensor bearing (tekan Enter untuk pakai nilai default):")
    values = {}
    for key, label, default in fields:
        try:
            raw = input(f"  {label} [{default}]: ").strip()
            values[key] = float(raw) if raw else default
        except ValueError:
            print(f"    Input tidak valid, pakai default: {default}")
            values[key] = default
    return generate_custom(values)


def run():
    args     = parse_args()
    mode     = args.mode
    total    = args.total
    interval = args.interval

    print("=" * 65)
    print(f"  CMMS Sensor Simulator — Bearing (Version 2)")
    print(f"  Sensor  : noise_db, water_flow, air_flow, gaccx, outlet_temp")
    print(f"  Mode    : {mode.upper()}")
    if mode != "manual":
        print(f"  Total   : {total} data")
        print(f"  Interval: {interval} detik")
    print("=" * 65)

    if mode == "manual":
        payload  = input_manual()
        print(f"\nMengirim data sensor...")
        response = send_sensor(payload)
        print_result(1, 1, payload, response)
        print("\nSelesai.")
        return

    for i in range(total):
        if mode == "normal":
            payload = generate_normal()
        elif mode == "fault":
            payload = generate_fault()
        elif mode == "gradual":
            payload = generate_gradual(i, total - 1)
        elif mode == "random":
            payload = generate_random(fault_probability=0.3)

        response = send_sensor(payload)
        print_result(i + 1, total, payload, response)

        if i < total - 1:
            try:
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\n\nDihentikan oleh user.")
                sys.exit(0)

    print("\nSelesai.")


if __name__ == "__main__":
    run()
