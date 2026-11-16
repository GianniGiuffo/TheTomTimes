"""Collect a single edition from configured public HTTPS RSS feeds."""

import argparse
import http.client
import ipaddress
import json
import logging
import socket
import sqlite3
import ssl
from contextlib import closing
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from xml.etree import ElementTree

from backend.collectors.discovery import DEFAULT_INTERESTS, load_interests
from backend.database import DEFAULT_DB, export_edition, read_edition, store_run
from backend.main import (
    SITE_DIR,
    unique_object,
    validate_date,
    validate_keys,
    validate_text,
    validate_web_url,
)


DEFAULT_SOURCES = SITE_DIR.parent / "config" / "sources.json"
MAX_FEED_BYTES = 2_000_000
TIMEOUT_SECONDS = 10
LOG = logging.getLogger(__name__)


class PublicHTTPSConnection(http.client.HTTPSConnection):
    def connect(self):
        addresses = socket.getaddrinfo(self.host, self.port, type=socket.SOCK_STREAM)
        host_addresses = [entry[4][0] for entry in addresses]
        if not all(ipaddress.ip_address(address).is_global for address in host_addresses):
            raise ValueError("Il feed punta a un indirizzo di rete non pubblico")

        # Use the verified addresses for the connection, keeping the host for TLS.
        for family, kind, protocol, _, address in addresses:
            connection = socket.socket(family, kind, protocol)
            connection.settimeout(self.timeout)
            try:
                connection.connect(address)
            except OSError:
                connection.close()
                continue
            try:
                self.sock = ssl.create_default_context().wrap_socket(connection, server_hostname=self.host)
            except OSError:
                connection.close()
                raise
            return
        raise OSError("Connessione al feed non riuscita")


class FeedTreeBuilder(ElementTree.TreeBuilder):
    def doctype(self, name, pubid, system):
        raise ValueError("Il feed RSS contiene una dichiarazione DTD")


