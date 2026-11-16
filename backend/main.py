"""Generate a single Hugo edition from a UTF-8 JSON file."""

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit


SITE_DIR = Path(__file__).resolve().parents[1] / "site"
DATE_PATTERN = r"[0-9]{4}-[0-9]{2}-[0-9]{2}"
IMAGE_PATTERN = r"img/(?:[a-zA-Z0-9_-]+/)*[a-zA-Z0-9_-]+\.(?:webp|avif|png|jpg|jpeg|gif)"
VIDEO_PATTERN = r"video/(?:[a-zA-Z0-9_-]+/)*[a-zA-Z0-9_-]+\.mp4"
SLUG_PATTERN = r"[a-z0-9]+(?:-[a-z0-9]+)*"
CARD_FIELDS = frozenset({"title", "category", "summary"})
STORY_METADATA = frozenset({"original_url", "source_name", "published_at"})


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Chiave JSON ripetuta: {key}")
        result[key] = value
    return result


def validate_keys(value, location, required, optional=()):
    if not isinstance(value, dict):
        raise ValueError(f"{location}: è richiesto un oggetto JSON")
    missing = required - value.keys()
    unknown = value.keys() - required - set(optional)
    if missing:
        raise ValueError(f"{location}: campi mancanti: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"{location}: campi sconosciuti: {', '.join(sorted(unknown))}")


def validate_text(value, location):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{location}: è richiesto un testo non vuoto")
    if re.search(r"[\x00-\x1f\x85\u2028\u2029]", value):
        raise ValueError(f"{location}: usa una sola riga e nessun carattere di controllo")


def validate_web_url(value, location, schemes=("http", "https")):
    if isinstance(value, str) and not re.search(r"[\s\x00-\x1f\x7f\\]", value):
        try:
            url = urlsplit(value)
            if url.scheme in schemes and url.hostname and "@" not in url.netloc:
                if url.port is None or 0 < url.port <= 65535:
                    return url
        except ValueError:
            pass
    raise ValueError(f"{location}: URL web non valido")


def validate_timestamp(value, location):
    if isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value):
        try:
            datetime.fromisoformat(value[:-1] + "+00:00")
            return
        except ValueError:
            pass
    raise ValueError(f"{location}: usa una data e ora UTC nel formato YYYY-MM-DDTHH:MM:SSZ")


def validate_date(value, location):
    if isinstance(value, str) and re.fullmatch(DATE_PATTERN, value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    raise ValueError(f"{location}: usa una data valida nel formato YYYY-MM-DD")


def validate_file(value, pattern, root, location, suffix=""):
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError(f"{location}: percorso non valido")
    target = (root / (value + suffix)).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        raise ValueError(f"{location}: file locale mancante: {value}{suffix}")


def validate_card(card, location, site_dir, *, video=False):
    if video:
        validate_keys(card, location, CARD_FIELDS | {"image", "source"})
    else:
        validate_keys(card, location, CARD_FIELDS, STORY_METADATA | {"image", "slug"})
    for field in ("title", "category", "summary"):
        validate_text(card[field], f"{location}.{field}")
    if "image" in card:
        validate_file(card["image"], IMAGE_PATTERN, site_dir / "static", f"{location}.image")
    if video:
        validate_file(card["source"], VIDEO_PATTERN, site_dir / "static", f"{location}.source")
    if "slug" in card:
        validate_file(card["slug"], SLUG_PATTERN, site_dir / "content", f"{location}.slug", ".md")
    if "original_url" in card:
        validate_web_url(card["original_url"], f"{location}.original_url")
    if "source_name" in card:
        validate_text(card["source_name"], f"{location}.source_name")
    if "published_at" in card:
        validate_timestamp(card["published_at"], f"{location}.published_at")


def validate_edition(edition, selected_date, site_dir):
    validate_keys(edition, "edizione", {"date", "title", "featured", "stories"}, {"videos", "kind"})
    if edition.get("kind", "demo") not in ("demo", "rss"):
        raise ValueError("kind: usa demo oppure rss")
    file_date = validate_date(edition["date"], "date")
    if file_date != selected_date:
        raise ValueError(f"date: il JSON contiene {file_date}, mentre --date indica {selected_date}")
    validate_text(edition["title"], "title")

    validate_card(edition["featured"], "featured", site_dir)
    for field in ("stories", "videos"):
        cards = edition.get(field, [])
        if not isinstance(cards, list):
            raise ValueError(f"{field}: è richiesto un array JSON")
        for index, card in enumerate(cards):
            validate_card(card, f"{field}[{index}]", site_dir, video=field == "videos")

    news = [edition["featured"], *edition["stories"]]
    titles = {" ".join(card["title"].split()).casefold() for card in news}
    if len(titles) != len(news):
        raise ValueError("featured/stories: titolo di notizia duplicato")


def publish(input_path, day, site_dir=SITE_DIR):
    selected_date = validate_date(day, "--date")
    with input_path.open(encoding="utf-8-sig") as source:
        edition = json.load(source, object_pairs_hook=unique_object)
    validate_edition(edition, selected_date, site_dir)

    metadata = {
        "title": edition["title"],
        "date": selected_date.isoformat(),
        "description": edition["featured"]["summary"],
        "params": {
            "featured": edition["featured"],
            "stories": edition["stories"],
            "videos": edition.get("videos", []),
        },
    }
    if "kind" in edition:
        metadata["params"]["kind"] = edition["kind"]
    content = (json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    target = site_dir / "content" / "daily" / f"{selected_date.isoformat()}.md"
    return target, write_if_changed(target, content)


def write_if_changed(target, content):
    if target.exists() and target.read_bytes() == content:
        return False

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with NamedTemporaryFile(dir=target.parent, suffix=".tmp", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
        temporary_path.chmod(0o644)
        temporary_path.replace(target)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description="Genera una singola edizione Hugo da un file JSON.")
    parser.add_argument("--date", required=True, help="data dell’edizione YYYY-MM-DD")
    parser.add_argument("--input", required=True, type=Path, help="file JSON dell’edizione")
    parser.add_argument("--site", default=SITE_DIR, type=Path, help="cartella del progetto Hugo")
    args = parser.parse_args(argv)
    try:
        path, changed = publish(args.input, args.date, args.site)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Errore: {error}\n")
    print(f"{'Scritta' if changed else 'Già aggiornata'}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
