"""Collect, rank and publish a daily briefing with Docker Compose."""

import argparse
import logging
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from backend.collectors.discovery import DEFAULT_INTERESTS, load_interest_config, search_sources
from backend.collectors.rss import DEFAULT_SOURCES, acquire, load_sources
from backend.database import export_edition, format_edition, read_acquisition
from backend.main import SITE_DIR, publish, validate_date
from backend.ranking import DEFAULT_RANKING, load_ranking, score_stories, select_stories


LOG = logging.getLogger(__name__)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Seleziona e pubblica il briefing giornaliero.")
    parser.add_argument("--date", required=True, help="data del briefing YYYY-MM-DD")
    parser.add_argument("--db", type=Path, help="database SQLite")
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES, help="configurazione dei feed diretti")
    parser.add_argument("--interests", type=Path, default=DEFAULT_INTERESTS, help="configurazione degli interessi")
    parser.add_argument("--ranking", type=Path, default=DEFAULT_RANKING, help="configurazione del ranking")
    parser.add_argument("--run-id", type=int, help="riutilizza un’acquisizione salvata")
    parser.add_argument("--project-dir", type=Path, default=SITE_DIR.parent, help="progetto da pubblicare con Compose")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        day = validate_date(args.date, "--date")
        project = args.project_dir.resolve()
        if not (project / "docker-compose.yml").is_file() or not (project / "site" / "hugo.toml").is_file():
            raise ValueError(f"Progetto Hugo e Compose assente in {project}")
        output = project / "output" / f"edition-ranked-{day.isoformat()}.json"
        db = args.db or project / "data" / "news.sqlite3"
        protected = {path.resolve() for path in (args.sources, args.interests, args.ranking)}
        if output.resolve() == db.resolve() or protected.intersection((output.resolve(), db.resolve())):
            raise ValueError("Database, configurazioni e JSON di uscita devono usare file distinti.")
        interests = load_interest_config(args.interests)
        ranking = load_ranking(args.ranking)
        run_id = args.run_id
        if run_id is None:
            sources = load_sources(args.sources) + search_sources(interests)
            run_id = acquire(sources, day, datetime.now(timezone.utc), db)
        collected_at, cards = read_acquisition(db, day, run_id)
        scored = score_stories(cards, interests["interests"], ranking, collected_at)
        selected = select_stories(scored, ranking["edition_size"])
        if not selected:
            raise ValueError(f"Acquisizione {run_id}: nessuna notizia pertinente alle parole chiave.")

        LOG.info("Acquisizione %d: %d selezionate su %d notizie", run_id, len(selected), len(cards))
        for score, card in selected:
            LOG.info("%5.1f | %s | %s", score, card["category"], card["title"])
        edition = format_edition(day, [card for _, card in selected])
        export_edition(edition, day, output)
        publish(output, day.isoformat(), project / "site")
        subprocess.run(["docker", "compose", "up", "--build", "-d", "--wait", "web"],
                       cwd=project, check=True)
    except (OSError, ValueError, sqlite3.Error, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Errore: {error}\n")
    print(f"Briefing pubblicato su /daily/{day.isoformat()}/. JSON in {output}")


if __name__ == "__main__":
    main()
