from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import ImageDraw, ImageFont

from .design import (
    BADGE_POLYGON, BAND_HEIGHT, BLACK, CANVAS_SIZE, FOOTER_POLYGON,
    INFO_BOX, LEFT_LOGO_BOX, LEFT_TEAM_BOX, MAX_MATCHES_PER_PAGE,
    RIGHT_LOGO_BOX, RIGHT_TEAM_BOX, ROW_HEIGHT, ROW_STRIDE, VS_BOX,
    WHITE, YELLOW,
)


@dataclass(slots=True)
class MatchSlot:
    left_logo_box: tuple[int, int, int, int]
    right_logo_box: tuple[int, int, int, int]
    left_team_box: tuple[int, int, int, int]
    vs_box: tuple[int, int, int, int]
    right_team_box: tuple[int, int, int, int]
    info_box: tuple[int, int, int, int]
    left_band_box: tuple[int, int, int, int]
    center_band_box: tuple[int, int, int, int]
    right_band_box: tuple[int, int, int, int]
    badge_polygon: tuple[tuple[int, int], ...]
    footer_polygon: tuple[tuple[int, int], ...]


@dataclass(slots=True)
class FittedText:
    lines: list[str]
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont
    line_height: int


def _shift(box: tuple[int, int, int, int], offset_y: int) -> tuple[int, int, int, int]:
    left, top, right, bottom = box
    return left, top + offset_y, right, bottom + offset_y


def get_match_slots(count: int) -> list[MatchSlot]:
    if not 0 <= count <= MAX_MATCHES_PER_PAGE:
        raise ValueError("Cada pagina admite entre 0 y 8 partidos.")
    slots: list[MatchSlot] = []
    for index in range(count):
        offset_y = index * ROW_STRIDE
        slots.append(
            MatchSlot(
                left_logo_box=_shift(LEFT_LOGO_BOX, offset_y),
                right_logo_box=_shift(RIGHT_LOGO_BOX, offset_y),
                left_team_box=_shift(LEFT_TEAM_BOX, offset_y),
                vs_box=_shift(VS_BOX, offset_y),
                right_team_box=_shift(RIGHT_TEAM_BOX, offset_y),
                info_box=_shift(INFO_BOX, offset_y),
                left_band_box=_shift((0, 0, 454, BAND_HEIGHT), offset_y),
                center_band_box=_shift((454, 0, 626, BAND_HEIGHT), offset_y),
                right_band_box=_shift((626, 0, CANVAS_SIZE[0], BAND_HEIGHT), offset_y),
                badge_polygon=tuple((x, y + offset_y) for x, y in BADGE_POLYGON),
                footer_polygon=tuple((x, y + offset_y) for x, y in FOOTER_POLYGON),
            )
        )
    return slots


def _load_font(font_path: Path, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return ImageFont.truetype(str(font_path), size=size)


def measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text or " ", font=font, stroke_width=0)
    return right - left, bottom - top


def _split_long_word(
    draw: ImageDraw.ImageDraw,
    word: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> tuple[str, str]:
    if not word:
        return "", ""
    current = ""
    for character in word:
        candidate = f"{current}{character}"
        width, _ = measure_text(draw, candidate, font)
        if width <= max_width or not current:
            current = candidate
        else:
            break

    if len(current) == len(word):
        return current, ""
    if not current:
        return word[0], word[1:]
    return current, word[len(current):]


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int | None = None,
) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = ""
    queue = words[:]
    while queue:
        word = queue.pop(0)
        candidate = word if not current else f"{current} {word}"
        width, _ = measure_text(draw, candidate, font)
        if width <= max_width:
            current = candidate
            continue

        if current:
            lines.append(current)
            if max_lines is not None and len(lines) > max_lines:
                return lines
            current = ""
            queue.insert(0, word)
            continue

        head, tail = _split_long_word(draw, word, font, max_width)
        lines.append(head)
        if max_lines is not None and len(lines) > max_lines:
            return lines
        if tail:
            queue.insert(0, tail)

    if current:
        lines.append(current)
    return lines


def truncate_to_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    wrapped = wrap_text(draw, text, font, max_width, max_lines=None)
    if len(wrapped) <= max_lines:
        return wrapped

    lines = wrapped[:max_lines]
    last_line = lines[-1].rstrip()
    while last_line:
        candidate = f"{last_line}…"
        width, _ = measure_text(draw, candidate, font)
        if width <= max_width:
            lines[-1] = candidate
            return lines
        last_line = last_line[:-1].rstrip()
    lines[-1] = "…"
    return lines


def fit_text_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: Path,
    max_width: int,
    max_height: int,
    base_size: int = 28,
    min_size: int = 18,
    max_lines: int = 3,
    line_spacing: int = 0,
) -> FittedText:
    for font_size in range(base_size, min_size - 1, -2):
        font = _load_font(font_path, font_size)
        lines = wrap_text(draw, text, font, max_width, max_lines=max_lines)
        if len(lines) > max_lines:
            continue

        line_height = max(1, max(measure_text(draw, line, font)[1] for line in lines))
        total_height = line_height * len(lines) + line_spacing * max(0, len(lines) - 1)
        if total_height <= max_height:
            return FittedText(lines=lines, font=font, line_height=line_height)

    font = _load_font(font_path, min_size)
    _, line_height = measure_text(draw, "Ag", font)
    height_limit = max(1, int((max_height + line_spacing) // (line_height + line_spacing)))
    lines = truncate_to_lines(draw, text, font, max_width, max_lines=min(max_lines, height_limit))
    line_height = max(1, max(measure_text(draw, line, font)[1] for line in lines))
    return FittedText(lines=lines, font=font, line_height=line_height)


def centered_text_origin(
    box: tuple[int, int, int, int],
    text_width: int,
    text_height: int,
) -> tuple[int, int]:
    left, top, right, bottom = box
    x = left + (right - left - text_width) // 2
    y = top + (bottom - top - text_height) // 2
    return x, y




