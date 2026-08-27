"""Single-process BFS crawler for basketball.realgm.com.

Crawls a handful of pages, extract title/text/links, and grows the frontier.
Robots.txt, politeness delay, and basic filtering keep it well-behaved.
No persistence or indexing yet.
"""

from __future__ import annotations

import time
from collections import deque
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

SEED_URL = "https://basketball.realgm.com/"
ALLOWED_DOMAIN = "basketball.realgm.com"
MAX_PAGES = 10
MAX_DEPTH = 2
REQUEST_TIMEOUT = 10
CRAWL_DELAY_SECONDS = 2
USER_AGENT = "search-engine-crawler/0.1 (educational local project)"

DISALLOWED_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico",
    ".css", ".js", ".pdf", ".zip", ".mp4",
)
DISALLOWED_PATH_KEYWORDS = ("/forum", "/login", "/register", "/account", "/betting")

_robots_parser: RobotFileParser | None = None


def get_robots_parser(session: requests.Session) -> RobotFileParser:
    global _robots_parser
    if _robots_parser is None: # ensure the parser exists
        parser = RobotFileParser()
        parser.set_url(f"https://{ALLOWED_DOMAIN}/robots.txt")
        # RobotFileParser.read() fetches with urllib's generic User-Agent, which
        # this site 403s (triggering its own disallow-all-on-403 rule) even though
        # the real robots.txt has no Disallow rules. Fetch it ourselves through the
        # same session as page fetches, so headers/cookies/UA stay consistent.
        response = fetch(session, parser.url)
        parser.parse(response.text.splitlines())
        _robots_parser = parser
    return _robots_parser # return the existing parser


def fetch(session: requests.Session, url: str) -> requests.Response:
    response = session.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response


def parse_page(url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""
    text = soup.get_text(separator=" ", strip=True)
    links = [urljoin(url, a["href"]) for a in soup.find_all("a", href=True)]

    canonical_tag = soup.find("link", rel="canonical")
    canonical_href = canonical_tag.get("href") if canonical_tag else None
    canonical_url = normalize_url(urljoin(url, canonical_href)) if canonical_href else url

    return {
        "url": url,
        "canonical_url": canonical_url,
        "title": title,
        "text": text,
        "links": links,
    }


def normalize_url(url: str) -> str:
    normalized, _fragment = urldefrag(url)
    parsed = urlparse(normalized)
    path = parsed.path
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return parsed._replace(netloc=parsed.netloc.lower(), path=path).geturl()


def should_crawl(url: str) -> bool:
    """Structural filtering only — checked once before a URL enters the frontier."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or parsed.netloc != ALLOWED_DOMAIN:
        return False

    path_lower = parsed.path.lower()
    if path_lower.endswith(DISALLOWED_EXTENSIONS):
        return False
    if any(keyword in path_lower for keyword in DISALLOWED_PATH_KEYWORDS):
        return False

    return True


def crawl(seed_url: str, max_pages: int = MAX_PAGES, max_depth: int = MAX_DEPTH) -> list[dict]:
    frontier: deque[tuple[str, int]] = deque([(seed_url, 0)])
    seen = {seed_url} # have we already put this URL in the queue?
    visited: set[str] = set() # have we already downloaded & parsed this
    results = []

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    # breadth first search crawler
    while frontier and len(visited) < max_pages:
        url, depth = frontier.popleft()

        # Dynamic checks belong here, right before fetching: already-visited
        # (defensive, since enqueue-time dedup already prevents this), robots.txt,
        # and the politeness delay that paces every real request to the site.
        if url in visited:
            continue
        if not get_robots_parser(session).can_fetch(USER_AGENT, url): # asks whether this URL is allower for our user agent
            print(f"skip (robots disallow): {url}")
            continue

        time.sleep(CRAWL_DELAY_SECONDS)

        try:
            response = fetch(session, url) # download this URL
        except requests.exceptions.HTTPError as exc: # the server answered, but w/ an error
            status = exc.response.status_code if exc.response is not None else None
            if status == 429: # rate limited
                retry_after = int(exc.response.headers.get("Retry-After", CRAWL_DELAY_SECONDS))
                print(f"429 for {url}, waiting {retry_after}s before retrying")
                time.sleep(retry_after)
                frontier.appendleft((url, depth))
                continue
            print(f"skip (HTTP {status}): {url}")
            continue
        except requests.exceptions.RequestException as exc: # everything else
            print(f"skip (request error: {exc}): {url}") # fade this URL
            continue

        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            print(f"skip (non-HTML content-type {content_type!r}): {url}")
            continue

        visited.add(url)
        page = parse_page(url, response.text)
        results.append(page)

        canonical_note = (
            f" canonical={page['canonical_url']}"
            if page["canonical_url"] != page["url"]
            else ""
        )
        print(
            f"[{len(visited)}] depth={depth} {page['url']} — {page['title']!r} "
            f"({len(page['text'])} chars, {len(page['links'])} links)" + canonical_note
        )

        if depth < max_depth:
            for link in page["links"]:
                normalized = normalize_url(link)
                if normalized in seen: # have we already put this URL in the queue?
                    continue
                if not should_crawl(normalized): # check basic filters for URL
                    continue
                seen.add(normalized) # put URL in queue
                frontier.append((normalized, depth + 1)) # append URL to queue

    return results # in-memory array of document results


if __name__ == "__main__":
    crawl(SEED_URL, MAX_PAGES, MAX_DEPTH)
