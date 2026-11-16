"""Store RSS acquisitions in SQLite and reconstruct editions."""

import argparse
import json
import re
import sqlite3
import unicodedata
from contextlib import closing
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import unquote_plus, urlunsplit

from backend.main import SITE_DIR, validate_date, validate_edition, validate_web_url, write_if_changed


DEFAULT_DB = SITE_DIR.parent / "data" / "news.sqlite3"
EDITION_LIMIT = 10
TRACKING_KEYS = {"fbclid", "gclid", "dclid", "gbraid", "wbraid", "msclkid", "mc_cid", "mc_eid"}
UNRESERVED = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~")
MIGRATIONS = (
    (
        """CREATE TABLE articles (
            id INTEGER PRIMARY KEY,
            host TEXT NOT NULL,
            title_key TEXT NOT NULL,
            published_at TEXT,
            card TEXT NOT NULL
        )""",
        "CREATE INDEX articles_host_date ON articles(host, published_at)",
        """CREATE TABLE article_urls (
            url TEXT PRIMARY KEY,
            article_id INTEGER NOT NULL REFERENCES articles(id)
        )""",
        """CREATE TABLE collection_runs (
            id INTEGER PRIMARY KEY,
            edition_date TEXT NOT NULL,
            collected_at TEXT NOT NULL,
            source_results TEXT NOT NULL,
            new_articles INTEGER NOT NULL
        )""",
        "CREATE INDEX collection_runs_date ON collection_runs(edition_date, id)",
        """CREATE TABLE acquisitions (
            run_id INTEGER NOT NULL REFERENCES collection_runs(id),
            article_id INTEGER NOT NULL REFERENCES articles(id),
            position INTEGER NOT NULL,
            PRIMARY KEY (run_id, article_id),
            UNIQUE (run_id, position)
        )""",
    ),
    (
        "UPDATE articles SET host = substr(host, 5) WHERE host LIKE 'www.%'",
        "CREATE INDEX articles_host_title_date ON articles(host, title_key, published_at)",
    ),
)


def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("BEGIN IMMEDIATE")
        with db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version > len(MIGRATIONS):
                raise ValueError(f"Versione SQLite del progetto non supportata: {version}")
            for number, migration in enumerate(MIGRATIONS[version:], start=version + 1):
                for statement in migration:
                    db.execute(statement)
                db.execute(f"PRAGMA user_version = {number}")
    except BaseException:
        db.close()
        raise
    return db


def normalize_url(value):
    url = validate_web_url(value, "original_url")
    host = url.hostname
    authority = f"[{host}]" if ":" in host else host.encode("idna").decode("ascii").lower()
    if url.port is not None and url.port != {"http": 80, "https": 443}[url.scheme]:
        authority += f":{url.port}"
    ignored = {"hl", "gl", "ceid", "oc"} if authority == "news.google.com" and url.path.startswith("/rss/articles/") else set()
    query = [
        part for part in url.query.split("&")
        if not is_tracking_parameter(unquote_plus(part.partition("=")[0]).lower(), ignored)
    ]
    path = re.sub(r"%[0-9a-fA-F]{2}", normalize_escape, url.path or "/")
    return urlunsplit((url.scheme, authority, path, "&".join(query), ""))


def is_tracking_parameter(key, ignored):
    return key.startswith("utm_") or key in TRACKING_KEYS or key in ignored


def normalize_escape(match):
    char = chr(int(match[0][1:], 16))
    return char if char in UNRESERVED else match[0].upper()


