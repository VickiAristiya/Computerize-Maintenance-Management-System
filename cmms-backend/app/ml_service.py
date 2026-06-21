# Backward compatibility — import dari lokasi baru
from app.predictors.compressor import (
    CompressorPredictor,
    COMPONENTS,
    COMPONENT_LABELS,
    COMPONENT_NAME_ID,
)

__all__ = ["CompressorPredictor", "COMPONENTS", "COMPONENT_LABELS", "COMPONENT_NAME_ID"]
