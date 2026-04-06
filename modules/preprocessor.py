from pathlib import Path
from typing import Union

import cv2
import numpy as np
from PIL import Image

import config


def _read_image_unicode_safe(image_path: Path) -> np.ndarray:
    """Read image with Unicode path support and keep original channels."""
    image_bytes = np.fromfile(str(image_path), dtype=np.uint8)
    image = cv2.imdecode(image_bytes, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"Failed to read image from path: {image_path}")
    return image


def preprocess_image(image_input: Union[Image.Image, str, Path, np.ndarray]) -> np.ndarray:
    """
    Preprocess an input image for downstream feature extraction and model inference.

    This function accepts one of three input formats:
    1. `PIL.Image.Image` object (e.g. from Streamlit uploader)
    2. Local image file path (`str` or `pathlib.Path`)
    3. In-memory image array (`np.ndarray`)

    Processing pipeline:
    1. Convert all input types to `np.ndarray`
    2. If RGBA/BGRA exists, remove alpha and convert to RGB
    3. Convert color space to RGB (OpenCV image arrays are assumed BGR/BGRA)
    4. Resize to `config.IMG_SIZE` with `cv2.INTER_AREA`
    5. Normalize to `[0, 1]` and cast to `np.float32`

    Args:
        image_input: PIL image, local image path, or numpy image array.

    Returns:
        np.ndarray: Float32 array in RGB format with shape `(224, 224, 3)`
        and value range `[0, 1]`.

    Raises:
        TypeError: If input type is unsupported.
        ValueError: If image data is invalid or cannot be decoded.
    """
    source = "cv2"

    if isinstance(image_input, Image.Image):
        image = np.array(image_input)
        source = "pil"
    elif isinstance(image_input, (str, Path)):
        path = Path(image_input)
        if not path.is_absolute():
            path = config.ROOT_DIR / path
        image = _read_image_unicode_safe(path)
    elif isinstance(image_input, np.ndarray):
        image = image_input
    else:
        raise TypeError(
            "Unsupported image_input type. Expected PIL.Image, str/Path, or np.ndarray."
        )

    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif image.ndim == 3 and image.shape[2] == 4:
        if source == "pil":
            image = image[:, :, :3]
        else:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
    elif image.ndim == 3 and image.shape[2] == 3:
        if source != "pil":
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    else:
        raise ValueError(f"Invalid image shape: {image.shape}")

    target_width, target_height = config.IMG_SIZE
    image = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)

    image = image.astype(np.float32) / 255.0
    image = np.clip(image, 0.0, 1.0)
    return image
