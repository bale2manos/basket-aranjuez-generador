from pathlib import Path
from queue import Queue
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from tests.generator_fixtures import make_config
from launcher import GeneratorApp


class LauncherTests(unittest.TestCase):
    def test_worker_reports_exception_as_text_without_accessing_tk(self):
        app = GeneratorApp.__new__(GeneratorApp)
        app.messages = Queue()
        with TemporaryDirectory() as tmp:
            config = make_config(Path(tmp))
            with patch("launcher.run_pipeline", side_effect=ValueError("Falta Amoresa")):
                app._run_generation(config)
        success, message, output = app.messages.get_nowait()
        self.assertFalse(success)
        self.assertIn("Falta Amoresa", message)
        self.assertIsNone(output)

    def test_worker_reports_completed_output(self):
        app = GeneratorApp.__new__(GeneratorApp)
        app.messages = Queue()
        result = Mock(images=[{}, {}, {}], rendered_count=10, skipped_count=0, output_dir=Path("output/jornada_2026-10-10/horarios"))
        with TemporaryDirectory() as tmp, patch("launcher.run_pipeline", return_value=result):
            app._run_generation(make_config(Path(tmp)))
        success, message, output = app.messages.get_nowait()
        self.assertTrue(success)
        self.assertIn("Partidos: 10", message)
        self.assertEqual(output, result.output_dir)


if __name__ == "__main__":
    unittest.main()
