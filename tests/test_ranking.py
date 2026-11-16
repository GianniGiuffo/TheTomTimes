import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from backend.database import store_run
from backend.pipeline import main
from backend.ranking import score_stories, select_stories


NOW = datetime(2026, 11, 16, 12, tzinfo=timezone.utc)
INTERESTS = [
    {"category": "Tecnologia", "keywords": ["Linux", "open source"]},
    {"category": "Scienza", "keywords": ["NASA"]},
]
CONFIG = {
    "weights": {"interest": 60, "recency": 30, "source": 10},
    "recency_hours": 24,
    "source_priorities": {"Testata": 80},
    "default_source_priority": 50,
    "exclude_keywords": ["pubblicità"],
}


def story(title, *, summary="Notizia di prova.", hour=6, source="Testata"):
    return {
        "original_url": f"https://example.com/{'-'.join(title.lower().split())}",
        "title": title,
        "summary": summary,
        "published_at": f"2026-11-16T{hour:02d}:00:00Z",
        "source_name": source,
        "category": "Scienza",
    }


class RankingTest(unittest.TestCase):
    def test_formula_and_normalized_weights(self):
        card = story("Linux in produzione", summary="Un progetto open-source.")
        result = score_stories([card], INTERESTS, CONFIG, NOW)
        self.assertEqual(result, [(75.5, {**card, "category": "Tecnologia"})])
        config = {**CONFIG, "weights": {"interest": 1, "source": 0, "recency": 0}}
        self.assertEqual(score_stories([card], INTERESTS, config, NOW)[0][0], 75)

    def test_recency_and_source_priority_break_relevance_ties(self):
        fresh = story("Linux aggiornato", hour=12, source="Altra testata")
        preferred = story("Linux in azienda", hour=6)
        ordinary = story("Linux per utenti", hour=6, source="Altra testata")
        undated = story("Linux in ufficio")
        del undated["published_at"]
        ranked = score_stories([ordinary, undated, preferred, fresh], INTERESTS, CONFIG, NOW)
        self.assertEqual([card["title"] for _, card in ranked],
                         [item["title"] for item in (fresh, preferred, ordinary, undated)])

    def test_balance_filters_irrelevant_and_is_deterministic(self):
        cards = [story(f"Linux {number} open source") for number in range(12)]
        cards += [story("Missione NASA"), story("Linuxoid"), story("Linux pubblicità")]
        ranked = score_stories(cards, INTERESTS, CONFIG, NOW)
        self.assertEqual(len(ranked), 13)
        self.assertEqual(ranked, score_stories(reversed(cards), INTERESTS, CONFIG, NOW))
        selected = select_stories(ranked, 10)
        self.assertEqual(len(selected), 10)
        self.assertEqual(selected[-1][1]["title"], "Missione NASA")
        self.assertEqual([score for score, _ in selected], sorted((score for score, _ in selected), reverse=True))

    def test_manual_pipeline_publishes_saved_acquisition(self):
        with TemporaryDirectory() as temporary:
            project = Path(temporary)
            site = project / "site"
            site.mkdir()
            (site / "hugo.toml").touch()
            (project / "docker-compose.yml").touch()
            database = project / "data" / "news.sqlite3"
            day = NOW.date().isoformat()
            run_id, _, _ = store_run(database, NOW.date(), NOW, [story("Linux in produzione")], [])
            with patch("backend.pipeline.subprocess.run") as compose:
                main(["--project-dir", str(project), "--date", day, "--run-id", str(run_id)])
            compose.assert_called_once_with(
                ["docker", "compose", "up", "--build", "-d", "--wait", "web"],
                check=True, cwd=project.resolve(),
            )
            self.assertIn("Linux in produzione", (site / f"content/daily/{day}.md").read_text(encoding="utf-8"))

            unrelated, _, _ = store_run(database, NOW.date(), NOW, [story("Il meteo locale")], [])
            target = site / f"content/daily/{day}.md"
            published = target.read_bytes()
            compose.reset_mock()
            with patch("backend.pipeline.subprocess.run") as compose, patch("sys.stderr"):
                with self.assertRaises(SystemExit) as error:
                    main(["--project-dir", str(project), "--date", day, "--run-id", str(unrelated)])
            self.assertEqual(error.exception.code, 1)
            compose.assert_not_called()
            self.assertEqual(target.read_bytes(), published)
