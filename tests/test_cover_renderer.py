from datetime import date
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image, ImageDraw

from tests.generator_fixtures import make_config
from generador_horarios.background import load_background
from generador_horarios.cover_renderer import cover_title, format_cover_dates, render_cover
from generador_horarios.design import COVER_DATE_BOX, COVER_TITLE_BOX, RENDER_SCALE, WHITE
from generador_horarios.typography import draw_text_block


class CoverRendererTests(unittest.TestCase):
    def test_span_dates_are_sorted_unique_and_use_new_format(self):
        self.assertEqual(format_cover_dates([date(2026, 10, 10)]), "10 de Octubre")
        self.assertEqual(format_cover_dates([date(2026, 10, 11), date(2026, 10, 10), date(2026, 10, 10)]), "10 y 11 de Octubre")
        self.assertEqual(format_cover_dates([date(2026, 10, 10), date(2026, 10, 11), date(2026, 10, 12)]), "10, 11 y 12 de Octubre")
        self.assertEqual(format_cover_dates([date(2026, 10, 31), date(2026, 11, 1)]), "31 de Octubre y 1 de Noviembre")
        self.assertEqual(format_cover_dates([date(2026, 12, 31), date(2027, 1, 1)]), "31 de Diciembre de 2026 y 1 de Enero de 2027")

    def test_title_depends_on_mode(self):
        self.assertEqual(cover_title("horarios"), "HORARIOS")
        self.assertEqual(cover_title("resultados"), "RESULTADOS")

    def test_visible_italic_glyphs_and_titles_stay_in_boxes(self):
        with TemporaryDirectory() as tmp:
            config = make_config(Path(tmp))
            for text, box, font in (
                ("HORARIOS", COVER_TITLE_BOX, config.cover_title_font_path),
                ("RESULTADOS", COVER_TITLE_BOX, config.cover_title_font_path),
                ("10 y 11 de Octubre", COVER_DATE_BOX, config.cover_date_font_path),
                ("31 de Octubre y 1 de Noviembre", COVER_DATE_BOX, config.cover_date_font_path),
            ):
                with self.subTest(text=text):
                    canvas = Image.new("RGBA", (2160, 2700), (0, 0, 0, 0))
                    scaled = tuple(value * RENDER_SCALE for value in box)
                    fitted = draw_text_block(ImageDraw.Draw(canvas), scaled, text, font, fill=WHITE,
                                             base_size=480, min_size=40, max_lines=2)
                    self.assertNotIn("\u2026", " ".join(fitted.lines))
                    actual = canvas.getbbox()
                    self.assertGreaterEqual(actual[0], scaled[0])
                    self.assertGreaterEqual(actual[1], scaled[1])
                    self.assertLessEqual(actual[2], scaled[2])
                    self.assertLessEqual(actual[3], scaled[3])

    def test_cover_uses_shared_photo_with_darkening_and_only_left_logo(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(base)
            path = render_cover(base, config, "horarios", [date(2026, 10, 10), date(2026, 10, 11)], logging.getLogger("cover"))
            with Image.open(path) as raw:
                image = raw.convert("RGB")
                self.assertEqual(image.size, (1080, 1350))
                expected = load_background(config.background_image_path, image.size, dark_opacity=0.65)
                self.assertEqual(image.getpixel((900, 1200)), expected.getpixel((900, 1200))[:3])
                self.assertEqual(image.getpixel((400, 200)), expected.getpixel((400, 200))[:3])


if __name__ == "__main__":
    unittest.main()
