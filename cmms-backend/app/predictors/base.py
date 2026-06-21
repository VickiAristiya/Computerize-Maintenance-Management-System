"""
Base class untuk semua predictor mesin.
Setiap predictor mesin baru harus mewarisi class ini
dan mengimplementasikan semua method yang ada.
"""
from pathlib import Path
from abc import ABC, abstractmethod


class BasePredictor(ABC):
    """Interface wajib yang harus diimplementasikan setiap predictor."""

    # Root folder machine-learning (2 level di atas cmms-backend/app/)
    _ML_ROOT: Path = Path(__file__).resolve().parents[3] / "machine-learning filtered data"

    @property
    @abstractmethod
    def feature_columns(self) -> list[str]:
        """Daftar nama kolom fitur input model, sesuai urutan."""

    @abstractmethod
    def is_ready(self) -> bool:
        """True jika semua file model tersedia."""

    @abstractmethod
    def missing_model_files(self) -> list[str]:
        """Daftar path file model yang belum ada."""

    @abstractmethod
    def predict(self, payload: dict) -> dict:
        """
        Jalankan inferensi.
        payload: dict berisi nilai sensor (key = nama fitur)
        Return: dict dengan minimal key 'ok' (bool)
        """
