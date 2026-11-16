import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch
from xml.etree.ElementTree import ParseError

from backend.collectors import rss
from backend.database import inspect
from backend.main import publish


SOURCE = {"name": "Notizie di prova", "url": "https://example.com/feed/", "category": "Scienza"}
NOW = datetime(2026, 11, 13, 18, tzinfo=timezone.utc)
DAY = date(2026, 11, 13)
FEED = b"""<rss version="2.0"><channel>
  <item><title>Recente &amp; verificata</title><link>/news/recent</link>
    <pubDate>Fri, 13 Nov 2026 18:30:00 +0100</pubDate>
    <description><![CDATA[<p>Ciao <b>mondo</b></p><script>omesso</script>]]></description></item>
  <item><title>Sul limite</title><link>/news/boundary</link>
    <pubDate>Thu, 12 Nov 2026 18:00:00 GMT</pubDate></item>
  <item><title>Senza data valida</title><link>/news/undated</link><pubDate>ignota</pubDate></item>
  <item><title>Vecchia</title><link>/news/old</link>
    <pubDate>Thu, 12 Nov 2026 17:59:59 GMT</pubDate></item>
  <item><title>Futura</title><link>/news/future</link>
    <pubDate>Fri, 13 Nov 2026 18:00:01 GMT</pubDate></item>
  <item><title>Senza link</title></item>
  <item><title>Link non valido</title><link>javascript:alert(1)</link></item>
</channel></rss>"""


class RssTest(unittest.TestCase):
    def test_date_window_and_incomplete_items(self):
        recent, boundary, undated = rss.parse_feed(FEED, SOURCE, NOW)
        self.assertEqual(recent["published_at"], "2026-11-13T17:30:00Z")
        self.assertEqual(recent["title"], "Recente & verificata")
        self.assertEqual(recent["original_url"], "https://example.com/news/recent")
        self.assertEqual(recent["summary"], "Ciao mondo")
        self.assertEqual(boundary["published_at"], "2026-11-12T18:00:00Z")
        self.assertNotIn("published_at", undated)
        self.assertEqual(undated["summary"], "Consulta l’articolo originale per i dettagli.")

    def test_invalid_xml_and_dtd(self):
        with self.assertRaises(ParseError):
            list(rss.parse_feed(b"<rss", SOURCE, NOW))
        with self.assertRaisesRegex(ValueError, "DTD"):
            list(rss.parse_feed(b'<!DOCTYPE rss><rss><channel/></rss>', SOURCE, NOW))

    def test_private_destination_is_rejected_before_socket_creation(self):
        with patch.object(rss.socket, "getaddrinfo", return_value=[(0, 0, 0, "", ("127.0.0.1", 443))]), \
             patch.object(rss.socket, "socket") as socket:
            with self.assertRaisesRegex(ValueError, "non pubblico"):
                rss.fetch_feed("https://example.com/feed")
            socket.assert_not_called()

    def test_timeout_and_malformed_feed_allow_partial_collection(self):
        sources = [{**SOURCE, "name": name} for name in ("Timeout", "XML errato", SOURCE["name"])]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            db = root / "news.sqlite3"
            with patch.object(rss, "fetch_feed", side_effect=[TimeoutError("scaduto"), b"<", FEED]), \
                 self.assertLogs(rss.LOG, level="WARNING") as messages:
                edition = rss.collect(sources, DAY, NOW, db)
            self.assertEqual(len(messages.output), 2)
            self.assertEqual(edition["featured"]["source_name"], SOURCE["name"])
            self.assertEqual(len(edition["stories"]), 2)
            history = inspect(db, DAY.isoformat(), 1)["runs"][0]
            self.assertEqual(history["articles"], 3)
            self.assertEqual(history["source_results"][0]["error"], "scaduto")
            source = root / "edition.json"
            source.write_text(json.dumps(edition), encoding="utf-8")
            target, changed = publish(source, DAY.isoformat(), root)
            self.assertTrue(changed)
            metadata = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(metadata["params"]["kind"], "rss")
            self.assertEqual(metadata["params"]["featured"], edition["featured"])

    def test_failed_collection_preserves_existing_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "sources.json"
            output = root / "edition.json"
            db = root / "news.sqlite3"
            config.write_text(json.dumps([SOURCE]), encoding="utf-8")
            output.write_bytes(b"previous edition")
            with patch.object(rss, "fetch_feed", side_effect=TimeoutError("scaduto")), \
                 self.assertLogs(rss.LOG, level="WARNING"), \
                 self.assertRaises(SystemExit) as error, \
                 patch("sys.stderr"):
                rss.main(["--date", DAY.isoformat(), "--sources", str(config), "--output", str(output),
                          "--db", str(db), "--rss-only"])
            self.assertEqual(error.exception.code, 1)
            self.assertEqual(output.read_bytes(), b"previous edition")
            history = inspect(db, DAY.isoformat(), 1)["runs"][0]
            self.assertEqual(history["articles"], 0)
