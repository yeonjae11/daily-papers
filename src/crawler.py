"""Awesome repo crawler: fetch READMEs, extract arXiv paper URLs, build track pool."""

import json
import os
import re
import datetime
import urllib.request

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


def _is_year_2024_plus(arxiv_id: str) -> bool:
    """Check if arXiv ID is from 2024 or later (prefix >= 24)."""
    try:
        year_prefix = int(arxiv_id[:2])
        return year_prefix >= 24
    except (ValueError, IndexError):
        return False


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
                if not _is_year_2024_plus(aid):
                    continue
                pool[track_name].append({
                    "arxiv_id": aid,
                    "source_repo": repo,
                })
                existing_ids.add(aid)
                new_count += 1

            print(f"    Found {len(arxiv_ids)} arXiv IDs, {new_count} new (2024+)")

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
