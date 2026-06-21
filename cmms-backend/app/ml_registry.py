"""
Registry ML: petakan machine_id aset → predictor class-nya.

Cara menambah mesin baru:
  1. Latih model, simpan ke:
       machine-learning filtered data/<nama_mesin>/models/
  2. Buat file predictors/<nama_mesin>.py mengikuti pola predictors/compressor.py
  3. Import class-nya di sini dan tambahkan entri ke REGISTRY.
"""
from app.predictors.compressor import CompressorPredictor

# ── Tambahkan baris baru di sini saat ada model mesin baru ──────────────────
# from app.predictors.cnc_milling import CNCMillingPredictor
# from app.predictors.conveyor   import ConveyorPredictor

REGISTRY: dict[str, type] = {
    # machine_id (dari field Asset.machine_id) → predictor class
    "CMP-DUMMY-001": CompressorPredictor,

    # Contoh mesin berikutnya (uncomment + isi setelah model siap):
    # "CNC-B2":    CNCMillingPredictor,
    # "CONV-C3":   ConveyorPredictor,
}
# ────────────────────────────────────────────────────────────────────────────


def get_predictor(machine_id: str):
    """
    Kembalikan instance predictor untuk machine_id yang diberikan.
    Return None jika mesin belum memiliki model ML.
    """
    cls = REGISTRY.get(machine_id)
    return cls() if cls else None


def registered_machine_ids() -> list[str]:
    """Daftar machine_id yang sudah terdaftar di registry."""
    return list(REGISTRY.keys())
