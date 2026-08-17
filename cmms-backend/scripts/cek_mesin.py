# /cmms-backend/scripts/cek_mesin.py
"""
Verifikasi integrasi model ML sebuah mesin — dipakai setelah menambah mesin
baru ke app/ml_registry.py, sebelum menyalakan backend.

Script ini memeriksa satu per satu hal yang biasanya bikin integrasi gagal:
  1. machine_id sudah terdaftar di registry?
  2. File model (.pkl + .keras) lengkap di folder yang benar?
  3. Bundle .pkl berisi kunci yang dibutuhkan (scaler, svm, feature_columns)?
  4. Inferensi benar-benar jalan (smoke test pakai nilai tengah data training)?

Lalu mencetak bahan yang siap dipakai:
  - daftar nama field sensor yang HARUS dikirim ke POST /api/ml/sensor-data
  - contoh payload JSON
  - blok SENSOR_FIELDS siap tempel untuk config.py simulator

Jalankan dari folder cmms-backend:
    venv/Scripts/python.exe -m scripts.cek_mesin <MACHINE_ID>
    venv/Scripts/python.exe -m scripts.cek_mesin            (lihat semua mesin)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml_registry import get_predictor, registered_machine_ids

OK = "[OK]  "
BAD = "[GAGAL]"


def _first_bundle(predictor):
    """Bundle .pkl komponen pertama — untuk predictor generik maupun yang lama."""
    if hasattr(predictor, "_bundle") and getattr(predictor, "components", None):
        return predictor._bundle(predictor.components[0])
    predictor._ensure_loaded()          # predictor lama: cache di ._bundles
    return next(iter(predictor._bundles.values()))


def _components(predictor):
    comps = getattr(predictor, "components", None)
    if comps:
        return list(comps)
    module = sys.modules[type(predictor).__module__]
    return list(getattr(module, "COMPONENTS", []))


def _sample_values(predictor):
    """Nilai contoh per fitur: titik tengah rentang data training (dari MinMaxScaler)."""
    bundle = _first_bundle(predictor)
    scaler = bundle["scaler"]
    cols = list(bundle["feature_columns"])
    lo = getattr(scaler, "data_min_", None)
    hi = getattr(scaler, "data_max_", None)
    if lo is None or hi is None:
        return {c: 1.0 for c in cols}
    return {c: round(float((lo[i] + hi[i]) / 2), 4) for i, c in enumerate(cols)}


def cek(machine_id):
    print(f"\n=== Cek integrasi model: {machine_id} ===\n")

    predictor = get_predictor(machine_id)
    if predictor is None:
        print(f"{BAD} '{machine_id}' belum terdaftar di app/ml_registry.py")
        print("        Tambahkan entri di dict MACHINES, lalu jalankan lagi.")
        print(f"        Terdaftar saat ini: {', '.join(registered_machine_ids())}")
        return False
    print(f"{OK} Terdaftar di registry ({type(predictor).__name__})")

    if not predictor.is_ready():
        print(f"{BAD} File model belum lengkap:")
        for path in predictor.missing_model_files():
            print(f"        - {path}")
        return False
    print(f"{OK} File model lengkap di {predictor.models_dir}")

    try:
        features = predictor.feature_columns
    except Exception as exc:
        print(f"{BAD} Gagal membaca feature_columns dari bundle .pkl: {exc}")
        return False

    print(f"{OK} Komponen  : {', '.join(_components(predictor))}")
    print(f"{OK} Fitur ({len(features)}) : {', '.join(features)}")

    sample = _sample_values(predictor)
    try:
        result = predictor.predict(sample)
    except Exception as exc:
        print(f"{BAD} Inferensi error: {exc}")
        return False

    if not result.get("ok"):
        print(f"{BAD} Inferensi menolak payload: {result}")
        return False

    print(
        f"{OK} Smoke test inferensi jalan - prediction={result['prediction']}, "
        f"risk={result['risk_level']}, health={result['health_score']:.3f}"
    )

    payload = {"machine_id": machine_id, **sample}
    print("\n--- Contoh payload POST /api/ml/sensor-data ---")
    print(json.dumps(payload, indent=2))

    print("\n--- Blok SENSOR_FIELDS untuk config.py simulator ---")
    print("SENSOR_FIELDS = [")
    for col in features:
        print(f'    ("{col}", "{col.replace("_", " ").title()}", "", {sample[col]}),')
    print("]")

    print("\nSisa langkah manual: pastikan aset dengan machine_id "
          f"'{machine_id}' sudah ada di database CMMS.\n")
    return True


def main():
    if len(sys.argv) > 1:
        sys.exit(0 if cek(sys.argv[1]) else 1)

    ids = registered_machine_ids()
    print(f"Mesin terdaftar: {', '.join(ids)}")
    gagal = [mid for mid in ids if not cek(mid)]
    if gagal:
        print(f"\nMesin bermasalah: {', '.join(gagal)}")
    sys.exit(1 if gagal else 0)


if __name__ == "__main__":
    main()
