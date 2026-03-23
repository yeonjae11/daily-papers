"""Paper scoring: positive keywords, org boost, exclusion with core-keyword override."""

from src import config


def _has_core_keyword(text: str) -> bool:
    """Check if text contains ANY core keyword (binary presence check)."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in config.CORE_KEYWORDS)


def _has_hard_exclude(text: str) -> bool:
    """Check if text contains any hard exclusion keyword."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in config.EXCLUDE_HARD)


def _count_low_priority(text: str) -> int:
    """Count low-priority (hardware) keywords in text."""
    text_lower = text.lower()
    return sum(1 for kw in config.EXCLUDE_LOW_PRIORITY if kw in text_lower)


def score_paper(paper: dict) -> tuple:
    """Score a paper and assign it to the best matching track.

    Returns:
        (score, track_name) where score < 0 means rejected.
    """
    title = paper.get("title", "")
    abstract = paper.get("abstract", "")
    text = (title + " " + abstract).lower()
    affiliation_text = paper.get("affiliation_text", text)
    categories = paper.get("categories", [])

    # Rule 1: Core keyword gate
    has_core = _has_core_keyword(text)

    # Rule 2: Exclusion check (only if no core keyword)
    if not has_core and _has_hard_exclude(text):
        return (-1.0, "Excluded")

    # Rule 3: cs.LG extra strictness — must have core keyword
    if any(c == "cs.LG" for c in categories) and not has_core:
        return (-1.0, "Excluded")

    # Score: match against each track's positive keywords
    best_score = 0.0
    best_track = "Other"

    for track in config.TRACKS:
        track_score = 0.0
        for kw in track["positive_keywords"]:
            if kw in text:
                track_score += config.KEYWORD_MATCH_SCORE
        if track_score > best_score:
            best_score = track_score
            best_track = track["name"]

    # Org boost
    for org in config.ORG_BOOST:
        if org in affiliation_text:
            best_score += config.ORG_BOOST_SCORE

    # Low-priority penalty
    lp_count = _count_low_priority(text)
    best_score += lp_count * config.LOW_PRIORITY_PENALTY

    return (best_score, best_track)
