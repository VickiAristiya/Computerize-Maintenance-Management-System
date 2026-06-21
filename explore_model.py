"""
Eksplorasi model ML: cari kombinasi sensor yang menghasilkan
berbagai level fault probability untuk semua 4 komponen.

Strategi:
  1. Baca baris langsung dari dataset (ground truth)
  2. Sweep satu sensor sekaligus (sensitivity analysis)
  3. Random sampling dari range yang diketahui
  4. Ringkasan batas keputusan per komponen

Jalankan: python explore_model.py
"""
import sys, os, io, warnings, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "cmms-backend"))
from app.ml_service import CompressorPredictor, COMPONENT_NAME_ID, COMPONENTS

random.seed(42)
np.random.seed(42)

COMP_NAMES = {c: COMPONENT_NAME_ID[c] for c in COMPONENTS}
SHORT = {"bearings": "BRG", "wpump": "WPU", "radiator": "RAD", "exvalve": "EXV"}

predictor = CompressorPredictor()
if not predictor.is_ready():
    print("ERROR: model tidak siap")
    sys.exit(1)

FEAT = predictor.feature_columns

# --------------------------------------------------------------------------
# Helper
# --------------------------------------------------------------------------
def predict_row(sensor_dict):
    result = predictor.predict(sensor_dict)
    if not result["ok"]:
        return None
    return result

def fp(result, comp):
    return result["components"][comp]["failure_probability"]

def hs(result, comp):
    return result["components"][comp]["health_score"]

def rl(result, comp):
    return result["components"][comp]["risk_level"]

def row_str(label, result, sensors=None):
    parts = [f"{label:<38}"]
    for c in COMPONENTS:
        parts.append(f"{fp(result,c)*100:6.1f}%/{hs(result,c)*100:5.1f}%")
    parts.append(f"{result['overall_health_score']*100:5.1f}%")
    return "  ".join(parts)

def print_table_header():
    h = f"{'Skenario':<38}"
    for c in COMPONENTS:
        h += f"  {SHORT[c]+' FP/HS':^13}"
    h += "  OverallHS"
    print(h)
    print("-" * len(h))


# ==========================================================================
# BAGIAN 1: Baca langsung dari dataset — per label komponen
# ==========================================================================
print("\n" + "=" * 110)
print("BAGIAN 1 -- BARIS DATASET ASLI (per label komponen)")
print("Membaca machine-learning filtered data/data.csv ...")
print("=" * 110)

CSV_PATH = os.path.join(os.path.dirname(__file__),
                        "machine-learning filtered data", "data.csv")
df_raw = pd.read_csv(CSV_PATH)
print(f"Dataset: {df_raw.shape[0]} baris, {df_raw.shape[1]} kolom")
print(f"Kolom: {list(df_raw.columns)}\n")

# Cari kolom label untuk setiap komponen
label_col_map = {}
for c in COMPONENTS:
    for col in df_raw.columns:
        if c.lower() in col.lower() and ("label" in col.lower() or "status" in col.lower() or "condition" in col.lower() or "state" in col.lower()):
            label_col_map[c] = col
            break

# Jika tidak ketemu, cari kolom yang nilai-nya mengandung Noisy/Dirty/Ok/Clean
if not label_col_map:
    for col in df_raw.columns:
        vals = df_raw[col].dropna().unique()
        str_vals = [str(v).strip().lower() for v in vals if isinstance(v, str)]
        if any(v in str_vals for v in ["noisy", "dirty", "ok", "clean"]):
            print(f"  Kolom kategorikal terdeteksi: {col} -> {vals[:8]}")

print(f"\nLabel kolom terdeteksi: {label_col_map}")

# Jika ada kolom label, ambil sampel per kondisi
SAMPLE_PER_COND = 5
dataset_results = []

