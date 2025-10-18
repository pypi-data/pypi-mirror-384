import io
import os
from functools import lru_cache

from PIL import Image, ImageDraw

from .s3 import read_s3_object_bytes

Image.MAX_IMAGE_PIXELS = None


@lru_cache
def read_file(file_path: str, allow_local=True) -> bytes:
    if file_path.startswith("s3://"):
        return read_s3_object_bytes(file_path)
    elif allow_local and os.path.isfile(file_path):
        with open(file_path, "rb") as f:
            return f.read()
    raise ValueError(f"File {file_path} does not exist or is not accessible.")


def read_image(file_path: str) -> Image.Image:
    content = read_file(file_path)
    image = Image.open(io.BytesIO(content))
    try:
        return image.convert("RGB")
    except Exception:
        # image is broken, return fake image
        fake_size = [*image.size]
        fake_image = Image.new("RGB", fake_size, (255, 255, 255))
        draw = ImageDraw.Draw(fake_image)
        draw.line((0, 0, *fake_size), fill=(255, 0, 0), width=10)
        draw.line((0, fake_size[1], fake_size[0], 0), fill=(255, 0, 0), width=10)
        return fake_image
