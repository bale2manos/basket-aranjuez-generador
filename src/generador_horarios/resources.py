from __future__ import annotations

import math

from PIL import Image, ImageFont

from config import AppConfig
from .design import MAX_MATCHES_PER_PAGE


def validate_render_assets(config: AppConfig) -> None:
    errors: list[str] = []
    for label, path in (
        ("Barlow Bold (texto)", config.font_path),
        ("Kvant (VS y marcadores)", config.number_font_path),
        ("Kvant (titulo de portada)", config.cover_title_font_path),
        ("Amoresa (fecha de portada)", config.cover_date_font_path),
    ):
        if path is None or not path.is_file():
            errors.append(f"Falta la fuente {label}: {path or 'ruta sin configurar'}")
            continue
        try:
            ImageFont.truetype(str(path), size=24)
        except OSError:
            errors.append(f"No se puede abrir la fuente {label}: {path}")

    if not config.background_image_path.is_file():
        errors.append(f"Falta la foto de fondo: {config.background_image_path}")
    else:
        try:
            with Image.open(config.background_image_path) as image:
                image.verify()
        except (OSError, ValueError):
            errors.append(f"La foto de fondo no es una imagen valida: {config.background_image_path}")

    if isinstance(config.max_per_page, bool) or not isinstance(config.max_per_page, int) or not 1 <= config.max_per_page <= MAX_MATCHES_PER_PAGE:
        errors.append("max_per_page debe ser un entero entre 1 y 8.")
    if config.mode not in ("horarios", "resultados"):
        errors.append("El modo debe ser horarios o resultados.")
    if not math.isfinite(config.cover_dark_overlay_opacity) or not 0 <= config.cover_dark_overlay_opacity <= 1:
        errors.append("cover_dark_overlay_opacity debe estar entre 0 y 1.")
    if errors:
        raise ValueError("No se puede generar el diseno 26/27:\n" + "\n".join(errors))
