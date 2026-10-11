from __future__ import annotations

from collections import defaultdict
from datetime import date
import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from config import AppConfig
from .background import load_background
from .design import (
    CANVAS_SIZE, COVER_DATE_BOX, COVER_DATE_FONT_SIZE, COVER_LOGO_BOX,
    COVER_TITLE_BOX, COVER_TITLE_FONT_SIZE, RENDER_SCALE, WHITE, YELLOW,
)
from .models import RenderMode
from .typography import draw_text_block

MONTH_NAMES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def _join_span(values: list[str]) -> str:
    return values[0] if len(values) == 1 else ", ".join(values[:-1]) + " y " + values[-1]


def format_cover_dates(dates: list[date]) -> str:
    groups: dict[tuple[int, int], list[str]] = defaultdict(list)
    for current in sorted(set(dates)):
        groups[(current.year, current.month)].append(str(current.day))
    multiple_years = len({year for year, _ in groups}) > 1
    labels = [
        f"{_join_span(days)} de {MONTH_NAMES[month]}" + (f" de {year}" if multiple_years else "")
        for (year, month), days in groups.items()
    ]
    return _join_span(labels) if labels else ""


def cover_title(mode: RenderMode) -> str:
    if mode not in ("horarios", "resultados"):
        raise ValueError("El modo debe ser horarios o resultados.")
    return mode.upper()


def _scale_box(box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return tuple(value * RENDER_SCALE for value in box)


def _paste_cover_logo(canvas: Image.Image, path: Path | None, logger: logging.Logger) -> None:
    if path is None or not path.is_file():
        logger.warning("No se encontro el logo horizontal de portada en %s", path or "<vacio>")
        return
    try:
        with Image.open(path) as raw:
            logo = raw.convert("RGBA")
            bounds = logo.getchannel("A").getbbox()
            if bounds is None:
                raise ValueError("Logo completamente transparente")
            # The supplied full-canvas overlay contains a small transparent logo.
            logo = logo.crop(bounds)
            box = _scale_box(COVER_LOGO_BOX)
            logo = ImageOps.contain(logo, (box[2] - box[0], box[3] - box[1]), Image.Resampling.LANCZOS)
            canvas.alpha_composite(logo, (box[0], box[1] + (box[3] - box[1] - logo.height) // 2))
    except (OSError, ValueError) as exc:
        logger.warning("No se pudo abrir el logo de portada %s: %s", path, exc)


def render_cover(
    output_dir: Path, config: AppConfig, mode: RenderMode,
    dates: list[date], logger: logging.Logger,
) -> Path:
    canvas = load_background(
        config.background_image_path, tuple(value * RENDER_SCALE for value in CANVAS_SIZE),
        dark_opacity=config.cover_dark_overlay_opacity,
    )
    draw = ImageDraw.Draw(canvas)
    draw_text_block(
        draw, _scale_box(COVER_TITLE_BOX), cover_title(mode), config.cover_title_font_path,
        fill=YELLOW, base_size=COVER_TITLE_FONT_SIZE * RENDER_SCALE,
        min_size=24 * RENDER_SCALE, max_lines=1,
    )
    draw_text_block(
        draw, _scale_box(COVER_DATE_BOX), format_cover_dates(dates), config.cover_date_font_path,
        fill=WHITE, base_size=COVER_DATE_FONT_SIZE * RENDER_SCALE,
        min_size=20 * RENDER_SCALE, max_lines=2, line_spacing=4 * RENDER_SCALE,
    )
    _paste_cover_logo(canvas, config.cover_basket_logo_path, logger)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "portada.png"
    canvas.convert("RGB").resize(CANVAS_SIZE, Image.Resampling.LANCZOS).save(
        output_path, format="PNG", optimize=True, compress_level=6,
    )
    return output_path
