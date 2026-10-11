import logging
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image, ImageDraw

from tests.generator_fixtures import make_config, make_match
from generador_horarios.design import LOSER_BAND_ALPHA, RENDER_SCALE, YELLOW
from generador_horarios.layout import get_match_slots
from generador_horarios.renderer import (
    _draw_match_band, _parse_result_scores, _paste_logo,
    _resolve_band_alphas, _scale_slot, render_page,
)
from generador_horarios.models import PageSpec
from generador_horarios.typography import draw_text_block


class RendererTests(unittest.TestCase):
    def test_score_orients_losing_side_and_ties_stay_opaque(self):
        for score, alphas in (("45-90", (89, 255)), ("123-100", (255, 89)), ("55-55", (255, 255))):
            with self.subTest(score=score):
                self.assertEqual(_resolve_band_alphas(make_match(mode="resultados", score=score)), alphas)
        self.assertEqual(_resolve_band_alphas(make_match(score="45-90")), (255, 255))

    def test_losing_band_composites_over_photo_not_opaque_black(self):
        canvas = Image.new("RGBA", (1080, 1350), (100, 150, 200, 255))
        _draw_match_band(canvas, get_match_slots(1)[0], make_match(mode="resultados", score="45-90"))
        self.assertEqual(LOSER_BAND_ALPHA, 89)
        self.assertEqual(canvas.getpixel((10, 10)), (65, 98, 130, 255))
        self.assertEqual(canvas.getpixel((700, 10)), (0, 0, 0, 255))
        self.assertEqual(canvas.getpixel((540, 10)), (0, 0, 0, 255))

    def test_results_remove_footer_and_schedule_keeps_it(self):
        for mode in ("horarios", "resultados"):
            with self.subTest(mode=mode):
                canvas = Image.new("RGBA", (1080, 1350), (100, 150, 200, 255))
                _draw_match_band(canvas, get_match_slots(1)[0], make_match(mode=mode, score="90-45"))
                self.assertEqual(canvas.getpixel((540, 135)), (0, 0, 0, 255) if mode == "horarios" else (100, 150, 200, 255))

    def test_parse_score_requires_complete_score(self):
        self.assertEqual(_parse_result_scores("123 - 145"), (123, 145))
        self.assertIsNone(_parse_result_scores("VS"))
        self.assertIsNone(_parse_result_scores("parcial 45-90"))

    def test_badge_labels_fit_without_truncation(self):
        with TemporaryDirectory() as tmp:
            config = make_config(Path(tmp))
            box = _scale_slot(get_match_slots(1)[0], RENDER_SCALE).vs_box
            for text in ("VS", "123-145", "PLAYOFFS"):
                with self.subTest(text=text):
                    canvas = Image.new("RGBA", (2160, 2700), (0, 0, 0, 0))
                    font = config.font_path if text == "PLAYOFFS" else config.number_font_path
                    fitted = draw_text_block(ImageDraw.Draw(canvas), box, text, font, fill=YELLOW,
                                             base_size=108 if text == "VS" else 64,
                                             min_size=28, max_lines=1)
                    self.assertEqual(fitted.lines, [text])
                    left, top, right, bottom = canvas.getbbox()
                    self.assertGreaterEqual(left, box[0])
                    self.assertGreaterEqual(top, box[1])
                    self.assertLessEqual(right, box[2])
                    self.assertLessEqual(bottom, box[3])

    def test_transparent_logo_padding_does_not_change_visual_size(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            bounds = []
            for size, inset in ((100, 10), (300, 90)):
                logo = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                ImageDraw.Draw(logo).rectangle((inset, inset, size - inset - 1, size - inset - 1), fill="red")
                path = base / f"logo{size}.png"
                logo.save(path)
                canvas = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
                self.assertTrue(_paste_logo(canvas, path, (10, 10, 110, 110), logging.getLogger("logos"), "test", draw_circle=False))
                bounds.append(canvas.getbbox())
            self.assertEqual(bounds[0], bounds[1])

    def test_missing_or_corrupt_logo_is_partial_failure(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(base)
            corrupt = base / "corrupt.png"
            corrupt.write_bytes(b"not an image")
            records = [make_match(1), make_match(2)]
            records[0].local_logo_path = config.basket_logo_path
            records[1].local_logo_path = corrupt
            path = base / "page.png"
            render_page(PageSpec("local", 1, path, records), config, logging.getLogger("partial_logos"))
            self.assertTrue(path.is_file())
            self.assertTrue(all(record.status == "rendered_missing_logo" for record in records))


if __name__ == "__main__":
    unittest.main()
