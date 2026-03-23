"""arXiv API search for fresh paper discovery."""

import datetime
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from src import config

ARXIV_API = "http://export.arxiv.org/api/query"
ARXIV_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def search_arxiv(query: str, max_results: int = 30, days_back: int = None) -> list:
    """Search arXiv API and return papers within the time window."""
    if days_back is None:
        days_back = config.FRESH_DAYS_BACK

    cat_filter = " OR ".join(f"cat:{c}" for c in config.ARXIV_CATEGORIES)
    full_query = f"({query}) AND ({cat_filter})"

    params = urllib.parse.urlencode({
        "search_query": full_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })

    url = f"{ARXIV_API}?{params}"
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_back)
    papers = []

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DailyLLMBriefing/2.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            tree = ET.parse(resp)
    except Exception as e:
        print(f"  [WARN] arXiv query failed: {e}")
        return []

    root = tree.getroot()
    for entry in root.findall("atom:entry", ARXIV_NS):
        published_str = entry.find("atom:published", ARXIV_NS).text
        published = datetime.datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        if published < cutoff:
            continue

        arxiv_id = re.sub(r"v\d+$", "", entry.find("atom:id", ARXIV_NS).text.split("/abs/")[-1])
        title = entry.find("atom:title", ARXIV_NS).text.strip().replace("\n", " ")
        abstract = entry.find("atom:summary", ARXIV_NS).text.strip().replace("\n", " ")
        authors = [a.find("atom:name", ARXIV_NS).text for a in entry.findall("atom:author", ARXIV_NS)]
        categories = [c.get("term") for c in entry.findall("atom:category", ARXIV_NS)]
        affiliation_text = " ".join(authors).lower() + " " + abstract.lower()

        papers.append({
            "id": arxiv_id,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "categories": categories,
            "published": published.isoformat(),
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "affiliation_text": affiliation_text,
        })

    return papers


def collect_fresh_papers(fresh_db, archive_db) -> list[dict]:
    """Collect fresh papers from arXiv using all track keywords."""
    from src.scoring import score_paper

    all_papers = {}

    # Build search queries from all tracks
    queries = []
    for track in config.TRACKS:
        # Pick top 5 most distinctive keywords per track for search
        top_kws = track["positive_keywords"][:5]
        query = " OR ".join(f'"{kw}"' for kw in top_kws)
        queries.append(query)

    for q in queries:
        print(f"  Searching: {q[:80]}...")
        results = search_arxiv(q, max_results=30)
        for p in results:
            if fresh_db.contains(p["id"]) or archive_db.contains(p["id"]):
                continue
            if p["id"] not in all_papers:
                all_papers[p["id"]] = p
        time.sleep(3)  # arXiv rate limiting

    # Score all collected papers
    papers = list(all_papers.values())
    for p in papers:
        score, track = score_paper(p)
        p["score"] = score
        p["track"] = track

    # Filter out rejected papers (score < 0)
    papers = [p for p in papers if p["score"] >= 0]
    papers.sort(key=lambda x: x["score"], reverse=True)
    return papers