if label_col_map:
    for comp, lcol in label_col_map.items():
        conditions = df_raw[lcol].unique()
        print(f"\n  [{COMP_NAMES[comp]}] kolom='{lcol}', kondisi={list(conditions)}")
        for cond in conditions:
            subset = df_raw[df_raw[lcol] == cond]
            sample = subset.sample(min(SAMPLE_PER_COND, len(subset)), random_state=42)
            for _, row in sample.iterrows():
                sensor = {f: float(row[f]) for f in FEAT if f in row and pd.notna(row[f])}
                if len(sensor) < len(FEAT):
                    continue
                result = predict_row(sensor)
                if result:
                    dataset_results.append({
                        "label": f"Dataset [{COMP_NAMES[comp]}] {cond}",
                        "result": result,
                        "sensors": sensor
                    })
else:
    # Tidak ada kolom label terstruktur — ambil 10 baris random
    print("\n  (Kolom label tidak ditemukan, ambil 10 baris random dari dataset)")
    sample = df_raw.sample(min(20, len(df_raw)), random_state=42)
    for i, (_, row) in enumerate(sample.iterrows()):
        sensor = {f: float(row[f]) for f in FEAT if f in row and pd.notna(row[f])}
        if len(sensor) < len(FEAT):
            continue
        result = predict_row(sensor)
        if result:
            dataset_results.append({
                "label": f"Dataset row#{i+1}",
                "result": result,
                "sensors": sensor
            })

if dataset_results:
    print()
    print_table_header()
    for d in dataset_results:
        print(row_str(d["label"], d["result"]))


# ==========================================================================
# BAGIAN 2: Sensor values dari dataset (percentile) per kolom
# ==========================================================================
print("\n\n" + "=" * 110)
print("BAGIAN 2 -- STATISTIK SENSOR DARI DATASET (untuk menentukan range sweep)")
print("=" * 110)

sensor_stats = {}
for f in FEAT:
    if f in df_raw.columns:
        col = df_raw[f].dropna()
        sensor_stats[f] = {
            "min": col.min(), "p10": col.quantile(0.10),
            "p25": col.quantile(0.25), "p50": col.quantile(0.50),
            "p75": col.quantile(0.75), "p90": col.quantile(0.90),
            "max": col.max(),
        }

print(f"{'Sensor':<22} {'Min':>8} {'P10':>8} {'P25':>8} {'P50':>8} {'P75':>8} {'P90':>8} {'Max':>8}")
print("-" * 86)
for f, s in sensor_stats.items():
    print(f"{f:<22} {s['min']:>8.2f} {s['p10']:>8.2f} {s['p25']:>8.2f} {s['p50']:>8.2f} {s['p75']:>8.2f} {s['p90']:>8.2f} {s['max']:>8.2f}")


# ==========================================================================
# BAGIAN 3: Sweep satu sensor — sisanya di nilai P50
# ==========================================================================
print("\n\n" + "=" * 110)
print("BAGIAN 3 -- SENSITIVITY SWEEP: variasikan 1 sensor, sisanya di P50")
print("=" * 110)

# Baseline: semua sensor di P50
baseline = {f: sensor_stats[f]["p50"] if f in sensor_stats else 1.0 for f in FEAT}

sweep_points = [0, 10, 25, 50, 75, 90, 100]  # percentile label
sweep_values_map = {
    pct: {f: sensor_stats[f][f"p{pct}"] if f"p{pct}" in sensor_stats.get(f, {}) else sensor_stats[f]["p50"]
          for f in FEAT if f in sensor_stats}
    for pct in [10, 25, 50, 75, 90]
}
# Min dan max
sweep_values_map[0]   = {f: sensor_stats[f]["min"] for f in FEAT if f in sensor_stats}
sweep_values_map[100] = {f: sensor_stats[f]["max"] for f in FEAT if f in sensor_stats}

