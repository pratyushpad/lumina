import base64
from pathlib import Path


def encode_image_base64(image_path: str) -> tuple[str, str]:
    """Return (base64_string, mime_type)."""
    ext = Path(image_path).suffix.lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8"), mime
