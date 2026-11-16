"""Select an edition using configurable, deterministic scoring rules."""

from datetime import datetime

from backend.collectors.discovery import load_yaml
from backend.database import title_key
from backend.main import SITE_DIR, validate_keys, validate_text


DEFAULT_RANKING = SITE_DIR.parent / "config" / "ranking.yaml"
COMPONENTS = ("interest", "recency", "source")


def load_ranking(path):
    config = load_yaml(path)
    validate_keys(config, "ranking.yaml", {
        "edition_size", "recency_hours", "weights", "default_source_priority", "source_priorities",
    }, {"exclude_keywords"})
    size = config["edition_size"]
    if type(size) is not int or not 10 <= size <= 20:
        raise ValueError("edition_size: usa un intero da 10 a 20")
    hours = config["recency_hours"]
    if type(hours) is not int or hours < 1:
        raise ValueError("recency_hours: usa un intero positivo")
    weights = config["weights"]
    validate_keys(weights, "weights", set(COMPONENTS))
    if any(type(weights[name]) not in (int, float) or not 0 <= weights[name] <= 100 for name in COMPONENTS):
        raise ValueError("weights: usa valori da 0 a 100")
    if weights["interest"] <= 0:
        raise ValueError("weights.interest deve essere positivo")
    priorities = config["source_priorities"]
    if not isinstance(priorities, dict):
        raise ValueError("source_priorities: usa una mappa testata → priorità")
    for name in priorities:
        validate_text(name, "source_priorities")
    for priority in (config["default_source_priority"], *priorities.values()):
        if type(priority) not in (int, float) or not 0 <= priority <= 100:
            raise ValueError("Priorità delle fonti: usa valori da 0 a 100")
    excluded = config.get("exclude_keywords", [])
    if not isinstance(excluded, list):
        raise ValueError("exclude_keywords: usa una lista di espressioni")
    for term in excluded:
        validate_text(term, "exclude_keywords")
        if not title_key(term):
            raise ValueError("exclude_keywords: ogni espressione deve contenere una parola")
    return config


def score_stories(cards, interests, config, collected_at):
    phrases = [
        (interest["category"], {key for term in interest["keywords"] if (key := title_key(term))})
        for interest in interests
    ]
    excluded = [title_key(term) for term in config.get("exclude_keywords", [])]
    priorities = {name.strip().casefold(): value for name, value in config["source_priorities"].items()}
    weights = config["weights"]
    total_weight = sum(weights[name] for name in COMPONENTS)
    scored = []
    for card in cards:
        title = f" {title_key(card['title'])} "
        summary = f" {title_key(card['summary'])} "
        if any(f" {term} " in title or f" {term} " in summary for term in excluded):
            continue
        matches = [
            (sum(2 if f" {term} " in title else int(f" {term} " in summary) for term in terms), category)
            for category, terms in phrases
        ]
        relevance, category = max(matches, key=lambda match: (match[0], match[1] == card["category"]))
        if relevance == 0:
            continue

        published = card.get("published_at", "")
        recency = 0.0
        if published:
            published_at = datetime.fromisoformat(published.removesuffix("Z") + "+00:00")
            age = (collected_at - published_at).total_seconds() / 3600
            recency = max(0.0, 1 - age / config["recency_hours"]) if age >= 0 else 0.0
        source = card.get("source_name", "").strip().casefold()
        priority = priorities.get(source, config["default_source_priority"]) / 100
        score = round(100 * (
            weights["interest"] * min(relevance / 4, 1)
            + weights["recency"] * recency
            + weights["source"] * priority
        ) / total_weight, 6)
        scored.append((score, {**card, "category": category}))
    # Stable tie-breaks by recency, then by headline and URL.
    scored.sort(key=lambda entry: (title_key(entry[1]["title"]), entry[1]["original_url"]))
    scored.sort(key=lambda entry: (entry[0], entry[1].get("published_at", "")), reverse=True)
    return scored


def select_stories(scored, size):
    seen_titles = set()
    candidates = []
    first_by_category = {}
    for score, card in scored:
        title = title_key(card["title"]) or card["title"]
        if title in seen_titles:
            continue
        seen_titles.add(title)
        first_by_category.setdefault(card["category"], len(candidates))
        candidates.append((score, card))

    selected = set(list(first_by_category.values())[:size])
    for position in range(len(candidates)):
        if len(selected) >= size:
            break
        selected.add(position)
    return [candidates[position] for position in sorted(selected)]