for sweep_sensor in FEAT:
    if sweep_sensor not in sensor_stats:
        continue
    print(f"\n  Sweep sensor: {sweep_sensor}")
    print(f"  {'Nilai':>10}  {'%-ile':>6}", end="")
    for c in COMPONENTS:
        print(f"  {SHORT[c]+' FP':>8}", end="")
    print(f"  {'OverHS':>8}")
    print("  " + "-" * (10 + 6 + len(COMPONENTS) * 10 + 10))

    for pct_label in sorted(sweep_values_map.keys()):
        sensors = {**baseline}
        sensors[sweep_sensor] = sweep_values_map[pct_label].get(sweep_sensor, baseline.get(sweep_sensor, 0))
        result = predict_row(sensors)
        if not result:
            continue
        val = sensors[sweep_sensor]
        print(f"  {val:>10.3f}  P{pct_label:<4}", end="")
        for c in COMPONENTS:
            print(f"  {fp(result,c)*100:>7.1f}%", end="")
        print(f"  {result['overall_health_score']*100:>7.1f}%")


# ==========================================================================
# BAGIAN 4: Random combinations dari rentang dataset
# ==========================================================================
print("\n\n" + "=" * 110)
print("BAGIAN 4 -- RANDOM COMBINATIONS (200 sampel dari range dataset)")
print("=" * 110)

N_RANDOM = 200
random_results = []
for _ in range(N_RANDOM):
    sensors = {}
    for f in FEAT:
        if f in sensor_stats:
            lo = sensor_stats[f]["min"]
            hi = sensor_stats[f]["max"]
            sensors[f] = lo + random.random() * (hi - lo)
        else:
            sensors[f] = baseline.get(f, 1.0)
    result = predict_row(sensors)
    if result:
        random_results.append({"sensors": sensors, "result": result})

# Grup berdasarkan pola fault
groups = {
    "none_fault": [],
    "brg_only": [],
    "wpu_only": [],
    "rad_only": [],
    "exv_only": [],
    "multi_fault": [],
    "all_fault": [],
}
for d in random_results:
    faults = [c for c in COMPONENTS if fp(d["result"], c) >= 0.5]
    if len(faults) == 0:
        groups["none_fault"].append(d)
    elif len(faults) == 4:
        groups["all_fault"].append(d)
    elif len(faults) > 1:
        groups["multi_fault"].append(d)
    elif faults[0] == "bearings":
        groups["brg_only"].append(d)
    elif faults[0] == "wpump":
        groups["wpu_only"].append(d)
    elif faults[0] == "radiator":
        groups["rad_only"].append(d)
    elif faults[0] == "exvalve":
        groups["exv_only"].append(d)

print(f"\nDistribusi dari {N_RANDOM} random samples:")
for g, items in groups.items():
    print(f"  {g:<16}: {len(items)} sampel")

# Tampilkan 3 contoh dari tiap grup
for g, items in groups.items():
    if not items:
        continue
    print(f"\n  -- Contoh {g} --")
    print_table_header()
    for d in items[:3]:
        faults = [SHORT[c] for c in COMPONENTS if fp(d["result"], c) >= 0.5]
        label = g + f" ({','.join(faults)})" if faults else g
        print(row_str(label, d["result"]))
        # Print sensor values ringkas
        sv = "  ".join(f"{f}={d['sensors'][f]:.1f}" for f in FEAT)
        print(f"{'':38}  sensors: {sv[:90]}")


# ==========================================================================
# BAGIAN 5: Cari boundary — di mana bearing berpindah dari Ok ke Noisy
# ==========================================================================
print("\n\n" + "=" * 110)
print("BAGIAN 5 -- BINARY SEARCH: batas keputusan bearing (Ok->Noisy)")
print("Sweep setiap sensor satu per satu dari P50_ok ke P50_noisy")
print("=" * 110)

# Titik ok = baseline P50
OK_BASE   = {f: sensor_stats[f]["p50"] for f in FEAT if f in sensor_stats}
# Titik fault = P90 (tertinggi yang kita tahu trigger fault)
FAULT_BASE = {f: sensor_stats[f]["p90"] for f in FEAT if f in sensor_stats}

def predict_bearing_fp(sensors):
    r = predict_row(sensors)
    return fp(r, "bearings") if r else 0.0

