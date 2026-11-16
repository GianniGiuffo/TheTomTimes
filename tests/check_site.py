"""Verify the Phase 2 demo served by Hugo or Nginx."""

import argparse
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlsplit
from urllib.request import Request, urlopen


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.ids = set()
        self.links = []
        self.assets = set()
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a":
            self.links.append(attrs)
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.assets.add(attrs["href"])
        self.assets.update(attrs[key] for key in ("src", "poster") if key in attrs)


def check_site(base_url):
    dates = ("2026-10-30", "2026-11-09", "2026-11-13")
    editions = [urljoin(base_url, f"daily/{date}/") for date in dates]
    archive_url = urljoin(base_url, "daily/")
    article_url = urljoin(base_url, "laboratorio-in-orbita/")
    pages = {}
    for url in (base_url, archive_url, article_url, *editions):
        with urlopen(url, timeout=10) as response:
            assert response.status == 200 and response.headers.get_content_type() == "text/html", url
            pages[url] = Page(response.read().decode("utf-8"))

    home_targets = [urljoin(base_url, link["href"]) for link in pages[base_url].links]
    assert archive_url in home_targets and editions[-1] in home_targets
    assert not set(editions[:-1]).intersection(home_targets)

    archive = pages[archive_url]
    assert {"mese-2026-10", "mese-2026-11"} <= archive.ids
    calendar_days = [urljoin(archive_url, link["href"]) for link in archive.links
                     if link.get("aria-label", "").startswith("Edizione del")]
    assert sorted(calendar_days) == editions
    assert {link["rel"]: link["href"] for link in archive.links if "rel" in link} == {
        "prev": "#mese-2026-10", "next": "#mese-2026-11",
    }

    for index, url in enumerate(editions):
        neighbors = {link["rel"]: urljoin(url, link["href"]) for link in pages[url].links if "rel" in link}
        expected = {}
        if index > 0:
            expected["prev"] = editions[index - 1]
        if index < len(editions) - 1:
            expected["next"] = editions[index + 1]
        assert neighbors == expected, (url, neighbors)
    assert any("back-link" in link.get("class", "").split()
               and urljoin(article_url, link["href"]) == editions[-1] for link in pages[article_url].links)

    assets = set()
    for url, page in pages.items():
        for reference in page.assets | {link["href"] for link in page.links}:
            address, fragment = urldefrag(urljoin(url, reference))
            assert urlsplit(address).netloc == urlsplit(base_url).netloc, reference
            if address in pages:
                assert not fragment or fragment in pages[address].ids, reference
            else:
                assets.add(address)

    for address in sorted(assets):
        with urlopen(address, timeout=10) as response:
            assert response.status == 200 and response.read(1), address
        if address.endswith(".mp4"):
            request = Request(address, headers={"Range": "bytes=0-31"})
            with urlopen(request, timeout=10) as response:
                assert response.status == 206 and len(response.read()) == 32, address
    print(f"{len(pages)} pagine e {len(assets)} asset verificati.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", nargs="?", default="http://127.0.0.1:8080/")
    check_site(parser.parse_args().base_url.rstrip("/") + "/")
