"""Awesome repo crawler: fetch READMEs, extract arXiv paper URLs, build track pool."""

import json
import os
import re
import datetime
import time
import urllib.request
import urllib.parse

from src import config

# Regex to match arXiv URLs in markdown
ARXIV_PATTERN = re.compile(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?")


def _fetch_readme(repo: str, token: str = None) -> str:
    """Fetch raw README.md from a GitHub repo."""
    # Try main branch first, then master
    for branch in ["main", "master"]:
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/README.md"
        headers = {"User-Agent": "DailyLLMBriefing/2.0"}
        if token:
            headers["Authorization"] = f"token {token}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except Exception:
            continue
    return ""


def _extract_arxiv_ids(readme_text: str) -> list[str]:
    """Extract unique arXiv IDs from README text."""
    matches = ARXIV_PATTERN.findall(readme_text)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            unique.append(m)
    return unique


def _is_after_cutoff(arxiv_id: str, min_yymm: int = 2406) -> bool:
    """Check if arXiv ID is from after the cutoff (default: 2024 H2)."""
    try:
        yymm = int(arxiv_id[:4])
        return yymm >= min_yymm
    except (ValueError, IndexError):
        return False


def _is_ml_relevant(title: str) -> bool:
    """Check if a paper title is AI/ML relevant (not pure systems)."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in config.ML_RELEVANCE_KEYWORDS)


def _fetch_dblp_proceedings(dblp_venue: str, year: int) -> list[dict]:
    """Fetch papers from DBLP conference proceedings.

    Returns list of dicts with 'title' and 'arxiv_id' keys.
    """
    venue_key = dblp_venue.split("/")[-1]  # e.g., "mlsys" from "conf/mlsys"
    toc_key = f"db/{dblp_venue}/{venue_key}{year}.bht:"
    encoded_q = urllib.parse.quote(f"toc:{toc_key}")
    url = f"https://dblp.org/search/publ/api?q={encoded_q}&h=1000&format=json"

    headers = {"User-Agent": "DailyLLMBriefing/2.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"    [WARN] DBLP fetch failed for {venue_key} {year}: {e}")
        return []

    papers = []
    hits = data.get("result", {}).get("hits", {}).get("hit", [])
    for hit in hits:
        info = hit.get("info", {})
        title = info.get("title", "")
        ee = info.get("ee", "")
        # ee can be a string or list
        if isinstance(ee, str):
            ee = [ee]
        elif not isinstance(ee, list):
            ee = []

        # Try to find arXiv ID from ee URLs
        arxiv_id = None
        for link in ee:
            match = ARXIV_PATTERN.search(link)
            if match:
                arxiv_id = match.group(1)
                break

        if arxiv_id and title:
            papers.append({"title": title, "arxiv_id": arxiv_id})

    return papers


def crawl_awesome_repos(tracks: list[dict] = None, token: str = None) -> dict:
    """Crawl all awesome repos and build track pool.

    Returns:
        dict with track names as keys and lists of paper entries as values,
        plus a 'last_crawled' timestamp.
    """
    if tracks is None:
        tracks = config.TRACKS
    if token is None:
        token = config.GITHUB_TOKEN

    # Load existing pool for incremental update
    pool = {"last_crawled": None}
    if os.path.exists(config.TRACK_POOL_PATH):
        with open(config.TRACK_POOL_PATH, "r", encoding="utf-8") as f:
            pool = json.load(f)

    for track in tracks:
        track_name = track["name"]
        if track_name not in pool:
            pool[track_name] = []

        existing_ids = {p["arxiv_id"] for p in pool[track_name]}

        min_yymm = track.get("min_yymm", 2406)
        cutoff_label = f"{2000 + min_yymm // 100} {'H2' if min_yymm % 100 >= 6 else 'H1'}+"
        if min_yymm % 100 == 1:
            cutoff_label = f"{2000 + min_yymm // 100}+"

        for repo in track["awesome_repos"]:
            print(f"  Crawling {repo} for {track_name}...")
            readme = _fetch_readme(repo, token)
            if not readme:
                print(f"    [WARN] Could not fetch README from {repo}, skipping")
                continue

            arxiv_ids = _extract_arxiv_ids(readme)
            new_count = 0
            for aid in arxiv_ids:
                if aid in existing_ids:
                    continue
                if not _is_after_cutoff(aid, min_yymm):
                    continue
                pool[track_name].append({
                    "arxiv_id": aid,
                    "source_repo": repo,
                })
                existing_ids.add(aid)
                new_count += 1

            print(f"    Found {len(arxiv_ids)} arXiv IDs, {new_count} new ({cutoff_label})")

        # Crawl conference proceedings from DBLP (if configured)
        for conf in track.get("conferences", []):
            dblp_venue = conf["dblp_venue"]
            venue_label = dblp_venue.split("/")[-1].upper()
            for year in conf["years"]:
                print(f"  Crawling {venue_label} {year} from DBLP for {track_name}...")
                papers = _fetch_dblp_proceedings(dblp_venue, year)
                new_count = 0
                for paper in papers:
                    aid = paper["arxiv_id"]
                    if aid in existing_ids:
                        continue
                    if track.get("ml_filter") and not _is_ml_relevant(paper["title"]):
                        continue
                    pool[track_name].append({
                        "arxiv_id": aid,
                        "source_repo": f"dblp:{dblp_venue}/{year}",
                    })
                    existing_ids.add(aid)
                    new_count += 1
                ml_note = " ML-relevant" if track.get("ml_filter") else ""
                print(f"    Found {len(papers)} papers, {new_count} new{ml_note}")
                time.sleep(1)  # Respect DBLP rate limits

    pool["last_crawled"] = datetime.datetime.now().isoformat()
    return pool


def save_pool(pool: dict):
    """Save track pool to JSON."""
    os.makedirs(os.path.dirname(config.TRACK_POOL_PATH), exist_ok=True)
    with open(config.TRACK_POOL_PATH, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)


def needs_refresh(max_age_days: int = 7) -> bool:
    """Check if track pool needs refreshing."""
    if not os.path.exists(config.TRACK_POOL_PATH):
        return True
    try:
        with open(config.TRACK_POOL_PATH, "r", encoding="utf-8") as f:
            pool = json.load(f)
        last = pool.get("last_crawled")
        if not last:
            return True
        last_dt = datetime.datetime.fromisoformat(last)
        age = datetime.datetime.now() - last_dt
        return age.days >= max_age_days
    except Exception:
        return True
