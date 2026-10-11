from datetime import date, time
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from config import apply_overrides, default_config
from generador_horarios.models import MatchRecord


def make_config(base: Path, **overrides):
    background = base / "background.png"
    Image.new("RGB", (1200, 1500), (120, 160, 180)).save(background)
    config = apply_overrides(
        default_config(),
        excel_path=base / "partidos.xlsx", background_image_path=background,
        output_root_dir=base / "output", club_logo_map_path=base / "clubs.csv",
        venue_map_path=base / "venues.csv", results_overrides_path=base / "results.json",
        font_path=ROOT / "fonts" / "Barlow-Bold.ttf",
        number_font_path=ROOT / "fonts" / "kvant-trial-bold.otf",
        cover_title_font_path=ROOT / "fonts" / "kvant-trial-bold.otf",
        cover_date_font_path=ROOT / "fonts" / "Amoresa Aged.otf",
        basket_logo_path=ROOT / "logos" / "basket_aranjuez.png",
        cover_basket_logo_path=ROOT / "logos" / "cover_ba_logo.png",
        logos_dir=ROOT / "logos",
    )
    return apply_overrides(config, **overrides)


def make_match(index=1, mode="horarios", score=None):
    return MatchRecord(
        row_index=index, categoria="Junior Masc. Pref.",
        local_original="BASKET ARANJUEZ C", visitante_original="RIVAL",
        fecha=date(2026, 10, 10), hora=time(13, 15), campo_original="Las Olivas",
        page_type="local", local_display="Junior Masc C", visitante_display="Torrejon Spartans",
        venue_display="Las Olivas", render_mode=mode,
        middle_text=score or "VS", result_text=score,
    )


def create_eight_match_inputs(base: Path):
    """Synthetic scores for validation only; never used as a club result feed."""
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill
    from tests.test_pipeline import create_test_docx

    rows = [
        ("Junior Masc. Pref.", "BASKET ARANJUEZ C", "FUENTELARREYNA", "45-90"),
        ("Junior Masc. Pref.", "BASKET ARANJUEZ D", "C.D.I. ROZASBASKET", "123-100"),
        ("Junior Masc. Pref.", "BASKET ARANJUEZ C", "BRAINS MORALEJA", "55-55"),
        ("Cadete Fem. 1\u00baa\u00f1o", "BASKET ARANJUEZ BLANCO", "Colegio con un nombre extremadamente largo para verificar el ajuste y el truncado del texto", "100-123"),
        ("Infantil Fem. 1\u00baa\u00f1o", "BASKET ARANJUEZ POSTAS TAPERIA", "LICEO FRANCES", "62-45"),
        ("Senior Masc ORO", "BASKET ARANJUEZ A", "SAN AGUSTIN MADRID A", "90-45"),
        ("Alv Fem 2\u00baa\u00f1o", "BASKET ARANJUEZ NEGRO", "BALONCESTO ARISTOS A", "34-67"),
        ("Junior Masc. Pref.", "BASKET ARANJUEZ MISTER PIXEL", "CB COSLADA", "99-100"),
        ("Liga Ginos Femenina", "SAN AGUSTIN MADRID A", "BASKET ARANJUEZ", "80-76"),
        ("Sub22", "CB COSLADA", "BASKET ARANJUEZ B", "91-92"),
    ]
    base.mkdir(parents=True, exist_ok=True)
    excel = base / "DEMO_partidos.xlsx"
    docx = base / "DEMO_resultados_ficticios.docx"
    book = Workbook()
    sheet = book.active
    sheet.append(["Categor\u00eda", "Local", "Visitante", "Fecha", "Hora", "Campo de juego"])
    paragraphs = ["DEMO: marcadores sinteticos para verificar el programa"]
    for index, (category, local, visitor, score) in enumerate(rows):
        sheet.append([category, local, visitor, date(2026, 10, 10 if index < 8 else 11), time(13, 15), "LAS OLIVAS, CIUDAD DEPORTIVA"])
        paragraphs.extend((category, f"{local} {score} {visitor}"))
    for cell in sheet[2]:
        cell.fill = PatternFill(fill_type="solid", fgColor="FFFFFF00")
    book.save(excel)
    create_test_docx(docx, paragraphs)
    return excel, docx