print(f"\n  Baseline (P50) -> bearing FP = {predict_bearing_fp(OK_BASE)*100:.1f}%")
print(f"  P90 all        -> bearing FP = {predict_bearing_fp(FAULT_BASE)*100:.1f}%")

# Binary search untuk setiap sensor: titik mana sensor mulai trigger bearing
print(f"\n  Binary search per sensor (semua lain di P50, target: bearing FP>=50%)")
print(f"  {'Sensor':<22}  {'P50 val':>9}  {'P90 val':>9}  {'Threshold val':>14}  {'FP di threshold':>16}")
print("  " + "-" * 80)

for sweep_sensor in FEAT:
    if sweep_sensor not in sensor_stats:
        continue
    lo_val = sensor_stats[sweep_sensor]["p50"]
    hi_val = sensor_stats[sweep_sensor]["p90"]

    # Cek apakah P90 memang memicu fault
    test_hi = {**OK_BASE, sweep_sensor: hi_val}
    fp_at_hi = predict_bearing_fp(test_hi)
    if fp_at_hi < 0.5:
        # P90 pun tidak cukup trigger -> coba max
        hi_val = sensor_stats[sweep_sensor]["max"]
        test_hi = {**OK_BASE, sweep_sensor: hi_val}
        fp_at_hi = predict_bearing_fp(test_hi)

    if fp_at_hi < 0.5:
        print(f"  {sweep_sensor:<22}  {lo_val:>9.3f}  {hi_val:>9.3f}  {'tidak trigger':>14}  {fp_at_hi*100:>15.1f}%")
        continue

    # Binary search
    lo, hi = lo_val, hi_val
    for _ in range(20):
        mid = (lo + hi) / 2
        test = {**OK_BASE, sweep_sensor: mid}
        fp_mid = predict_bearing_fp(test)
        if fp_mid >= 0.5:
            hi = mid
        else:
            lo = mid
    threshold = (lo + hi) / 2
    test_thresh = {**OK_BASE, sweep_sensor: threshold}
    fp_thresh = predict_bearing_fp(test_thresh)
    print(f"  {sweep_sensor:<22}  {lo_val:>9.3f}  {sensor_stats[sweep_sensor]['p90']:>9.3f}  {threshold:>14.3f}  {fp_thresh*100:>15.1f}%")


# ==========================================================================
# BAGIAN 6: Ringkasan fault probability dari semua eksperimen
# ==========================================================================
print("\n\n" + "=" * 110)
print("BAGIAN 6 -- CONTOH NILAI SENSOR YANG MENGHASILKAN FP BERBEDA")
print("Mencari sample dengan FP: <10%, 10-30%, 30-50%, 50-80%, >80%")
print("=" * 110)

all_exp = dataset_results + random_results

buckets = {
    "< 10%  (SG.RENDAH)": lambda f: f < 0.10,
    "10-30% (RENDAH)":    lambda f: 0.10 <= f < 0.30,
    "30-50% (SEDANG)":    lambda f: 0.30 <= f < 0.50,
    "50-80% (TINGGI)":    lambda f: 0.50 <= f < 0.80,
    ">= 80% (KRITIS)":   lambda f: f >= 0.80,
}

for comp in COMPONENTS:
    print(f"\n  [{COMP_NAMES[comp]}] -- contoh nilai FP berbeda:")
    for bucket_label, cond in buckets.items():
        matches = [d for d in all_exp if cond(fp(d["result"], comp))]
        if not matches:
            print(f"    {bucket_label}: (tidak ditemukan)")
        else:
            d = matches[0]
            sv = ", ".join(f"{f}={d['sensors'][f]:.2f}" for f in FEAT)
            print(f"    {bucket_label}: FP={fp(d['result'],comp)*100:.1f}%  HS={hs(d['result'],comp)*100:.1f}%  Risk={rl(d['result'],comp)}")
            print(f"      Sensor: {sv}")

print("\n\nSelesai.")
