from __future__ import annotations

from dataclasses import fields
import logging
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from config import AppConfig
from .background import load_background
from .design import (
    BADGE_FONT_SIZE, BASKET_LOGO_SCALE, BLACK, CANVAS_SIZE, LOSER_BAND_ALPHA,
    PLAYOFF_FONT_SIZE, RENDER_SCALE, RIVAL_LOGO_SCALE, SCHEDULE_FONT_SIZE,
    SCHEDULE_MIN_FONT_SIZE, SCORE_FONT_SIZE, TEAM_FONT_SIZE,
    TEAM_LINE_SPACING, TEAM_MIN_FONT_SIZE, WHITE, YELLOW,
)
from .layout import MatchSlot, get_match_slots
from .models import MatchRecord, PageSpec
from .normalization import format_schedule_line
from .typography import draw_text_block


def _scale_box(box: tuple[int, int, int, int], scale: int) -> tuple[int, int, int, int]:
    return tuple(value * scale for value in box)


def _scale_slot(slot: MatchSlot, scale: int) -> MatchSlot:
    values = {}
    for field in fields(slot):
        shape = getattr(slot, field.name)
        values[field.name] = (
            tuple((x * scale, y * scale) for x, y in shape)
            if field.name.endswith("polygon") else _scale_box(shape, scale)
        )
    return MatchSlot(**values)


def _same_path(left: Path | None, right: Path | None) -> bool:
    return left is not None and right is not None and left.resolve() == right.resolve()


def _parse_result_scores(result_text: str | None) -> tuple[int, int] | None:
    match = re.fullmatch(r"\s*(\d+)\s*[-\u2013\u2014\u2212]\s*(\d+)\s*", result_text or "")
    return (int(match.group(1)), int(match.group(2))) if match else None


def _resolve_band_alphas(match: MatchRecord) -> tuple[int, int]:
    if match.render_mode == "resultados":
        scores = _parse_result_scores(match.result_text or match.middle_text)
        if scores:
            if scores[0] < scores[1]:
                return LOSER_BAND_ALPHA, 255
            if scores[1] < scores[0]:
                return 255, LOSER_BAND_ALPHA
    return 255, 255


def _draw_match_band(canvas: Image.Image, slot: MatchSlot, match: MatchRecord) -> None:
    left_alpha, right_alpha = _resolve_band_alphas(match)
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for box, alpha in ((slot.left_band_box, left_alpha), (slot.center_band_box, 255), (slot.right_band_box, right_alpha)):
        draw.rectangle((box[0], box[1], box[2] - 1, box[3] - 1), fill=(0, 0, 0, alpha))
    if match.render_mode == "horarios":
        draw.polygon(slot.footer_polygon, fill=BLACK)
    canvas.alpha_composite(overlay)


def _paste_logo(
    canvas: Image.Image, logo_path: Path | None, circle_box: tuple[int, int, int, int],
    logger: logging.Logger, warning_label: str, *, draw_circle: bool = True,
    scale: float = RIVAL_LOGO_SCALE,
) -> bool:
    if draw_circle:
        ImageDraw.Draw(canvas).ellipse(circle_box, fill=WHITE)
    if logo_path is None or not logo_path.is_file():
        logger.warning("%s: falta logo en %s", warning_label, logo_path or "<vacio>")
        return False
    try:
        with Image.open(logo_path) as raw:
            logo = raw.convert("RGBA")
            bounds = logo.getchannel("A").getbbox()
            if bounds is None:
                raise ValueError("Logo completamente transparente")
            logo = logo.crop(bounds)
            logo = ImageOps.contain(logo, (
                round((circle_box[2] - circle_box[0]) * scale),
                round((circle_box[3] - circle_box[1]) * scale),
            ), Image.Resampling.LANCZOS)
            x = circle_box[0] + (circle_box[2] - circle_box[0] - logo.width) // 2
            y = circle_box[1] + (circle_box[3] - circle_box[1] - logo.height) // 2
            canvas.alpha_composite(logo, (x, y))
        return True
    except (OSError, ValueError) as exc:
        logger.warning("%s: logo no valido %s (%s)", warning_label, logo_path, exc)
        return False


def _draw_match(
    canvas: Image.Image, slot: MatchSlot, match: MatchRecord,
    config: AppConfig, logger: logging.Logger, scale: int,
) -> bool:
    _draw_match_band(canvas, slot, match)
    draw = ImageDraw.Draw(canvas)
    draw.polygon(slot.badge_polygon, fill=YELLOW)
    logos_ok = []
    for path, box, text, text_box, label in (
        (match.local_logo_path, slot.left_logo_box, match.local_display, slot.left_team_box, "local"),
        (match.visitante_logo_path, slot.right_logo_box, match.visitante_display, slot.right_team_box, "visitante"),
    ):
        is_basket = _same_path(path, config.basket_logo_path)
        logos_ok.append(_paste_logo(
            canvas, path, box, logger, f"Fila {match.row_index} logo {label}",
            draw_circle=not is_basket, scale=BASKET_LOGO_SCALE if is_basket else RIVAL_LOGO_SCALE,
        ))
        draw_text_block(
            draw, text_box, text, config.font_path, fill=YELLOW,
            base_size=TEAM_FONT_SIZE * scale, min_size=TEAM_MIN_FONT_SIZE * scale,
            line_spacing=TEAM_LINE_SPACING * scale, align="left",
        )

    is_playoff_label = match.render_mode == "horarios" and match.middle_text == "PLAYOFFS"
    badge_font = config.font_path if is_playoff_label else config.number_font_path
    badge_size = PLAYOFF_FONT_SIZE if is_playoff_label else (SCORE_FONT_SIZE if match.render_mode == "resultados" else BADGE_FONT_SIZE)
    draw_text_block(
        draw, slot.vs_box, match.middle_text, badge_font, fill=BLACK,
        base_size=badge_size * scale, min_size=14 * scale, max_lines=1,
    )
    if match.render_mode == "horarios":
        draw_text_block(
            draw, slot.info_box, format_schedule_line(match.fecha, match.hora, match.venue_display),
            config.font_path, fill=YELLOW, base_size=SCHEDULE_FONT_SIZE * scale,
            min_size=SCHEDULE_MIN_FONT_SIZE * scale, max_lines=2, line_spacing=scale,
        )
    return all(logos_ok)


def render_page(page: PageSpec, config: AppConfig, logger: logging.Logger) -> None:
    render_size = tuple(value * RENDER_SCALE for value in CANVAS_SIZE)
    canvas = load_background(config.background_image_path, render_size)
    for slot, match in zip(get_match_slots(len(page.matches)), page.matches):
        logos_ok = _draw_match(canvas, _scale_slot(slot, RENDER_SCALE), match, config, logger, RENDER_SCALE)
        if match.status != "skipped":
            match.status = "rendered" if logos_ok else "rendered_missing_logo"
    page.output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").resize(CANVAS_SIZE, Image.Resampling.LANCZOS).save(
        page.output_path, format="PNG", optimize=True, compress_level=6,
    )
