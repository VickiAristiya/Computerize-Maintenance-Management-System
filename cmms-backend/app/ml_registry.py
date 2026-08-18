"""
Registry ML: petakan machine_id aset → model prediktifnya.

=== MENAMBAH MESIN BARU (jalur cepat) ======================================

  1. Latih model, simpan hasilnya ke:
       machine-learning filtered data/<folder>/models/
         - hybrid_model_<komponen>.pkl    (scaler, svm, feature_columns, class_names)
         - dnn_extractor_<komponen>.keras

  2. Tambahkan SATU entri di dict MACHINES di bawah.

  3. Verifikasi:
       venv/Scripts/python.exe scripts/cek_mesin.py <MACHINE_ID>

  Tidak perlu membuat file predictor baru, tidak perlu mengubah models.py,
  tidak perlu mengubah front-end. Nama fitur, nama komponen, dan label kelas
  dibaca otomatis dari bundle .pkl hasil training.

  REGISTRY (class-based) di bawah hanya menyimpan 4 mesin lama yang sudah
  terlanjur punya file predictor sendiri. Mesin baru cukup lewat MACHINES.
===========================================================================
"""
from app.predictors.compressor import CompressorPredictor
from app.predictors.induksi import InduksiPredictor
from app.predictors.forging import ForgingPredictor
from app.predictors.bor import BorPredictor
from app.predictors.generic import GenericHybridPredictor


# ── Mesin lama: predictor punya file sendiri (jangan diubah) ────────────────
REGISTRY: dict[str, type] = {
    "CMP-DUMMY-001": CompressorPredictor,
    "IND-001": InduksiPredictor,
    "FRG-002": ForgingPredictor,
    "DRL-001": BorPredictor,
}


# ── Mesin baru: cukup tambah satu entri di sini ─────────────────────────────
#
# Field wajib : folder, label
# Field opsional:
#   components      list komponen; kosongkan = deteksi otomatis dari nama file
#   component_names {komponen: "Nama tampilan"} untuk teks rekomendasi
#   ok_message      teks rekomendasi saat kondisi normal
#   fault_message   teks rekomendasi saat fault (kalimat urgensi otomatis)
#   aliases         {nama_kolom_model: [nama_yang_dikirim_sensor, ...]}
#                   dipakai kalau simulator/perangkat mengirim nama field beda
#
MACHINES: dict[str, dict] = {
    # Mesin Bubut — 6 sensor: daya aktif, suhu, getaran X/Y/Z, dan getaran
    # resultan (vrms). Model hybrid DNN-SVM, lih.
    # machine-learning filtered data/bubut/bubut_model.ipynb
    "BBT-001": {
        "folder": "bubut",
        "label": "Mesin Bubut",
        "component_names": {"status": "Spindle & Chuck"},
        "ok_message": "Mesin Bubut dalam kondisi normal — lanjutkan pemantauan rutin.",
        "fault_message": (
            "Mesin Bubut terindikasi fault — periksa getaran spindle, "
            "kesejajaran chuck, dan kondisi bearing headstock."
        ),
        # Power meter 3 fasa di mesin bubut mengirim daya aktif sebagai
        # "active_power_total_w", sedangkan model dilatih dengan kolom
        # "active_power_w" (dari header CSV "Active Power Total W"). Tanpa alias
        # ini satu field dianggap hilang dan seluruh prediksi ditolak — health
        # score mesin bubut tidak pernah terisi meski datanya masuk.
        "aliases": {"active_power_w": ["active_power_total_w"]},
    },
    #
    # Contoh entri baru — hapus komentar dan sesuaikan saat model mesin lain siap:
    #
    # "CNC-001": {
    #     "folder": "cnc",                       # machine-learning filtered data/cnc/models/
    #     "label": "Mesin CNC",
    #     "component_names": {"status": "Spindle & Servo"},
    #     "fault_message": "Mesin CNC terindikasi fault — periksa spindle dan servo drive.",
    #     "aliases": {"temp_c": ["temp", "suhu"]},
    # },
}
# ────────────────────────────────────────────────────────────────────────────


def get_predictor(machine_id: str):
    """
    Kembalikan instance predictor untuk machine_id yang diberikan.
    Return None jika mesin belum memiliki model ML.
    """
    cls = REGISTRY.get(machine_id)
    if cls:
        return cls()

    spec = MACHINES.get(machine_id)
    if not spec:
        return None

    return GenericHybridPredictor(
        folder=spec["folder"],
        machine_label=spec.get("label", machine_id),
        components=spec.get("components"),
        component_names=spec.get("component_names"),
        ok_message=spec.get("ok_message"),
        fault_message=spec.get("fault_message"),
    )


def registered_machine_ids() -> list[str]:
    """Daftar machine_id yang sudah terdaftar di registry."""
    return list(REGISTRY.keys()) + list(MACHINES.keys())


def registry_field_aliases() -> dict[str, list[str]]:
    """Gabungan alias field dari semua entri MACHINES (lih. ml_routes.FIELD_ALIASES)."""
    merged: dict[str, list[str]] = {}
    for spec in MACHINES.values():
        for canonical, aliases in (spec.get("aliases") or {}).items():
            merged.setdefault(canonical, [])
            merged[canonical].extend(a for a in aliases if a not in merged[canonical])
    return merged
