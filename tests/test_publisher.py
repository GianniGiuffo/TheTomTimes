import json
import os
import subprocess
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from backend.main import publish


class PublisherTest(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.site = self.root / "site"
        self.source = self.root / "edition.json"
        self.date = "2026-11-13"
        self.target = self.site / "content/daily/2026-11-13.md"
        fixtures = ["static/img/demo.webp", "static/video/demo.mp4", "content/prova.md"]
        for fixture in fixtures:
            path = self.site / fixture
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        self.edition = {
            "date": self.date,
            "title": "Edizione di prova",
            "featured": {
                "title": "L’orbita & il cielo",
                "category": "Scienza",
                "summary": 'Una storia "di prova" con un simbolo <.',
                "image": "img/demo.webp",
                "slug": "prova",
            },
            "stories": [],
            "videos": [{
                "title": "Una clip",
                "category": "Scienza",
                "summary": "Clip dimostrativa",
                "image": "img/demo.webp",
                "source": "video/demo.mp4",
            }],
        }

    def write_input(self, data=None):
        self.source.write_text(json.dumps(self.edition if data is None else data), encoding="utf-8")

    def test_create_regenerate_and_preserve_other_editions(self):
        self.target.parent.mkdir()
        self.target.write_text("Vecchia edizione", encoding="utf-8")
        older = self.target.with_name("2026-11-09.md")
        older.write_bytes(b"older edition")
        self.write_input()

        self.assertEqual(publish(self.source, self.date, self.site), (self.target, True))
        metadata = json.loads(self.target.read_text(encoding="utf-8"))
        self.assertEqual(metadata["date"], self.date)
        self.assertEqual(metadata["description"], self.edition["featured"]["summary"])
        self.assertEqual(metadata["params"]["featured"], self.edition["featured"])
        self.assertEqual(metadata["params"]["videos"], self.edition["videos"])
        if os.name == "posix":
            self.assertEqual(self.target.stat().st_mode & 0o777, 0o644)
        timestamp = self.target.stat().st_mtime_ns

        self.assertEqual(publish(self.source, self.date, self.site), (self.target, False))
        self.assertEqual(self.target.stat().st_mtime_ns, timestamp)
        self.edition["featured"]["summary"] = "Riassunto aggiornato"
        self.write_input()
        self.assertEqual(publish(self.source, self.date, self.site), (self.target, True))
        self.assertIn("Riassunto aggiornato", self.target.read_text(encoding="utf-8"))
        self.assertEqual(older.read_bytes(), b"older edition")
        self.assertEqual(set(self.target.parent.iterdir()), {self.target, older})

    def test_invalid_card_or_date_preserves_existing_edition(self):
        self.write_input()
        publish(self.source, self.date, self.site)
        original = self.target.read_bytes()
        invalid = (
            ("date", None, "2026-02-30", "data valida"),
            ("date", None, "2026-11-12", "mentre --date"),
            ("featured", "image", "../demo.webp", "percorso non valido"),
            ("featured", "image", "img/missing.webp", "file locale mancante"),
            ("featured", "slug", "inesistente", "file locale mancante"),
            ("featured", "title", " ", "testo non vuoto"),
            ("featured", "summary", "Uno\nDue", "una sola riga"),
            ("stories", None, [self.edition["featured"]], "titolo di notizia duplicato"),
            ("stories", None, {}, "array JSON"),
            ("draft", None, True, "campi sconosciuti"),
            ("videos", None, [{**self.edition["videos"][0], "source": "video/missing.mp4"}],
             "file locale mancante"),
        )
        for field, key, value, error in invalid:
            with self.subTest(field=field, key=key, value=value):
                data = deepcopy(self.edition)
                if key is None:
                    data[field] = value
                else:
                    data[field][key] = value
                self.write_input(data)
                with self.assertRaisesRegex(ValueError, error):
                    publish(self.source, self.date, self.site)
                self.assertEqual(self.target.read_bytes(), original)

    def test_bad_json_exits_nonzero_without_creating_edition(self):
        cli = Path(__file__).resolve().parents[1] / "backend/main.py"
        for payload, message in (("{", "line 1"), ('{"date":1,"date":2}', "Chiave JSON ripetuta")):
            with self.subTest(payload=payload):
                self.source.write_text(payload, encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(cli), "--input", str(self.source),
                     "--date", self.date, "--site", str(self.site)],
                    capture_output=True, text=True, check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertFalse(self.target.exists())

    def test_new_edition_without_videos(self):
        self.edition.pop("videos")
        self.write_input()
        self.assertEqual(publish(self.source, self.date, self.site), (self.target, True))
        metadata = json.loads(self.target.read_text(encoding="utf-8"))
        self.assertEqual(metadata["params"]["videos"], [])

    def test_replace_failure_leaves_original_and_cleans_temporary_file(self):
        self.write_input()
        publish(self.source, self.date, self.site)
        original = self.target.read_bytes()
        self.edition["title"] = "Titolo aggiornato"
        self.write_input()
        with patch.object(Path, "replace", side_effect=PermissionError("file bloccato")):
            with self.assertRaises(PermissionError):
                publish(self.source, self.date, self.site)
        self.assertEqual(self.target.read_bytes(), original)
        self.assertEqual(list(self.target.parent.iterdir()), [self.target])