class FeedText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden_tag = None

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden_tag = tag
        if tag in {"p", "br", "div", "li"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag == self.hidden_tag:
            self.hidden_tag = None
        if tag in {"p", "div", "li"}:
            self.parts.append(" ")

    def handle_data(self, data):
        if self.hidden_tag is None:
            self.parts.append(data)


def fetch_feed(url):
    endpoint = validate_web_url(url, "feed", schemes=("https",))
    if endpoint.port not in (None, 443) or endpoint.fragment:
        raise ValueError("Il feed deve usare HTTPS sulla porta 443, senza frammento")
    path = endpoint.path or "/"
    if endpoint.query:
        path += "?" + endpoint.query
    with closing(PublicHTTPSConnection(endpoint.hostname, timeout=TIMEOUT_SECONDS)) as connection:
        connection.request("GET", path, headers={
            "User-Agent": "TheTomTimes/0.1 RSS reader",
            "Accept": "application/rss+xml, application/xml, text/xml",
        })
        with connection.getresponse() as response:
            if response.status != 200:
                raise ValueError(f"Risposta HTTP {response.status}")
            payload = response.read(MAX_FEED_BYTES + 1)
            if len(payload) > MAX_FEED_BYTES:
                raise ValueError("Il feed supera il limite di 2 MB")
            return payload


def plain_text(html):
    parser = FeedText()
    parser.feed(html)
    parser.close()
    return " ".join("".join(char for char in "".join(parser.parts)
                            if ord(char) >= 32 or char.isspace()).split())


def read_publication_date(value):
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is not None:
            return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        pass
    return None


def parse_feed(payload, source, now):
    root = ElementTree.fromstring(payload, parser=ElementTree.XMLParser(target=FeedTreeBuilder()))
    channel = root.find("channel")
    if root.tag != "rss" or channel is None:
        raise ValueError("Il documento non è un feed RSS 2.0")

    search = "query" in source
    cutoff = now - timedelta(hours=source.get("window_hours", 24))
    for item in channel.findall("item"):
        title = plain_text(item.findtext("title", ""))
        link = item.findtext("link", "").strip()
        if not title or not link:
            continue
        url = urljoin(source["url"], link)
        try:
            validate_web_url(url, "link")
        except ValueError:
            continue
        published = read_publication_date(item.findtext("pubDate", ""))
        if published is not None and not cutoff <= published <= now:
            continue
        if search and published is None:
            continue

        description = plain_text(item.findtext("description", ""))
        publisher = item.find("source") if search else None
        publisher_name = plain_text(publisher.text or "") if publisher is not None else ""
        if publisher_name and title.endswith(f" - {publisher_name}"):
            title = title.removesuffix(f" - {publisher_name}").strip()
        if not title:
            continue
        # Google News descriptions often repeat only the headline and publisher.
        if search and description in {title, f"{title} {publisher_name}".strip(), f"{title} - {publisher_name}"}:
            description = ""
        if len(description) > 200:
            description = description[:197].rsplit(" ", 1)[0] + "…"
        card = {
            "title": title,
            "category": source["category"],
            "summary": description or "Consulta l’articolo originale per i dettagli.",
            "source_name": publisher_name or source["name"],
            "original_url": url,
        }
        if published is not None:
            card["published_at"] = published.strftime("%Y-%m-%dT%H:%M:%SZ")
        if publisher is not None and publisher.get("url"):
            try:
                card["_publisher_url"] = validate_web_url(publisher.get("url"), "source").geturl()
            except ValueError:
                pass
        yield card


def load_sources(path):
    with path.open(encoding="utf-8-sig") as stream:
        sources = json.load(stream, object_pairs_hook=unique_object)
    if not isinstance(sources, list) or not sources:
        raise ValueError("La configurazione deve contenere almeno un feed RSS")
    for source in sources:
        validate_keys(source, "fonte", {"name", "url", "category"})
        validate_text(source["name"], "name")
        validate_text(source["category"], "category")
        validate_web_url(source["url"], "url", schemes=("https",))
    return sources


def acquire(sources, day, now, db_path):
    cards = []
    results = []
    for source in sources:
        result = {"name": source["name"], "url": source["url"]}
        if "query" in source:
            result.update(query=source["query"], category=source["category"])
            LOG.info("Ricerca %s: %s", source["category"], source["query"])
        try:
            entries = list(parse_feed(fetch_feed(source["url"]), source, now))
        except (OSError, http.client.HTTPException, ValueError, ElementTree.ParseError) as error:
            LOG.warning("%s: %s", source["name"], error)
            result.update(items=0, error=str(error))
        else:
            if "limit" in source:
                entries.sort(key=lambda card: card["published_at"], reverse=True)
                entries = entries[:source["limit"]]
            LOG.info("%s (%s): %d notizie idonee", source["name"], source["category"], len(entries))
            result["items"] = len(entries)
            cards.extend(entries)
        results.append(result)

    run_id, new, articles = store_run(db_path, day, now, cards, results)
    LOG.info("Acquisizione %d: %d notizie distinte, %d nuove", run_id, articles, new)
    return run_id


def collect(sources, day, now, db_path):
    return read_edition(db_path, day, acquire(sources, day, now, db_path))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Raccoglie notizie RSS per un’edizione Hugo.")
    parser.add_argument("--date", required=True, help="data dell’edizione YYYY-MM-DD")
    parser.add_argument("--output", required=True, type=Path, help="file JSON di destinazione")
    parser.add_argument("--sources", default=DEFAULT_SOURCES, type=Path, help="configurazione dei feed")
    search = parser.add_mutually_exclusive_group()
    search.add_argument("--interests", default=DEFAULT_INTERESTS, type=Path, help="configurazione YAML degli interessi")
    search.add_argument("--rss-only", action="store_true", help="usa solo i feed predefiniti")
    parser.add_argument("--db", default=DEFAULT_DB, type=Path, help="database SQLite")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        day = validate_date(args.date, "--date")
        protected = {args.sources.resolve(), args.interests.resolve()}
        if protected.intersection({args.db.resolve(), args.output.resolve()}) or args.output.resolve() == args.db.resolve():
            raise ValueError("Database, configurazioni e JSON di uscita devono usare file distinti.")
        sources = load_sources(args.sources)
        if not args.rss_only:
            sources.extend(load_interests(args.interests))
        edition = collect(sources, day, datetime.now(timezone.utc), args.db)
        export_edition(edition, day, args.output)
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f"Errore: {error}\n")
    print(f"Scritta edizione RSS in {args.output}")


if __name__ == "__main__":
    main()
