"""
Generator nilai sensor untuk berbagai skenario simulasi.
Version 2 — 5 sensor untuk komponen Bearing.
"""

import random
from config import NORMAL_RANGE, FAULT_RANGE


def generate_normal(noise=0.02):
    """Sensor dalam kondisi normal dengan sedikit noise acak."""
    return {
        key: round(random.uniform(lo, hi) * (1 + random.uniform(-noise, noise)), 4)
        for key, (lo, hi) in NORMAL_RANGE.items()
    }


def generate_fault(noise=0.02):
    """Sensor dalam kondisi fault — Bearing Noisy."""
    return {
        key: round(random.uniform(lo, hi) * (1 + random.uniform(-noise, noise)), 4)
        for key, (lo, hi) in FAULT_RANGE.items()
    }


def generate_gradual(step, total_steps):
    """
    Degradasi bertahap dari kondisi normal ke fault.
    step=0 → normal, step=total_steps → fault.
    """
    t = step / max(total_steps, 1)
    result = {}
    for key in NORMAL_RANGE:
        lo_n, hi_n = NORMAL_RANGE[key]
        lo_f, hi_f = FAULT_RANGE[key]
        normal_mid = (lo_n + hi_n) / 2
        fault_mid  = (lo_f + hi_f) / 2
        val = normal_mid + (fault_mid - normal_mid) * t
        val *= (1 + random.uniform(-0.02, 0.02))
        result[key] = round(val, 4)
    return result


def generate_random(fault_probability=0.3):
    """Acak antara normal dan fault berdasarkan probabilitas."""
    if random.random() < fault_probability:
        return generate_fault()
    return generate_normal()


def generate_custom(values: dict):
    """
    Kirim nilai sensor kustom (manual).
    Contoh:
        generate_custom({
            "noise_db": 51.5, "water_flow": 58.1, "air_flow": 600.0,
            "gaccx": 0.5768, "outlet_temp": 118.28
        })
    """
    required = list(NORMAL_RANGE.keys())
    missing = [k for k in required if k not in values]
    if missing:
        raise ValueError(f"Field sensor kurang: {missing}")
    return {k: round(float(values[k]), 4) for k in required}
