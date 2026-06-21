"""
Analisis prediksi model ML untuk berbagai kondisi sensor.
Jalankan dari root project: python analyze_templates.py
"""
import sys, os, io, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "cmms-backend"))

from app.ml_service import CompressorPredictor, COMPONENT_NAME_ID, COMPONENTS

# Template sensor dari dataset percentile
TEMPLATES = {
    "Normal (Ok-P50)": {
        "rpm": 1500.0, "motor_power": 5874.4252, "noise_db": 51.5149,
        "outlet_pressure_bar": 4.018, "air_flow": 600.1478, "outlet_temp": 119.3749,
        "wpump_outlet_press": 2.8, "water_flow": 55.8112, "gaccz": 3.5898, "haccz": 3.3219,
    },
    "Maintenance Rendah (Noisy-P25)": {
        "rpm": 989.25, "motor_power": 3567.173, "noise_db": 51.4391,
        "outlet_pressure_bar": 2.4125, "air_flow": 594.9976, "outlet_temp": 100.1398,
        "wpump_outlet_press": 2.3454, "water_flow": 58.1976, "gaccz": 2.5713, "haccz": 2.7966,
    },
    "Maintenance Sedang (Noisy-P50)": {
        "rpm": 1499.5, "motor_power": 6138.0733, "noise_db": 58.2337,
        "outlet_pressure_bar": 4.096, "air_flow": 902.107, "outlet_temp": 112.353,
        "wpump_outlet_press": 2.634, "water_flow": 58.4681, "gaccz": 3.6527, "haccz": 3.3943,
    },
    "Maintenance Tinggi (Noisy-P75)": {
        "rpm": 2010.25, "motor_power": 9405.3371, "noise_db": 66.6373,
        "outlet_pressure_bar": 5.7722, "air_flow": 1215.3731, "outlet_temp": 125.5074,
        "wpump_outlet_press": 3.0428, "water_flow": 58.6898, "gaccz": 5.3003, "haccz": 4.1704,
    },
    "Maintenance Kritis (Noisy-P90)": {
        "rpm": 2497.1, "motor_power": 14309.501, "noise_db": 70.3081,
        "outlet_pressure_bar": 6.8842, "air_flow": 1505.4202, "outlet_temp": 137.3772,
        "wpump_outlet_press": 3.3735, "water_flow": 58.8931, "gaccz": 6.7893, "haccz": 4.9894,
    },
}

def interpolate(a, b, t):
    return {k: a[k] + (b[k] - a[k]) * t for k in a}

base_ok  = TEMPLATES["Normal (Ok-P50)"]
base_p50 = TEMPLATES["Maintenance Sedang (Noisy-P50)"]
base_p90 = TEMPLATES["Maintenance Kritis (Noisy-P90)"]

extra = {
    "Blend 25% (Ok->Noisy-P50)": interpolate(base_ok, base_p50, 0.25),
    "Blend 50% (Ok->Noisy-P50)": interpolate(base_ok, base_p50, 0.50),
    "Blend 75% (Ok->Noisy-P50)": interpolate(base_ok, base_p50, 0.75),
    "Blend 25% (Ok->Noisy-P90)": interpolate(base_ok, base_p90, 0.25),
    "Blend 50% (Ok->Noisy-P90)": interpolate(base_ok, base_p90, 0.50),
    "Blend 75% (Ok->Noisy-P90)": interpolate(base_ok, base_p90, 0.75),
}

ALL_SCENARIOS = {**TEMPLATES, **extra}

SENSOR_LABELS = {
    "rpm":                "RPM",
    "motor_power":        "Motor Power (W)",
    "noise_db":           "Noise (dB)",
    "outlet_pressure_bar":"Pressure (bar)",
    "air_flow":           "Air Flow (m3/h)",
    "outlet_temp":        "Outlet Temp (C)",
    "wpump_outlet_press": "WPump Press (bar)",
    "water_flow":         "Water Flow (L/min)",
    "gaccz":              "G-Acc Z (g)",
    "haccz":              "H-Acc Z (g)",
}

COMP_NAMES = {c: COMPONENT_NAME_ID[c] for c in COMPONENTS}
RISK_ORDER = ["very_low", "low", "medium", "high", "critical"]
RISK_LABEL = {"critical": "KRITIS", "high": "TINGGI", "medium": "SEDANG",
              "low": "RENDAH", "very_low": "SG.RENDAH"}


def pct(v):
    return f"{v*100:5.1f}%"