def title_key(title):
    return " ".join(re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", title).casefold()))


def similar_article(db, host, title, published):
    if not published or not 32 <= len(title) <= 300:
        return None
    date = datetime.fromisoformat(published.removesuffix("Z") + "+00:00")
    window = timedelta(hours=48)
    start, end = (value.isoformat().replace("+00:00", "Z") for value in (date - window, date + window))
    numbers = re.findall(r"\d+", title)
    matches = []
    for candidate in db.execute(
        "SELECT id, title_key FROM articles WHERE host = ? AND published_at BETWEEN ? AND ?",
        (host, start, end),
    ):
        other = candidate["title_key"]
        if 32 <= len(other) <= 300 and re.findall(r"\d+", other) == numbers:
            if SequenceMatcher(None, min(title, other), max(title, other), autojunk=False).ratio() >= 0.94:
                matches.append(candidate["id"])
    return matches[0] if len(matches) == 1 else None


def exact_title_article(db, host, title, published):
    if not published or len(title) < 24:
        return None
    date = datetime.fromisoformat(published.removesuffix("Z") + "+00:00")
    window = timedelta(hours=24)
    start, end = (value.isoformat().replace("+00:00", "Z") for value in (date - window, date + window))
    matches = db.execute(
        "SELECT id FROM articles WHERE host = ? AND title_key = ? AND published_at BETWEEN ? AND ? LIMIT 2",
        (host, title, start, end),
    ).fetchall()
    return matches[0]["id"] if len(matches) == 1 else None


def store_run(path, day, now, cards, source_results):
    with closing(connect(path)) as db:
        db.execute("BEGIN IMMEDIATE")
        with db:
            run_id = db.execute(
                "INSERT INTO collection_runs(edition_date, collected_at, source_results, new_articles) "
                "VALUES (?, ?, ?, 0)",
                (day.isoformat(), now.isoformat(), json.dumps(source_results, ensure_ascii=False)),
            ).lastrowid
            seen = {}
            new = 0
            ordered = sorted(cards, key=lambda item: item.get("published_at", ""), reverse=True)
            # When both feeds carry an article, store its direct link first.
            for position, entry in sorted(enumerate(ordered), key=lambda pair: "_publisher_url" in pair[1]):
                card = {key: value for key, value in entry.items() if key != "_publisher_url"}
                publisher = entry.get("_publisher_url")
                url = normalize_url(card["original_url"])
                existing = db.execute("SELECT article_id FROM article_urls WHERE url = ?", (url,)).fetchone()
                if existing is not None:
                    article_id = existing["article_id"]
                else:
                    host = validate_web_url(normalize_url(publisher) if publisher else url, "original_url").netloc
                    host = host.removeprefix("www.")
                    title = title_key(card["title"])
                    published = card.get("published_at")
                    article_id = exact_title_article(db, host, title, published)
                    if article_id is None and host != "news.google.com":
                        article_id = similar_article(db, host, title, published)
                    if article_id is None:
                        article_id = db.execute(
                            "INSERT INTO articles(host, title_key, published_at, card) VALUES (?, ?, ?, ?)",
                            (host, title, published, json.dumps(card, ensure_ascii=False)),
                        ).lastrowid
                        new += 1
                    db.execute("INSERT INTO article_urls(url, article_id) VALUES (?, ?)", (url, article_id))
                seen[article_id] = min(position, seen.get(article_id, position))
            db.executemany(
                "INSERT INTO acquisitions(run_id, article_id, position) VALUES (?, ?, ?)",
                ((run_id, article_id, position) for article_id, position in seen.items()),
            )
            db.execute("UPDATE collection_runs SET new_articles = ? WHERE id = ?", (new, run_id))
    return run_id, new, len(seen)


def read_cards(db, run_id):
    for row in db.execute(
        "SELECT a.card FROM acquisitions AS ac JOIN articles AS a ON a.id = ac.article_id "
        "WHERE ac.run_id = ? ORDER BY ac.position",
        (run_id,),
    ):
        yield json.loads(row["card"])


def read_edition(path, day, run_id=None):
    with closing(connect(path)) as db:
        if run_id is None:
            row = db.execute(
                "SELECT MAX(r.id) FROM collection_runs AS r JOIN acquisitions AS ac ON r.id = ac.run_id "
                "WHERE r.edition_date = ?",
                (day.isoformat(),),
            ).fetchone()
            run_id = row[0]
        elif db.execute(
            "SELECT 1 FROM collection_runs WHERE id = ? AND edition_date = ?", (run_id, day.isoformat())
        ).fetchone() is None:
            raise ValueError("Acquisizione assente per la data indicata.")
        selected = []
        titles = set()
        for card in read_cards(db, run_id):
            title = " ".join(card["title"].split()).casefold()
            if title not in titles:
                titles.add(title)
                selected.append(card)
                if len(selected) == EDITION_LIMIT:
                    break
    return format_edition(day, selected)


def format_edition(day, selected):
    if not selected:
        raise ValueError("Nessuna notizia idonea. Il file di uscita non è stato aggiornato.")
    return {
        "date": day.isoformat(),
        "title": f"Edizione del {day.isoformat()}",
        "kind": "rss",
        "featured": selected[0],
        "stories": selected[1:],
    }


def read_acquisition(path, day, run_id):
    with closing(connect(path)) as db:
        row = db.execute(
            "SELECT collected_at FROM collection_runs WHERE id = ? AND edition_date = ?",
            (run_id, day.isoformat()),
        ).fetchone()
        if row is None:
            raise ValueError("Acquisizione assente per la data indicata.")
        return datetime.fromisoformat(row["collected_at"]), list(read_cards(db, run_id))


def inspect(path, day, limit, run_id=None):
    with closing(connect(path)) as db:
        runs = db.execute(
            "SELECT r.*, (SELECT COUNT(*) FROM acquisitions WHERE run_id = r.id) AS articles "
            "FROM collection_runs AS r WHERE (? IS NULL OR r.edition_date = ?) "
            "AND (? IS NULL OR r.id = ?) ORDER BY r.id DESC LIMIT ?",
            (day, day, run_id, run_id, limit),
        ).fetchall()
        result = {
            "articles_total": db.execute("SELECT COUNT(*) FROM articles").fetchone()[0],
            "runs": [dict(run) | {"source_results": json.loads(run["source_results"])} for run in runs],
        }
        if run_id is not None:
            if not runs:
                raise ValueError("Acquisizione assente.")
            result["articles"] = list(read_cards(db, run_id))
        return result


def export_edition(edition, day, output):
    validate_edition(edition, day, SITE_DIR)
    payload = (json.dumps(edition, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return write_if_changed(output, payload)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ispeziona lo storico RSS o rigenera un briefing da SQLite.")
    parser.add_argument("--db", default=DEFAULT_DB, type=Path, help="database SQLite")
    commands = parser.add_subparsers(dest="command", required=True)
    history = commands.add_parser("inspect", help="mostra storico e conteggi")
    history.add_argument("--date", help="limita lo storico alla data indicata")
    history.add_argument("--limit", default=10, type=int, help="numero massimo di acquisizioni")
    history.add_argument("--run-id", type=int, help="mostra anche le notizie di questa acquisizione")
    regenerate = commands.add_parser("regenerate", help="rigenera il JSON del briefing")
    regenerate.add_argument("--date", required=True, help="data del briefing YYYY-MM-DD")
    regenerate.add_argument("--run-id", type=int, help="ID di una specifica acquisizione salvata")
    regenerate.add_argument("--output", required=True, type=Path, help="destinazione JSON")
    args = parser.parse_args(argv)
    try:
        day = validate_date(args.date, "--date") if args.date is not None else None
        if args.command == "inspect":
            if args.limit < 1:
                parser.error("--limit deve essere almeno 1")
            print(json.dumps(inspect(args.db, day.isoformat() if day else None, args.limit, args.run_id), indent=2))
        else:
            if args.output.resolve() == args.db.resolve():
                raise ValueError("Il JSON di uscita deve essere distinto dal database.")
            export_edition(read_edition(args.db, day, args.run_id), day, args.output)
            print(f"Edizione RSS disponibile in {args.output}")
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f"Errore: {error}\n")


if __name__ == "__main__":
    main()
