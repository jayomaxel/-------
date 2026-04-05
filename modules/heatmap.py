from __future__ import annotations

from pathlib import Path

import numpy as np

from modules.reference_pipeline import generate_attention_heatmap


def generate_heatmap(
    image_array: np.ndarray | str | Path,
    dataset_key: str | None = None,
) -> np.ndarray:
    _ = dataset_key
    return generate_attention_heatmap(image_array)
