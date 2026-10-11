from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps


def _trim_black_left_border(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    trim = 0
    for x in range(min(32, rgb.width // 50)):
        if all(max(rgb.getpixel((x, y))) <= 8 for y in range(0, rgb.height, max(1, rgb.height // 240))):
            trim = x + 1
        else:
            break
    return image.crop((trim, 0, image.width, image.height)) if trim else image


def load_background(path: Path, size: tuple[int, int], *, dark_opacity: float = 0.0) -> Image.Image:
    with Image.open(path) as raw:
        image = _trim_black_left_border(ImageOps.exif_transpose(raw).convert("RGB"))
        grayscale = ImageOps.grayscale(image).convert("RGBA")
        canvas = ImageOps.fit(grayscale, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    if dark_opacity:
        canvas.alpha_composite(Image.new("RGBA", size, (0, 0, 0, round(dark_opacity * 255))))
    return canvas
