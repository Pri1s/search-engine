#!/usr/bin/env python3
"""Build the initial basketball-search corpus from curated Wikipedia articles.

Wikimedia Special:Export returns current article source without page chrome,
ads, comments, or navigation. This script turns that source into clean prose
from a fixed, reviewable list rather than discovering arbitrary search pages.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
DOC_DIR = ROOT / "data" / "documents"
METADATA_PATH = ROOT / "data" / "metadata.json"
EXPORT_URL = "https://en.wikipedia.org/w/index.php"
USER_AGENT = "basketball-search-engine-initial-corpus/1.0 (educational local project)"


def document(
    title: str,
    category: str,
    *,
    teams: list[str] | None = None,
    players: list[str] | None = None,
) -> dict[str, object]:
    return {
        "title": title,
        "category": category,
        "teams": teams or [],
        "players": players or [],
    }


# Curated for durable basketball knowledge.  The list intentionally balances
# profiles, franchise context, major Finals, and tactical/conceptual pages.
DOCS = [
    # Player profiles (36)
    document("Michael Jordan", "player_profile", teams=["Chicago Bulls", "Washington Wizards"], players=["Michael Jordan"]),
    document("LeBron James", "player_profile", teams=["Cleveland Cavaliers", "Miami Heat", "Los Angeles Lakers"], players=["LeBron James"]),
    document("Kobe Bryant", "player_profile", teams=["Los Angeles Lakers"], players=["Kobe Bryant"]),
    document("Stephen Curry", "player_profile", teams=["Golden State Warriors"], players=["Stephen Curry"]),
    document("Nikola Jokić", "player_profile", teams=["Denver Nuggets"], players=["Nikola Jokić"]),
    document("Magic Johnson", "player_profile", teams=["Los Angeles Lakers"], players=["Magic Johnson"]),
    document("Larry Bird", "player_profile", teams=["Boston Celtics"], players=["Larry Bird"]),
    document("Tim Duncan", "player_profile", teams=["San Antonio Spurs"], players=["Tim Duncan"]),
    document("Shaquille O'Neal", "player_profile", teams=["Orlando Magic", "Los Angeles Lakers", "Miami Heat", "Phoenix Suns", "Cleveland Cavaliers", "Boston Celtics"], players=["Shaquille O'Neal"]),
    document("Kareem Abdul-Jabbar", "player_profile", teams=["Milwaukee Bucks", "Los Angeles Lakers"], players=["Kareem Abdul-Jabbar"]),
    document("Bill Russell", "player_profile", teams=["Boston Celtics"], players=["Bill Russell"]),
    document("Wilt Chamberlain", "player_profile", teams=["Philadelphia/San Francisco Warriors", "Philadelphia 76ers", "Los Angeles Lakers"], players=["Wilt Chamberlain"]),
    document("Hakeem Olajuwon", "player_profile", teams=["Houston Rockets", "Toronto Raptors"], players=["Hakeem Olajuwon"]),
    document("Kevin Durant", "player_profile", teams=["Seattle SuperSonics/Oklahoma City Thunder", "Golden State Warriors", "Brooklyn Nets", "Phoenix Suns"], players=["Kevin Durant"]),
    document("Giannis Antetokounmpo", "player_profile", teams=["Milwaukee Bucks"], players=["Giannis Antetokounmpo"]),
    document("Luka Dončić", "player_profile", teams=["Dallas Mavericks", "Los Angeles Lakers"], players=["Luka Dončić"]),
    document("Chris Paul", "player_profile", teams=["New Orleans Hornets", "Los Angeles Clippers", "Houston Rockets", "Oklahoma City Thunder", "Phoenix Suns", "Golden State Warriors"], players=["Chris Paul"]),
    document("Steve Nash", "player_profile", teams=["Phoenix Suns", "Dallas Mavericks", "Los Angeles Lakers"], players=["Steve Nash"]),
    document("Allen Iverson", "player_profile", teams=["Philadelphia 76ers", "Denver Nuggets", "Detroit Pistons", "Memphis Grizzlies"], players=["Allen Iverson"]),
    document("Dwyane Wade", "player_profile", teams=["Miami Heat", "Chicago Bulls", "Cleveland Cavaliers"], players=["Dwyane Wade"]),
    document("Kevin Garnett", "player_profile", teams=["Minnesota Timberwolves", "Boston Celtics", "Brooklyn Nets"], players=["Kevin Garnett"]),
    document("Dirk Nowitzki", "player_profile", teams=["Dallas Mavericks"], players=["Dirk Nowitzki"]),
    document("David Robinson (basketball)", "player_profile", teams=["San Antonio Spurs"], players=["David Robinson"]),
    document("Moses Malone", "player_profile", teams=["Houston Rockets", "Philadelphia 76ers", "Washington Bullets", "Atlanta Hawks", "Milwaukee Bucks", "San Antonio Spurs"], players=["Moses Malone"]),
    document("Oscar Robertson", "player_profile", teams=["Cincinnati Royals", "Milwaukee Bucks"], players=["Oscar Robertson"]),
    document("Jerry West", "player_profile", teams=["Los Angeles Lakers"], players=["Jerry West"]),
    document("James Harden", "player_profile", teams=["Oklahoma City Thunder", "Houston Rockets", "Brooklyn Nets", "Philadelphia 76ers", "Los Angeles Clippers"], players=["James Harden"]),
    document("Kawhi Leonard", "player_profile", teams=["San Antonio Spurs", "Toronto Raptors", "Los Angeles Clippers"], players=["Kawhi Leonard"]),
    document("Scottie Pippen", "player_profile", teams=["Chicago Bulls", "Houston Rockets", "Portland Trail Blazers"], players=["Scottie Pippen"]),
    document("Charles Barkley", "player_profile", teams=["Philadelphia 76ers", "Phoenix Suns", "Houston Rockets"], players=["Charles Barkley"]),
    document("Reggie Miller", "player_profile", teams=["Indiana Pacers"], players=["Reggie Miller"]),
    document("Ray Allen", "player_profile", teams=["Milwaukee Bucks", "Seattle SuperSonics", "Boston Celtics", "Miami Heat"], players=["Ray Allen"]),
    document("Damian Lillard", "player_profile", teams=["Portland Trail Blazers", "Milwaukee Bucks"], players=["Damian Lillard"]),
    document("Jayson Tatum", "player_profile", teams=["Boston Celtics"], players=["Jayson Tatum"]),
    document("Joel Embiid", "player_profile", teams=["Philadelphia 76ers"], players=["Joel Embiid"]),
    document("Victor Wembanyama", "player_profile", teams=["San Antonio Spurs"], players=["Victor Wembanyama"]),

    # Franchise context (10)
    document("Golden State Warriors", "team_analysis", teams=["Golden State Warriors"]),
    document("Chicago Bulls", "team_analysis", teams=["Chicago Bulls"]),
    document("Los Angeles Lakers", "team_analysis", teams=["Los Angeles Lakers"]),
    document("Boston Celtics", "team_analysis", teams=["Boston Celtics"]),
    document("San Antonio Spurs", "team_analysis", teams=["San Antonio Spurs"]),
    document("Miami Heat", "team_analysis", teams=["Miami Heat"]),
    document("Denver Nuggets", "team_analysis", teams=["Denver Nuggets"]),
    document("Cleveland Cavaliers", "team_analysis", teams=["Cleveland Cavaliers"]),
    document("Houston Rockets", "team_analysis", teams=["Houston Rockets"]),
    document("Dallas Mavericks", "team_analysis", teams=["Dallas Mavericks"]),

    # Historically consequential NBA Finals (21)
    document("1967 NBA Finals", "historical_analysis", teams=["Philadelphia 76ers", "San Francisco Warriors"], players=["Wilt Chamberlain", "Hal Greer", "Rick Barry"]),
    document("1969 NBA Finals", "historical_analysis", teams=["Boston Celtics", "Los Angeles Lakers"], players=["Bill Russell", "Jerry West", "Elgin Baylor", "John Havlicek"]),
    document("1976 NBA Finals", "historical_analysis", teams=["Boston Celtics", "Phoenix Suns"], players=["Jo Jo White", "John Havlicek", "Paul Westphal"]),
    document("1980 NBA Finals", "historical_analysis", teams=["Los Angeles Lakers", "Philadelphia 76ers"], players=["Magic Johnson", "Kareem Abdul-Jabbar", "Julius Erving"]),
    document("1984 NBA Finals", "historical_analysis", teams=["Boston Celtics", "Los Angeles Lakers"], players=["Larry Bird", "Magic Johnson", "Kevin McHale"]),
    document("1987 NBA Finals", "historical_analysis", teams=["Los Angeles Lakers", "Boston Celtics"], players=["Magic Johnson", "Larry Bird", "James Worthy"]),
    document("1991 NBA Finals", "historical_analysis", teams=["Chicago Bulls", "Los Angeles Lakers"], players=["Michael Jordan", "Magic Johnson", "Scottie Pippen"]),
    document("1993 NBA Finals", "historical_analysis", teams=["Chicago Bulls", "Phoenix Suns"], players=["Michael Jordan", "Charles Barkley", "Scottie Pippen"]),
    document("1998 NBA Finals", "historical_analysis", teams=["Chicago Bulls", "Utah Jazz"], players=["Michael Jordan", "Scottie Pippen", "Karl Malone", "John Stockton"]),
    document("2004 NBA Finals", "historical_analysis", teams=["Detroit Pistons", "Los Angeles Lakers"], players=["Chauncey Billups", "Ben Wallace", "Kobe Bryant", "Shaquille O'Neal"]),
    document("2008 NBA Finals", "historical_analysis", teams=["Boston Celtics", "Los Angeles Lakers"], players=["Kevin Garnett", "Paul Pierce", "Ray Allen", "Kobe Bryant"]),
    document("2010 NBA Finals", "historical_analysis", teams=["Los Angeles Lakers", "Boston Celtics"], players=["Kobe Bryant", "Pau Gasol", "Paul Pierce", "Kevin Garnett"]),
    document("2011 NBA Finals", "historical_analysis", teams=["Dallas Mavericks", "Miami Heat"], players=["Dirk Nowitzki", "Jason Kidd", "LeBron James", "Dwyane Wade"]),
    document("2013 NBA Finals", "historical_analysis", teams=["Miami Heat", "San Antonio Spurs"], players=["LeBron James", "Dwyane Wade", "Tim Duncan", "Tony Parker"]),
    document("2014 NBA Finals", "historical_analysis", teams=["San Antonio Spurs", "Miami Heat"], players=["Kawhi Leonard", "Tim Duncan", "LeBron James"]),
    document("2015 NBA Finals", "historical_analysis", teams=["Golden State Warriors", "Cleveland Cavaliers"], players=["Stephen Curry", "Andre Iguodala", "LeBron James"]),
    document("2016 NBA Finals", "historical_analysis", teams=["Cleveland Cavaliers", "Golden State Warriors"], players=["LeBron James", "Kyrie Irving", "Stephen Curry", "Draymond Green"]),
    document("2017 NBA Finals", "historical_analysis", teams=["Golden State Warriors", "Cleveland Cavaliers"], players=["Kevin Durant", "Stephen Curry", "LeBron James"]),
    document("2018 NBA Finals", "historical_analysis", teams=["Golden State Warriors", "Cleveland Cavaliers"], players=["Kevin Durant", "Stephen Curry", "LeBron James"]),
    document("2019 NBA Finals", "historical_analysis", teams=["Toronto Raptors", "Golden State Warriors"], players=["Kawhi Leonard", "Kyle Lowry", "Stephen Curry"]),
    document("2020 NBA Finals", "historical_analysis", teams=["Los Angeles Lakers", "Miami Heat"], players=["LeBron James", "Anthony Davis", "Jimmy Butler"]),

    # Tactics and core basketball concepts (33)
    document("Pick and roll", "strategy_breakdown"),
    document("Triangle offense", "strategy_breakdown"),
    document("Motion offense", "strategy_breakdown"),
    document("Princeton offense", "strategy_breakdown"),
    document("Flex offense", "strategy_breakdown"),
    document("Dribble-drive motion", "strategy_breakdown"),
    document("Zone defense", "strategy_breakdown"),
    document("Man-to-man defense", "strategy_breakdown"),
    document("Full-court press", "strategy_breakdown"),
    document("Match-up zone defense", "strategy_breakdown"),
    document("Box-and-one defense", "strategy_breakdown"),
    document("1–3–1 defense and offense", "strategy_breakdown"),
    document("Small ball (basketball)", "strategy_breakdown"),
    document("Run and gun (basketball)", "strategy_breakdown"),
    document("Offensive rating", "strategy_breakdown"),
    document("Fast break", "basketball_concept"),
    document("Screen (basketball)", "basketball_concept"),
    document("Basketball moves", "basketball_concept"),
    document("Crossover (basketball)", "basketball_concept"),
    document("Euro step", "basketball_concept"),
    document("Layup", "basketball_concept"),
    document("Three-point field goal", "basketball_concept"),
    document("Slam dunk", "basketball_concept"),
    document("Alley-oop (basketball)", "basketball_concept"),
    document("Rebound (basketball)", "basketball_concept"),
    document("Assist (basketball)", "basketball_concept"),
    document("Steal (basketball)", "basketball_concept"),
    document("Block (basketball)", "basketball_concept"),
    document("Triple-double", "basketball_concept"),
    document("Basketball statistics", "basketball_concept"),
    document("Basketball positions", "basketball_concept"),
    document("Point guard", "basketball_concept"),
    document("Center (basketball)", "basketball_concept"),
]


STOP_SECTIONS = {
    "see also",
    "notes",
    "references",
    "bibliography",
    "further reading",
    "external links",
    "sources",
}


def get_export_pages(titles: list[str]) -> dict[str, str]:
    """Fetch current wikitext revisions in one Wikimedia Special:Export request."""
    result = subprocess.run(
        [
            "curl",
            "--fail",
            "--silent",
            "--show-error",
            "--location",
            "--retry",
            "3",
            "--retry-delay",
            "1",
            "--connect-timeout",
            "20",
            "--max-time",
            "60",
            "--user-agent",
            USER_AGENT,
            "--get",
            EXPORT_URL,
            "--data-urlencode",
            "title=Special:Export",
            "--data-urlencode",
            f"pages={'\n'.join(titles)}",
            "--data-urlencode",
            "curonly=1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(f"curl failed for export batch: {result.stderr.strip()}")
    try:
        root = ElementTree.fromstring(result.stdout)
    except ElementTree.ParseError as exc:
        raise RuntimeError(f"Wikimedia returned invalid export XML: {exc}") from exc

    pages = root.findall("{*}page")
    collected: dict[str, str] = {}
    for page in pages:
        page_title = page.findtext("{*}title")
        raw_text = page.findtext("{*}revision/{*}text")
        if not page_title or raw_text is None:
            continue
        collected[page_title] = raw_text

    missing = sorted(title for title in titles if title.replace("_", " ") not in collected)
    if missing:
        raise RuntimeError(f"Export did not return pages for: {', '.join(missing)}")
    return collected


REDIRECT_PATTERN = re.compile(r"^\s*#redirect\s*\[\[([^\]|#]+)", re.IGNORECASE)


def get_articles(titles: list[str]) -> dict[str, tuple[str, str]]:
    """Fetch articles and follow one redirect hop to their substantive page."""
    exported = get_export_pages(titles)
    redirected: dict[str, str] = {}
    resolved: dict[str, tuple[str, str]] = {}
    for requested_title in titles:
        page_title = requested_title.replace("_", " ")
        raw_text = exported[page_title]
        target = REDIRECT_PATTERN.match(raw_text)
        if target:
            redirected[requested_title] = target.group(1).strip()
        else:
            resolved[requested_title] = (page_title, raw_text)

    if redirected:
        targets = sorted(set(redirected.values()))
        target_pages = get_export_pages(targets)
        for requested_title, target_title in redirected.items():
            raw_text = target_pages[target_title]
            if REDIRECT_PATTERN.match(raw_text):
                raise RuntimeError(f"Redirect chain needs curation: {requested_title} -> {target_title}")
            resolved[requested_title] = (target_title, raw_text)

    return {
        requested_title: (canonical_title, clean_wikitext(raw_text))
        for requested_title, (canonical_title, raw_text) in resolved.items()
    }


def clean_wikitext(wikitext: str) -> str:
    """Convert article wikitext to searchable prose while removing page chrome."""
    text = re.sub(r"<!--.*?-->", "", wikitext, flags=re.DOTALL)
    text = re.sub(r"<ref\b[^>/]*?/>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<ref\b[^>]*>.*?</ref\s*>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<(?:gallery|math|score|timeline|syntaxhighlight)\b[^>]*>.*?</(?:gallery|math|score|timeline|syntaxhighlight)\s*>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\{\|.*?\n\|\}", "", text, flags=re.DOTALL)

    # Strip nested templates (infoboxes, citations, statistics blocks) from the
    # inside out. Their prose is either duplicated in the body or tabular.
    while True:
        stripped = re.sub(r"\{\{[^{}]*\}\}", "", text, flags=re.DOTALL)
        if stripped == text:
            break
        text = stripped

    text = re.sub(r"\[\[(?:Category|File|Image):[^\]]+\]\]", "", text, flags=re.IGNORECASE)

    def wikilink(match: re.Match[str]) -> str:
        label = match.group(1).split("|")[-1]
        return label.split("#")[0].strip()

    # Some quotations include square brackets inside a wikilink label (for
    # example, ``[[Larry Bird|[Larry] Bird]]``). Match through the closing link
    # marker before removing the editorial brackets left in the display text.
    text = re.sub(r"\[\[([^\n]*?)\]\]", wikilink, text)
    text = text.replace("[", "").replace("]", "")
    text = re.sub(r"\[https?://[^\s\]]+\s+([^\]]+)\]", r"\1", text)
    text = re.sub(r"\[https?://[^\]]+\]", "", text)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("'''", "").replace("''", "")
    text = re.sub(r"__(?:NOTOC|NOEDITSECTION|FORCETOC|TOC)__", "", text)

    kept: list[str] = []
    for raw_line in text.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        # A few complex tables are embedded in templates whose opening marker
        # disappears when the template is stripped. Discard their remaining
        # row/header syntax rather than retaining orphaned statistics columns.
        if line.startswith(("{|", "|}", "|-", "|", "!")):
            continue
        heading = re.fullmatch(r"=+\s*(.*?)\s*=+", line)
        if heading:
            line = heading.group(1).strip()
            if line.lower() in STOP_SECTIONS:
                break
        line = re.sub(r"^[*#:;]+\s*", "", line)
        if line:
            kept.append(line)
        elif kept and kept[-1]:
            kept.append("")
    text = "\n".join(kept)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def count_words(text: str) -> int:
    return len(re.findall(r"[\w]+(?:[’'-][\w]+)*", text, flags=re.UNICODE))


def main() -> int:
    if len(DOCS) != 100:
        raise RuntimeError(f"Expected 100 curated documents, found {len(DOCS)}")

    DOC_DIR.mkdir(parents=True, exist_ok=True)
    articles: dict[str, tuple[str, str]] = {}
    title_batches = [
        [str(spec["title"]) for spec in DOCS[offset : offset + 20]]
        for offset in range(0, len(DOCS), 20)
    ]
    for batch_number, titles in enumerate(title_batches, start=1):
        try:
            articles.update(get_articles(titles))
        except Exception as exc:
            raise RuntimeError(f"Unable to collect export batch {batch_number}: {exc}") from exc
        print(f"Fetched source batch {batch_number}/{len(title_batches)}", flush=True)
        if batch_number < len(title_batches):
            time.sleep(1)

    collected: list[dict[str, object]] = []
    failures: list[str] = []
    for index, spec in enumerate(DOCS, start=1):
        requested_title = str(spec["title"])
        canonical_title, content = articles[requested_title]

        word_count = count_words(content)
        if word_count < 180:
            failures.append(
                f"{index:03d} {canonical_title}: extract too short ({word_count} words)"
            )
            continue

        record = {
            "title": canonical_title,
            "url": f"https://en.wikipedia.org/wiki/{quote(canonical_title.replace(' ', '_'))}",
            "source": "Wikipedia",
            "author": None,
            "published_date": None,
            "category": spec["category"],
            "teams": spec["teams"],
            "players": spec["players"],
            "content": content,
            "word_count": word_count,
        }
        collected.append(record)
        print(f"[{index:03d}/100] {canonical_title}: {word_count} words", flush=True)

    if failures:
        print("\nCorpus was not written because some selections need review:", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return 1
    if len(collected) != 100:
        raise RuntimeError(f"Expected 100 collected documents, got {len(collected)}")

    for index, record in enumerate(collected, start=1):
        destination = DOC_DIR / f"document_{index:03d}.json"
        destination.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    distribution = dict(sorted(Counter(str(row["category"]) for row in collected).items()))
    metadata = {
        "total_documents_collected": len(collected),
        "sources_used": [
            {
                "source": "Wikipedia",
                "documents": len(collected),
                "content_endpoint": "https://en.wikipedia.org/w/index.php?title=Special:Export",
                "license_note": "Wikipedia text is generally available under CC BY-SA; retain source URLs and provide attribution in downstream use.",
            }
        ],
        "category_distribution": distribution,
        "date_range": {
            "earliest": None,
            "latest": None,
            "note": "Publication dates are not consistently exposed by Wikimedia Special:Export and are therefore null in this initial corpus.",
        },
        "extraction_limitations": [
            "Content is sourced from English Wikipedia current revisions via Wikimedia Special:Export and may change when pages are revised.",
            "The export does not supply reliable bylines or original publication dates; author and published_date are null.",
            "Team and player arrays are curated entity tags for search filtering, not exhaustive entity extraction from every mention in the article body.",
            "Tables, images, citations, and reference lists are excluded so the corpus remains focused on searchable explanatory text.",
        ],
    }
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {len(collected)} documents to {DOC_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
