"""Slack DM delivery: header + per-paper analysis messages."""

import time

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src import config


def _split_message(text: str, max_len: int = 3800) -> list[str]:
    """Split text into chunks respecting Slack's 4000 char limit."""
    if len(text) <= max_len:
        return [text]

    chunks = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_len and current:
            chunks.append(current)
            current = line
        else:
            current += "\n" + line if current else line
    if current:
        chunks.append(current)
    return chunks


def send_briefing(date_str: str, papers: list[dict], analyses: list[str]):
    """Send daily briefing to Slack DM.

    Sends exactly 3 messages: 1 header + 2 paper analyses.
    """
    client = WebClient(token=config.SLACK_BOT_TOKEN)

    # Header message
    lines = [f"🤖 [{date_str}] AI/LLM 논문 데일리 브리핑\n"]
    for i, p in enumerate(papers, 1):
        track = p.get("track", "Other")
        title = p.get("title", p.get("id", "Unknown"))
        source = "📡 Fresh" if p.get("source") == "arxiv_fresh" else "📚 Track"
        lines.append(f"{i}. {title}\n   [{track}] {source}")
    header = "\n".join(lines)

    try:
        client.chat_postMessage(channel=config.SLACK_CHANNEL, text=header)
    except SlackApiError as e:
        print(f"  [ERROR] Slack header: {e}")

    # Per-paper analysis messages
    for i, (paper, analysis) in enumerate(zip(papers, analyses)):
        if not analysis:
            error_msg = f"⚠️ Paper {i+1} ({paper.get('title', paper['id'])}): 분석 생성 실패"
            try:
                client.chat_postMessage(channel=config.SLACK_CHANNEL, text=error_msg)
            except SlackApiError as e:
                print(f"  [ERROR] Slack error msg: {e}")
            continue

        title = paper.get("title", paper.get("id", "Unknown"))
        track = paper.get("track", "Other")
        url = paper.get("url", "")
        prefix = f"📄 *{i+1}. {title}*\n🔗 {url}\n🏷️ {track}\n\n"
        full_msg = prefix + analysis

        chunks = _split_message(full_msg)
        for chunk in chunks:
            try:
                client.chat_postMessage(channel=config.SLACK_CHANNEL, text=chunk)
                time.sleep(1)
            except SlackApiError as e:
                print(f"  [ERROR] Slack paper {i+1}: {e}")
