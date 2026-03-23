"""GitHub archiving: daily markdown, README rebuild, git commit & push."""

import datetime
import os
import subprocess

from src import config
from src.dedup import ArchiveDB


def md_escape(s: str) -> str:
    """Escape pipe characters for Markdown table cells."""
    return s.replace("|", "\\|")


def save_daily_markdown(
    date: datetime.date,
    papers: list[dict],
    analyses: list[str],
):
    """Write daily briefing markdown file."""
    year_month = date.strftime("%Y/%m")
    filename = date.strftime("%Y-%m-%d.md")
    dir_path = os.path.join(config.REPO_DIR, year_month)
    os.makedirs(dir_path, exist_ok=True)

    filepath = os.path.join(dir_path, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# 📚 AI/LLM 논문 데일리 브리핑 - {date.isoformat()}\n\n")
        f.write(f"> 자동 생성 | 5개 트랙 기반 상위 2편 분석\n\n")

        # Paper list table
        f.write("## 📋 논문 목록\n\n")
        f.write("| # | 제목 | 트랙 | 소스 | 링크 |\n")
        f.write("|---|------|------|------|------|\n")
        for i, p in enumerate(papers, 1):
            title = md_escape(p.get("title", p.get("id", "")))
            track = p.get("track", "Other")
            source = "Fresh" if p.get("source") == "arxiv_fresh" else "Track Pool"
            url = p.get("url", "")
            f.write(f"| {i} | {title} | {track} | {source} | [arXiv]({url}) |\n")

        # Detailed analyses
        f.write("\n## 📝 상세 분석\n\n")
        for i, (paper, analysis) in enumerate(zip(papers, analyses)):
            title = paper.get("title", paper.get("id", ""))
            track = paper.get("track", "Other")
            url = paper.get("url", "")
            f.write(f"### {i+1}. {title}\n\n")
            f.write(f"**트랙**: {track} | **링크**: [arXiv]({url})\n\n")
            if analysis:
                f.write(f"{analysis}\n\n")
            else:
                f.write("_분석 생성 실패_\n\n")

    return filepath


def rebuild_readme(archive_db: ArchiveDB):
    """Rebuild README.md with 5-track structure."""
    readme_path = os.path.join(config.REPO_DIR, "README.md")

    # Collect archive entries from existing daily files
    archive_entries = []
    for root, dirs, files in os.walk(config.REPO_DIR):
        for fname in files:
            if fname.endswith(".md") and fname[:4].isdigit() and len(fname) == 13:
                rel = os.path.relpath(os.path.join(root, fname), config.REPO_DIR)
                date_str = fname.replace(".md", "")
                archive_entries.append((date_str, rel))
    archive_entries.sort(key=lambda x: x[0], reverse=True)

    # Group archived papers by track
    categorized: dict[str, list] = {}
    for pid, info in sorted(archive_db.data.items(), key=lambda x: x[1].get("date_briefed", ""), reverse=True):
        track = info.get("track", "Other")
        if track not in categorized:
            categorized[track] = []
        categorized[track].append({"id": pid, **info})

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# 🤖 Daily AI/LLM Paper Briefing\n\n")
        f.write("AI/LLM 관련 논문을 매일 자동으로 검색하고 한국어로 깊이 있게 분석합니다.\n\n")

        # Track descriptions
        f.write("## 🎯 트랙 구조\n\n")
        f.write("| Track | 이름 | 범위 |\n")
        f.write("|-------|------|------|\n")
        track_scopes = [
            "training/serving systems, scheduling, parallelism, goodput, runtime",
            "instruction tuning, RLHF, DPO/GRPO, reward modeling, alignment",
            "reasoning RL, process reward, CoT efficiency, adaptive compute",
            "tool use, multi-agent, planning, browser/computer-use, evaluation",
            "speculative decoding, KV cache, quantization, long context, sparsity",
        ]
        for i, track in enumerate(config.TRACKS):
            f.write(f"| {i+1} | {track['name']} | {track_scopes[i]} |\n")
        f.write("\n")

        # Monitoring orgs
        f.write("## 🏢 모니터링 기관 (가중치 부여)\n\n")
        f.write("OpenAI, Anthropic, Meta, NVIDIA, Together AI, Google DeepMind, Apple, ByteDance, ")
        f.write("Microsoft, DeepSeek, Alibaba, Tencent, UC Berkeley, Stanford, MIT, CMU\n\n")

        # How it works
        f.write("## ⚙️ 운영 방식\n\n")
        f.write("- **매일 2편**: Fresh arXiv 1편 (14일 이내) + Track Pool 1편 (round-robin)\n")
        f.write("- **분석 형식**: Problem / Background / Methodology / Evaluation / Key Intuition\n")
        f.write("- **Slack DM**: KST 08:00 자동 전송\n")
        f.write("- **중복 방지**: 2-layer dedup (fresh_db + archive_db)\n\n")

        # Recent papers by track
        f.write("## 📊 최근 논문 (트랙별)\n\n")
        track_order = [t["name"] for t in config.TRACKS]
        for track_name in track_order:
            papers = categorized.get(track_name, [])
            if not papers:
                continue
            f.write(f"### {track_name}\n\n")
            f.write("| 날짜 | 제목 | 링크 |\n")
            f.write("|------|------|------|\n")
            for info in papers[:20]:  # Last 20 per track
                date = info.get("date_briefed", "")
                title = md_escape(info.get("title", info.get("id", "")))
                url = f"https://arxiv.org/abs/{info.get('id', info.get('arxiv_id', ''))}"
                f.write(f"| {date} | {title} | [arXiv]({url}) |\n")
            f.write("\n")

        # Archive
        f.write("## 📚 브리핑 아카이브\n\n")
        for date_str, rel_path in archive_entries:
            f.write(f"- [{date_str}](./{rel_path})\n")
        f.write("")


def git_commit_and_push(date: datetime.date, daily_md_path: str):
    """Git add specific files, commit, and push."""
    os.chdir(config.REPO_DIR)

    files_to_add = [
        daily_md_path,
        "papers_db/fresh_db.json",
        "papers_db/archive_db.json",
        "papers_db/track_pool.json",
        "README.md",
    ]

    for f in files_to_add:
        if os.path.exists(os.path.join(config.REPO_DIR, f)):
            subprocess.run(["git", "add", f], check=False)

    result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
    if result.returncode != 0:
        subprocess.run(
            ["git", "commit", "-m", f"📚 Daily briefing: {date.isoformat()}"],
            check=True,
        )
        push_result = subprocess.run(["git", "push"], capture_output=True)
        if push_result.returncode != 0:
            subprocess.run(
                ["git", "push", "--set-upstream", "origin", "main"],
                check=True,
            )
        print(f"  Pushed to GitHub")
    else:
        print("  No changes to commit")
