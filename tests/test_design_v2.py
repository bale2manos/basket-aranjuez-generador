from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import json

from PIL import Image

from tests.generator_fixtures import create_eight_match_inputs, make_config
from config import apply_overrides
from generador_horarios.pipeline import run_pipeline
from generador_horarios.resources import validate_render_assets


class DesignResourceTests(unittest.TestCase):
    def test_full_eight_match_page_in_both_modes_and_away_page(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            excel, docx = create_eight_match_inputs(base)
            config = make_config(base, excel_path=excel, results_doc_path=docx)
            for mode in ("horarios", "resultados"):
                with self.subTest(mode=mode):
                    result = run_pipeline(apply_overrides(config, mode=mode))
                    self.assertEqual(result.rendered_count, 10)
                    self.assertEqual(result.skipped_count, 0)
                    self.assertEqual(len(result.images), 3)
                    summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
                    self.assertEqual(summary["design_version"], "2.0")
                    self.assertEqual(summary["season"], "2026/27")
                    self.assertEqual(summary["images"][1]["match_count"], 8)
                    self.assertEqual(summary["images"][2]["match_count"], 2)
                    if mode == "horarios":
                        self.assertEqual(summary["items"][0]["middle_text"], "PLAYOFFS")
                    else:
                        self.assertEqual(summary["items"][0]["result_text"], "45-90")
                        self.assertTrue(all(item["result_source"] == "docx" for item in summary["items"]))
                    with Image.open(result.output_dir / "local1.png") as image:
                        self.assertEqual(image.size, (1080, 1350))
                        self.assertEqual(image.getpixel((467, 1226)), (253, 207, 33))

    def test_missing_assets_are_reported_together_before_output_writes(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(base, number_font_path=base / "kvant.otf", cover_date_font_path=base / "amoresa.otf", background_image_path=base / "photo.jpg")
            with self.assertRaises(ValueError) as error:
                run_pipeline(config)
            self.assertIn("Kvant", str(error.exception))
            self.assertIn("Amoresa", str(error.exception))
            self.assertIn("foto de fondo", str(error.exception))
            self.assertFalse(config.output_root_dir.exists())
            self.assertFalse(config.club_logo_map_path.exists())

    def test_invalid_font_has_controlled_error(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            bad = base / "font.otf"
            bad.write_bytes(b"not a font")
            with self.assertRaisesRegex(ValueError, "No se puede abrir la fuente"):
                validate_render_assets(make_config(base, number_font_path=bad))

    def test_page_size_and_opacity_are_validated(self):
        with TemporaryDirectory() as tmp:
            config = make_config(Path(tmp))
            validate_render_assets(config)
            for value in (0, 9, -1, True):
                with self.subTest(max_per_page=value), self.assertRaises(ValueError):
                    validate_render_assets(apply_overrides(config, max_per_page=value))
            for value in (-0.1, 1.1, float("nan")):
                with self.subTest(opacity=value), self.assertRaises(ValueError):
                    validate_render_assets(apply_overrides(config, cover_dark_overlay_opacity=value))


if __name__ == "__main__":
    unittest.main()
