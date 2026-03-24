#!/usr/bin/env python3
"""
Daily AI/LLM Paper Briefing - Orchestrator
- Selects 2 papers daily: 1 fresh arXiv + 1 from track pool (round-robin)
- Deep 5-section Korean analysis per paper via Claude API
- Posts to Slack DM, archives to GitHub
"""

import datetime
import sys

from src import config
from src.dedup import FreshDB, ArchiveDB
from src import crawler
from src import arxiv_search
from src.selector import select_daily_papers
from src.analyzer import analyze_paper
from src import slack_sender
from src import github_archive


def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def main():
    today = datetime.date.today()
    dry_run = "--dry-run" in sys.argv
    do_crawl = "--crawl" in sys.argv
    no_git = "--no-git" in sys.argv

    log(f"=== Daily AI/LLM Paper Briefing ({today.isoformat()}) ===")
    if dry_run:
        log("DRY RUN mode: will not post to Slack or push to GitHub")

    # Validate env
    if not dry_run and not config.SLACK_BOT_TOKEN:
        log("[ERROR] SLACK_BOT_TOKEN not set")
        sys.exit(1)

    # Analysis mode: API key or Claude CLI
    import shutil
    if config.ANTHROPIC_API_KEY:
        log("Analysis mode: Anthropic API")
    elif shutil.which("claude"):
        log("Analysis mode: Claude Code CLI (subscription)")
    else:
        log("[ERROR] Neither ANTHROPIC_API_KEY nor claude CLI found")
        sys.exit(1)

    # Load DBs
    fresh_db = FreshDB(config.FRESH_DB_PATH)
    archive_db = ArchiveDB(config.ARCHIVE_DB_PATH)

    # Crawl if requested or stale (>7 days)
    if do_crawl or crawler.needs_refresh():
        log("[1/5] Crawling awesome repos for track pool...")
        pool = crawler.crawl_awesome_repos()
        crawler.save_pool(pool)
        log(f"  Track pool updated ({sum(len(v) for k, v in pool.items() if k != 'last_crawled')} total papers)")
    else:
        log("[1/5] Track pool is fresh, skipping crawl")

    # Load track pool
    import json, os
    if os.path.exists(config.TRACK_POOL_PATH):
        with open(config.TRACK_POOL_PATH, "r", encoding="utf-8") as f:
            track_pool = json.load(f)
    else:
        log("[ERROR] No track_pool.json found. Run with --crawl first.")
        sys.exit(1)

    # Collect fresh papers from arXiv
    log("[2/5] Collecting fresh papers from arXiv...")
    fresh_papers = arxiv_search.collect_fresh_papers(fresh_db, archive_db)
    log(f"  Found {len(fresh_papers)} candidate papers")
    for i, p in enumerate(fresh_papers[:5], 1):
        log(f"  {i}. [{p['score']:.1f}] [{p['track']}] {p['title'][:70]}")

    # Select 2 papers
    log("[3/5] Selecting daily papers...")
    try:
        papers = select_daily_papers(today, fresh_db, archive_db, track_pool, fresh_papers)
    except RuntimeError as e:
        log(f"[ERROR] Selection failed: {e}")
        sys.exit(1)

    for i, p in enumerate(papers, 1):
        log(f"  Paper {i}: [{p.get('track')}] {p.get('title', p['id'])}")

    # Analyze each paper
    log("[4/5] Generating deep analyses...")
    analyses = []
    for i, paper in enumerate(papers, 1):
        log(f"  Analyzing paper {i}...")
        analysis = analyze_paper(paper)
        analyses.append(analysis)
        if analysis:
            log(f"  Paper {i} analysis: {len(analysis)} chars")
            # Update archive_db title if it was a pool paper with placeholder title
            if paper.get("source") == "track_pool" and archive_db.contains(paper["id"]):
                archive_db.data[paper["id"]]["title"] = paper.get("title", paper["id"])
        else:
            log(f"  [WARN] Paper {i} analysis failed")

    if dry_run:
        log("[DRY RUN] Analyses generated. Printing to stdout:")
        for i, (p, a) in enumerate(zip(papers, analyses), 1):
            print(f"\n{'='*60}")
            print(f"Paper {i}: {p.get('title', p['id'])} [{p.get('track')}]")
            print(f"URL: {p.get('url')}")
            print(f"{'='*60}")
            print(a or "(analysis failed)")
        log("=== Dry run complete ===")
        # Still save DBs so dedup state is preserved
        fresh_db.save()
        archive_db.save()
        return

    # Post to Slack (partial-failure: send whatever succeeded)
    log("[5/5] Posting to Slack & archiving...")
    if any(analyses):
        slack_sender.send_briefing(today.isoformat(), papers, analyses)
        log("  Posted to Slack")
    else:
        log("  [ERROR] All analyses failed, skipping Slack")

    # Archive to GitHub
    daily_path = github_archive.save_daily_markdown(today, papers, analyses)
    log(f"  Saved {daily_path}")
    github_archive.rebuild_readme(archive_db)
    log("  README rebuilt")

    # Save DBs
    fresh_db.save()
    archive_db.save()

    # Git commit & push
    if no_git:
        log("  Skipping git commit/push (--no-git)")
    else:
        github_archive.git_commit_and_push(today, daily_path)

    log("=== Done! ===")


if __name__ == "__main__":
    main()
