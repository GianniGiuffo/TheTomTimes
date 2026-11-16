import sqlite3
import unittest
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from backend.collectors import rss
from backend.collectors.discovery import load_interests
from backend.database import MIGRATIONS, inspect


NOW = datetime(2026, 11, 13, 18, tzinfo=timezone.utc)
DAY = date(2026, 11, 13)
FIXED = {"name": "Testata", "url": "https://example.com/feed", "category": "Scienza"}
TITLE = "Una nuova missione spaziale studia la nebulosa di Orione"
CONFIG = """language: it
region: IT
window_hours: 6
max_results_per_query: 2
interests:
  - category: Scienza
    keywords: [missione spaziale, Orione]
"""


def item(title, url, timestamp="", publisher=""):
    return (f"<item><title>{title}</title><link>{url}</link><pubDate>{timestamp}</pubDate>"
            f"{publisher}</item>")


def feed(*items):
    return ("<rss><channel>" + "".join(items) + "</channel></rss>").encode("utf-8")


class DiscoveryTest(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.config = root / "interests.yaml"
        self.config.write_text(CONFIG, encoding="utf-8")
        self.db = root / "news.sqlite3"

    def test_configuration_builds_encoded_search_and_rejects_invalid_limits(self):
        source, = load_interests(self.config)
        self.assertEqual(parse_qs(urlsplit(source["url"]).query), {
            "q": ['("missione spaziale" OR "Orione") when:6h'],
            "hl": ["it"], "gl": ["IT"], "ceid": ["IT:it"],
        })
        self.config.write_text(CONFIG.replace("query: 2", "query: 0"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "max_results_per_query"):
            load_interests(self.config)

    def test_combined_collection_filters_limits_and_deduplicates(self):
        search, = load_interests(self.config)
        publisher = '<source url="https://www.example.com/">Testata</source>'
        fixed = feed(item(TITLE, "https://example.com/orione", "Fri, 13 Nov 2026 15:00:00 GMT"))
        discovered = feed(
            item("Troppo vecchia", "/rss/articles/old", "Fri, 13 Nov 2026 11:59:00 GMT"),
            item("Senza data", "/rss/articles/undated"),
            item("Esclusa dal limite", "/rss/articles/limit", "Fri, 13 Nov 2026 14:00:00 GMT"),
            item(TITLE + " - Testata", "/rss/articles/duplicate", "Fri, 13 Nov 2026 17:00:00 GMT", publisher),
            item("Una notizia da una nuova testata - Altra fonte", "/rss/articles/new",
                 "Fri, 13 Nov 2026 16:00:00 GMT", '<source url="https://example.org/">Altra fonte</source>'),
        )
        with patch.object(rss, "fetch_feed", side_effect=[fixed, discovered, fixed, discovered]) as fetch:
            first = rss.collect([FIXED, search], DAY, NOW, self.db)
            second = rss.collect([FIXED, search], DAY, NOW, self.db)
            self.assertEqual(fetch.call_count, 4)
        self.assertEqual(first, second)
        self.assertEqual(first["featured"]["original_url"], "https://example.com/orione")
        self.assertEqual([story["source_name"] for story in first["stories"]], ["Altra fonte"])
        history = inspect(self.db, DAY.isoformat(), 2)
        self.assertEqual(history["articles_total"], 2)
        self.assertEqual([run["new_articles"] for run in history["runs"]], [0, 2])
        self.assertEqual(history["runs"][0]["source_results"][1]["query"], search["query"])
        self.assertEqual(history["runs"][0]["source_results"][1]["items"], 2)

    def test_search_failure_is_recorded_while_fixed_feed_continues(self):
        search, = load_interests(self.config)
        fixed = feed(item(TITLE, "https://example.com/orione"))
        with patch.object(rss, "fetch_feed", side_effect=[fixed, TimeoutError("scaduto")]), \
             self.assertLogs(rss.LOG, level="WARNING"):
            edition = rss.collect([FIXED, search], DAY, NOW, self.db)
        self.assertEqual(edition["featured"]["title"], TITLE)
        failure = inspect(self.db, DAY.isoformat(), 1)["runs"][0]["source_results"][1]
        self.assertEqual(failure["query"], search["query"])
        self.assertEqual(failure["error"], "scaduto")

    def test_existing_phase_five_database_migrates(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            for statement in MIGRATIONS[0]:
                db.execute(statement)
            db.execute("PRAGMA user_version = 1")
            db.execute("INSERT INTO articles(host, title_key, card) VALUES ('www.example.com', 'titolo', '{}')")
        self.assertEqual(inspect(self.db, None, 1)["articles_total"], 1)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT host FROM articles").fetchone()[0], "example.com")
