from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import sys
from typing import Literal


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_DIR = _base_dir()
RenderMode = Literal["horarios", "resultados"]


@dataclass(slots=True)
class AppConfig:
    excel_path: Path
    background_image_path: Path
    header_overlay_path: Path
    logos_dir: Path
    font_path: Path
    output_root_dir: Path
    basket_logo_path: Path
    club_logo_map_path: Path
    venue_map_path: Path
    cover_example_path: Path | None = None
    cover_font_bold_path: Path | None = None
    cover_font_italic_path: Path | None = None
    clupik_logo_path: Path | None = None
    cover_basket_logo_path: Path | None = None
    mode: RenderMode = "horarios"
    results_doc_path: Path | None = None
    results_overrides_path: Path | None = None
    max_per_page: int = 8
    number_font_path: Path | None = None
    cover_title_font_path: Path | None = None
    cover_date_font_path: Path | None = None
    cover_dark_overlay_opacity: float = 0.65


def default_config() -> AppConfig:
    return AppConfig(
        excel_path=BASE_DIR / "input" / "ejemplo.xlsx",
        background_image_path=BASE_DIR / "foto.png",
        header_overlay_path=BASE_DIR / "header.png",
        logos_dir=BASE_DIR / "logos",
        font_path=BASE_DIR / "fonts" / "Barlow-Bold.ttf",
        output_root_dir=BASE_DIR / "output",
        basket_logo_path=BASE_DIR / "logos" / "basket_aranjuez.png",
        club_logo_map_path=BASE_DIR / "data" / "club_logo_map.csv",
        venue_map_path=BASE_DIR / "data" / "venue_map.csv",
        cover_example_path=BASE_DIR / "cover.png",
        cover_font_bold_path=BASE_DIR / "fonts" / "Poppins-Bold.ttf",
        cover_font_italic_path=BASE_DIR / "fonts" / "Poppins-BoldItalic.ttf",
        clupik_logo_path=BASE_DIR / "logos" / "Clupik-logo.png",
        cover_basket_logo_path=BASE_DIR / "logos" / "cover_ba_logo.png",
        mode="horarios",
        results_doc_path=None,
        results_overrides_path=BASE_DIR / "data" / "result_overrides.json",
        max_per_page=8,
        number_font_path=BASE_DIR / "fonts" / "kvant-trial-bold.otf",
        cover_title_font_path=BASE_DIR / "fonts" / "kvant-trial-bold.otf",
        cover_date_font_path=BASE_DIR / "fonts" / "Amoresa Aged.otf",
        cover_dark_overlay_opacity=0.65,
    )


def apply_overrides(config: AppConfig, **overrides: object) -> AppConfig:
    clean_overrides = {key: value for key, value in overrides.items() if value is not None}
    return replace(config, **clean_overrides)
