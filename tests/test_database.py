import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from backend.collectors import rss
from backend.database import inspect, main, normalize_url, read_edition, store_run
from backend.main import publish


DAY = date(2026, 11, 13)
NOW = datetime(2026, 11, 13, 18, tzinfo=timezone.utc)
TITLE = "Nuove misurazioni del telescopio orbitale nella nebulosa di Orione"


def card(url, title=TITLE, published_at="2026-11-13T16:00:00Z"):
    return {
        "original_url": url,
        "title": title,
        "published_at": published_at,
        "category": "Scienza",
        "summary": "Estratto RSS di prova.",
        "source_name": "Fonte di prova",
    }


class DatabaseTest(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.db = self.root / "data" / "news.sqlite3"

    def test_url_normalization_preserves_functional_components(self):
        self.assertEqual(
            normalize_url("HTTPS://EXAMPLE.com:443/%7euser/A%2fb/?id=7&UTM_Source=rss&x=2&x=1&fbclid=z#part"),
            "https://example.com/~user/A%2Fb/?id=7&x=2&x=1",
        )
        self.assertEqual(normalize_url("http://EXAMPLE.com:8080"), "http://example.com:8080/")
        self.assertNotEqual(normalize_url("https://example.com/news?id=1"),
                            normalize_url("https://example.com/news?id=2"))

    def test_same_feed_twice_records_two_runs_without_reinserting_articles(self):
        source = {"name": "Feed demo", "url": "https://example.com/feed", "category": "Scienza"}
        payload = b"""<rss version="2.0"><channel>
        <item><title>Una notizia di prova</title><link>/news?utm_source=rss</link></item>
        <item><title>Un altro titolo</title><link>/news?fbclid=123</link></item>
        </channel></rss>"""
        with patch.object(rss, "fetch_feed", return_value=payload):
            first = rss.collect([source], DAY, NOW, self.db)
            second = rss.collect([source], DAY, NOW, self.db)
        self.assertEqual(first, second)
        history = inspect(self.db, DAY.isoformat(), 10)
        self.assertEqual(history["articles_total"], 1)
        self.assertEqual([run["new_articles"] for run in history["runs"]], [0, 1])
        self.assertEqual([run["articles"] for run in history["runs"]], [1, 1])

    def test_title_matching_is_conservative_and_remembers_alternate_urls(self):
        first = card("https://example.com/article")
        similar = card("https://example.com/rewritten", TITLE.replace("Nuove", "Nuovissime"))
        other_host = card("https://example.org/edition")
        other_day = card("https://example.com/article-later", published_at="2026-11-10T16:00:00Z")
        numbered = card("https://example.com/article-2", TITLE + " 2")
        store_run(self.db, DAY, NOW, [first], [])
        _, new, total = store_run(self.db, DAY, NOW, [similar, other_host, other_day, numbered], [])
        self.assertEqual((new, total), (3, 4))
        _, new, total = store_run(self.db, DAY, NOW, [{**similar, "title": "Titolo aggiornato"}], [])
        self.assertEqual((new, total), (0, 1))

    def test_latest_successful_or_explicit_run_can_regenerate_and_publish(self):
        first = card("https://example.com/one", "Prima notizia")
        second = card("https://example.com/two", "Seconda notizia")
        first_run, _, _ = store_run(self.db, DAY, NOW, [first], [])
        store_run(self.db, DAY, NOW, [second], [])
        store_run(self.db, DAY, NOW, [], [{"error": "Timeout"}])
        self.assertEqual(read_edition(self.db, DAY)["featured"], second)
        self.assertEqual(read_edition(self.db, DAY, first_run)["featured"], first)
        self.assertEqual(inspect(self.db, None, 1, first_run)["articles"], [first])
        output = self.root / "edition.json"
        main(["--db", str(self.db), "regenerate", "--date", DAY.isoformat(),
              "--run-id", str(first_run), "--output", str(output)])
        self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["featured"], first)
        target, changed = publish(output, DAY.isoformat(), self.root / "site")
        self.assertTrue(changed)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["params"]["featured"], first)

    def test_concurrent_first_runs_do_not_duplicate_articles_or_migrations(self):
        article = card("https://example.com/item")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: store_run(self.db, DAY, NOW, [article], []), range(2)))
        self.assertEqual(sorted(new for _, new, _ in results), [0, 1])
        self.assertEqual(inspect(self.db, None, 10)["articles_total"], 1)

    def test_editions_select_ten_but_history_keeps_every_article(self):
        cards = [card(f"https://example.com/item/{index}", f"Notizia {index}") for index in range(12)]
        run_id, new, total = store_run(self.db, DAY, NOW, cards, [])
        self.assertEqual((new, total), (12, 12))
        self.assertEqual(len(read_edition(self.db, DAY, run_id)["stories"]), 9)
        self.assertEqual(inspect(self.db, None, 1, run_id)["articles"], cards)
