from __future__ import annotations

from pathlib import Path

from PIL import ImageDraw

from .layout import FittedText, fit_text_block


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font_path: Path,
    *,
    fill: str,
    base_size: int,
    min_size: int,
    max_lines: int = 3,
    line_spacing: int = 0,
    align: str = "center",
) -> FittedText:
    fitted = fit_text_block(
        draw, text, font_path, box[2] - box[0], box[3] - box[1],
        base_size=base_size, min_size=min_size, max_lines=max_lines,
        line_spacing=line_spacing,
    )
    height = len(fitted.lines) * fitted.line_height + max(0, len(fitted.lines) - 1) * line_spacing
    y = box[1] + (box[3] - box[1] - height) / 2
    for line in fitted.lines:
        left, top, right, bottom = draw.textbbox((0, 0), line, font=fitted.font)
        x = box[0] if align == "left" else box[0] + (box[2] - box[0] - (right - left)) / 2
        # Account for glyph bearings, including italic swashes and descenders.
        draw.text(
            (round(x - left), round(y + (fitted.line_height - (bottom - top)) / 2 - top)),
            line, font=fitted.font, fill=fill,
        )
        y += fitted.line_height + line_spacing
    return fitted