def run():
    predictor = CompressorPredictor()
    if not predictor.is_ready():
        print("ERROR: Model files tidak ditemukan:", predictor.missing_model_files())
        return

    rows = []
    for name, sensors in ALL_SCENARIOS.items():
        result = predictor.predict(sensors)
        if not result["ok"]:
            print(f"SKIP {name}: {result}")
            continue
        row = {
            "scenario": name,
            "sensors": sensors,
            "overall_health": result["overall_health_score"],
            "recommendation": result["recommendation"],
        }
        for c in COMPONENTS:
            row[c] = result["components"][c]
        rows.append(row)

    # ====================================================================
    # TABEL 1: Nilai sensor per skenario
    # ====================================================================
    scenario_keys = [r["scenario"] for r in rows]
    W_S = 20
    W_V = 14

    div = "=" * (W_S + W_V * len(rows) + len(rows))
    print("\n" + div)
    print("TABEL 1 -- NILAI SENSOR PER SKENARIO")
    print(div)

    # Header: nama skenario disingkat 13 char
    print(f"{'Sensor':<{W_S}}", end="")
    for r in rows:
        label = r["scenario"][:13]
        print(f" {label:>{W_V-1}}", end="")
    print()
    print("-" * (W_S + W_V * len(rows) + len(rows)))

    for sk, slabel in SENSOR_LABELS.items():
        print(f"{slabel:<{W_S}}", end="")
        for r in rows:
            val = r["sensors"].get(sk, 0)
            print(f" {val:>{W_V-1}.2f}", end="")
        print()

    # ====================================================================
    # TABEL 2: Fault probability per komponen
    # ====================================================================
    W_N = 32
    W_C = 14

    print("\n" + "=" * (W_N + W_C * (len(COMPONENTS) + 1) + len(COMPONENTS) + 1))
    print("TABEL 2 -- FAULT PROBABILITY (FP) PER KOMPONEN")
    print("=" * (W_N + W_C * (len(COMPONENTS) + 1) + len(COMPONENTS) + 1))

    hdr = f"{'Skenario':<{W_N}}"
    for c in COMPONENTS:
        hdr += f" {('[' + COMP_NAMES[c] + '] FP'):>{W_C}}"
    hdr += f" {'Overall HS':>{W_C}}"
    print(hdr)
    print("-" * (W_N + W_C * (len(COMPONENTS) + 1) + len(COMPONENTS) + 1))

    for r in rows:
        line = f"{r['scenario']:<{W_N}}"
        for c in COMPONENTS:
            fp = r[c]["failure_probability"]
            line += f" {pct(fp):>{W_C}}"
        line += f" {pct(r['overall_health']):>{W_C}}"
        print(line)

    # ====================================================================
    # TABEL 3: Health score per komponen
    # ====================================================================
    print("\n" + "=" * (W_N + W_C * (len(COMPONENTS) + 1) + len(COMPONENTS) + 1))
    print("TABEL 3 -- HEALTH SCORE (HS) PER KOMPONEN")
    print("=" * (W_N + W_C * (len(COMPONENTS) + 1) + len(COMPONENTS) + 1))

    hdr = f"{'Skenario':<{W_N}}"
    for c in COMPONENTS:
        hdr += f" {('[' + COMP_NAMES[c] + '] HS'):>{W_C}}"
    hdr += f" {'Overall HS':>{W_C}}"
    print(hdr)
    print("-" * (W_N + W_C * (len(COMPONENTS) + 1) + len(COMPONENTS) + 1))

    for r in rows:
        line = f"{r['scenario']:<{W_N}}"
        for c in COMPONENTS:
            hs = r[c]["health_score"]
            line += f" {pct(hs):>{W_C}}"
        line += f" {pct(r['overall_health']):>{W_C}}"
        print(line)

    # ====================================================================
    # TABEL 4: Risk level per komponen
    # ====================================================================
    print("\n" + "=" * (W_N + W_C * (len(COMPONENTS) + 1) + len(COMPONENTS) + 1))
    print("TABEL 4 -- RISK LEVEL PER KOMPONEN")
    print("=" * (W_N + W_C * (len(COMPONENTS) + 1) + len(COMPONENTS) + 1))

    hdr = f"{'Skenario':<{W_N}}"
    for c in COMPONENTS:
        hdr += f" {('[' + COMP_NAMES[c] + ']'):>{W_C}}"
    hdr += f" {'Worst Risk':>{W_C}}"
    print(hdr)
    print("-" * (W_N + W_C * (len(COMPONENTS) + 1) + len(COMPONENTS) + 1))

    for r in rows:
        line = f"{r['scenario']:<{W_N}}"
        risk_levels = []
        for c in COMPONENTS:
            rl = r[c]["risk_level"]
            risk_levels.append(rl)
            label = RISK_LABEL.get(rl, rl)
            line += f" {label:>{W_C}}"
        worst = max(risk_levels, key=lambda x: RISK_ORDER.index(x) if x in RISK_ORDER else 0)
        line += f" {RISK_LABEL.get(worst, worst):>{W_C}}"
        print(line)

    # ====================================================================
    # TABEL 5: Predicted days per komponen
    # ====================================================================
    print("\n" + "=" * (W_N + W_C * (len(COMPONENTS) + 1) + len(COMPONENTS) + 1))
    print("TABEL 5 -- PREDICTED DAYS (hari sebelum maintenance)")
    print("=" * (W_N + W_C * (len(COMPONENTS) + 1) + len(COMPONENTS) + 1))

    hdr = f"{'Skenario':<{W_N}}"
    for c in COMPONENTS:
        hdr += f" {('[' + COMP_NAMES[c] + '] days'):>{W_C}}"
    hdr += f" {'Worst days':>{W_C}}"
    print(hdr)
    print("-" * (W_N + W_C * (len(COMPONENTS) + 1) + len(COMPONENTS) + 1))

    for r in rows:
        line = f"{r['scenario']:<{W_N}}"
        day_vals = []
        for c in COMPONENTS:
            d = r[c]["predicted_days"]
            day_vals.append(d)
            line += f" {str(d) + ' hr':>{W_C}}"
        worst_day = min(day_vals)
        line += f" {str(worst_day) + ' hr':>{W_C}}"
        print(line)

    # ====================================================================
    # TABEL 6: Prediction label per komponen
    # ====================================================================
    W_P = 16
    print("\n" + "=" * (W_N + W_P * len(COMPONENTS) + len(COMPONENTS)))
    print("TABEL 6 -- PREDICTION LABEL (Ok/Noisy/Dirty) PER KOMPONEN")
    print("=" * (W_N + W_P * len(COMPONENTS) + len(COMPONENTS)))

    hdr = f"{'Skenario':<{W_N}}"
    for c in COMPONENTS:
        hdr += f" {COMP_NAMES[c]:>{W_P}}"
    print(hdr)
    print("-" * (W_N + W_P * len(COMPONENTS) + len(COMPONENTS)))

    for r in rows:
        line = f"{r['scenario']:<{W_N}}"
        for c in COMPONENTS:
            label = r[c]["prediction"]
            line += f" {label:>{W_P}}"
        print(line)

    # ====================================================================
    # RINGKASAN: Threshold kondisi per level risiko
    # ====================================================================
    print("\n" + "=" * 90)
    print("RINGKASAN -- KONDISI YANG MENGHASILKAN SETIAP LEVEL RISIKO")
    print("=" * 90)

    thresholds = [
        ("KRITIS    (fp >= 80%)", lambda fp: fp >= 0.80),
        ("TINGGI    (fp >= 50%)", lambda fp: 0.50 <= fp < 0.80),
        ("SEDANG    (fp >= 30%)", lambda fp: 0.30 <= fp < 0.50),
        ("RENDAH    (fp >= 10%)", lambda fp: 0.10 <= fp < 0.30),
        ("SG.RENDAH (fp <  10%)", lambda fp: fp < 0.10),
    ]

    for label, cond in thresholds:
        print(f"\n-- {label} --")
        found = False
        for r in rows:
            triggered = [COMP_NAMES[c] for c in COMPONENTS if cond(r[c]["failure_probability"])]
            if triggered:
                fps = [f"{COMP_NAMES[c]}={pct(r[c]['failure_probability'])}" for c in COMPONENTS if cond(r[c]["failure_probability"])]
                print(f"   {r['scenario']:<40} -> {', '.join(fps)}")
                found = True
        if not found:
            print("   (tidak ada skenario)")

    # ====================================================================
    # DETAIL: Rekomendasi per skenario
    # ====================================================================
    print("\n" + "=" * 90)
    print("DETAIL REKOMENDASI AGREGAT PER SKENARIO")
    print("=" * 90)
    for r in rows:
        print(f"\n[{r['scenario']}]")
        faulty = [COMP_NAMES[c] for c in COMPONENTS if r[c]["failure_probability"] >= 0.5]
        print(f"  Komponen fault (fp>=50%): {', '.join(faulty) if faulty else 'Tidak ada'}")
        print(f"  Overall Health  : {pct(r['overall_health'])}")
        print(f"  Rekomendasi     : {r['recommendation']}")


if __name__ == "__main__":
    run()
