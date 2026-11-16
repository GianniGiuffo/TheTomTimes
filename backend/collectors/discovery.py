"""Build Google News RSS queries from the configured interests."""

import re
from urllib.parse import urlencode

from backend.main import SITE_DIR, validate_keys, validate_text


DEFAULT_INTERESTS = SITE_DIR.parent / "config" / "interests.yaml"
SEARCH_URL = "https://news.google.com/rss/search"


def load_yaml(path):
    try:
        import yaml
    except ModuleNotFoundError as error:
        raise ValueError("Installa PyYAML con python -m pip install -r backend/requirements.txt.") from error
    try:
        with path.open(encoding="utf-8-sig") as stream:
            return yaml.safe_load(stream)
    except yaml.YAMLError as error:
        raise ValueError(f"YAML non valido in {path}: {error}") from error


def load_interest_config(path):
    config = load_yaml(path)
    validate_keys(config, "interests.yaml", {"interests"},
                  {"language", "region", "window_hours", "max_results_per_query"})
    language = config.get("language", "it")
    region = config.get("region", "IT")
    window = config.get("window_hours", 24)
    limit = config.get("max_results_per_query", 20)
    if not isinstance(language, str) or not re.fullmatch("[a-z]{2}", language):
        raise ValueError("language: usa due lettere minuscole, per esempio it")
    if not isinstance(region, str) or not re.fullmatch("[A-Z]{2}", region):
        raise ValueError("region: usa due lettere maiuscole, per esempio IT")
    if type(window) is not int or not 1 <= window <= 168:
        raise ValueError("window_hours: usa un intero tra 1 e 168")
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("max_results_per_query: usa un intero tra 1 e 100")
    if not isinstance(config["interests"], list) or not config["interests"]:
        raise ValueError("interests: indica almeno una categoria")

    for interest in config["interests"]:
        validate_keys(interest, "interesse", {"category", "keywords"})
        category = interest["category"]
        validate_text(category, "category")
        keywords = interest["keywords"]
        if not isinstance(keywords, list) or not keywords:
            raise ValueError(f"{category}: keywords deve contenere almeno una voce")
        for keyword in keywords:
            validate_text(keyword, f"{category}.keywords")
            if '"' in keyword:
                raise ValueError(f"{category}.keywords: usa i termini senza virgolette doppie")
    return config


def search_sources(config):
    language = config.get("language", "it")
    region = config.get("region", "IT")
    window = config.get("window_hours", 24)
    limit = config.get("max_results_per_query", 20)
    sources = []
    for interest in config["interests"]:
        category = interest["category"]
        keywords = interest["keywords"]
        terms = " OR ".join(f'"{term.strip()}"' for term in dict.fromkeys(keywords))
        query = f"({terms}) when:{window}h"
        params = urlencode({"q": query, "hl": language, "gl": region, "ceid": f"{region}:{language}"})
        sources.append({
            "name": "Google News",
            "url": f"{SEARCH_URL}?{params}",
            "category": category,
            "query": query,
            "window_hours": window,
            "limit": limit,
        })
    return sources


def load_interests(path):
    return search_sources(load_interest_config(path))
