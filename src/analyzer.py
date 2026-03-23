"""Deep paper analysis using Claude (API or CLI) per-paper, 5-section Korean format."""

import re
import subprocess
import shutil
import urllib.request
import xml.etree.ElementTree as ET

from src import config

ARXIV_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def fetch_paper_metadata(arxiv_id: str) -> dict:
    """Fetch title, authors, abstract from arXiv API for a single paper."""
    clean_id = re.sub(r"v\d+$", "", arxiv_id)
    url = f"http://export.arxiv.org/api/query?id_list={clean_id}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DailyLLMBriefing/2.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            tree = ET.parse(resp)
    except Exception as e:
        print(f"  [WARN] Could not fetch metadata for {arxiv_id}: {e}")
        return {}

    root = tree.getroot()
    entry = root.find("atom:entry", ARXIV_NS)
    if entry is None:
        return {}

    title_el = entry.find("atom:title", ARXIV_NS)
    summary_el = entry.find("atom:summary", ARXIV_NS)
    authors = [a.find("atom:name", ARXIV_NS).text for a in entry.findall("atom:author", ARXIV_NS)]

    return {
        "title": title_el.text.strip().replace("\n", " ") if title_el is not None else "",
        "authors": authors,
        "abstract": summary_el.text.strip().replace("\n", " ") if summary_el is not None else "",
    }


def _build_prompt(paper: dict) -> str:
    """Build the 5-section analysis prompt."""
    authors_str = ", ".join(paper.get("authors", [])[:5])
    if len(paper.get("authors", [])) > 5:
        authors_str += " et al."

    return f"""아래 논문을 한국어로 깊이 있게 분석해주세요.

Title: {paper.get('title', 'N/A')}
Authors: {authors_str}
URL: {paper.get('url', 'N/A')}
Track: {paper.get('track', 'N/A')}
Abstract: {paper.get('abstract', 'N/A')}

아래 5개 항목으로 분석해주세요:

📋 **Problem Definition**: 어떤 문제를 해결하려고 했는지 (2-3문장)

📚 **Background / Related Works**: 관련된 작업이나 선행작업에는 뭐가 있는지 (2-3문장, 구체적 논문명 포함)

🔬 **Main Methodology**: 핵심 방법론 및 기여 (3-5문장, 기술적으로 정확하게)

🧪 **Evaluation**: 어떤 setting에서 어떻게 evaluation을 했고 결과가 어땠는지 (2-3문장, 구체적 수치 포함)

💡 **Key Intuition & Lesson**: 이 논문에서 얻을 수 있는 핵심 인사이트 및 교훈 (2-3문장)

주의사항:
- 반드시 한국어로 작성
- 피상적이지 않게, 구체적인 방법론과 수치를 포함해서 작성
- 논문의 핵심 아이디어를 정확히 전달"""


def _analyze_via_api(prompt: str) -> str:
    """Analyze using Anthropic API (requires ANTHROPIC_API_KEY)."""
    import anthropic
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=config.ANALYSIS_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _analyze_via_cli(prompt: str) -> str:
    """Analyze using Claude Code CLI (uses Pro/Pro Max subscription)."""
    claude_path = shutil.which("claude")
    if not claude_path:
        raise RuntimeError(
            "claude CLI not found. Install Claude Code or set ANTHROPIC_API_KEY."
        )

    result = subprocess.run(
        [claude_path, "-p", prompt, "--output-format", "text"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {result.stderr[:200]}")
    return result.stdout.strip()


def analyze_paper(paper: dict) -> str:
    """Generate deep 5-section Korean analysis for a single paper.

    Routing:
      - ANTHROPIC_API_KEY set → Anthropic API (pay-per-token)
      - ANTHROPIC_API_KEY empty → Claude Code CLI (Pro/Pro Max subscription)
    """
    # Fetch metadata if missing (track pool papers only have arxiv_id)
    if not paper.get("abstract") or paper.get("source") == "track_pool":
        print(f"  Fetching metadata for {paper['id']}...")
        meta = fetch_paper_metadata(paper["id"])
        if meta:
            paper["title"] = meta.get("title", paper.get("title", ""))
            paper["authors"] = meta.get("authors", paper.get("authors", []))
            paper["abstract"] = meta.get("abstract", paper.get("abstract", ""))

    prompt = _build_prompt(paper)
    use_api = bool(config.ANTHROPIC_API_KEY)

    try:
        if use_api:
            print(f"  Using Anthropic API ({config.CLAUDE_MODEL})")
            return _analyze_via_api(prompt)
        else:
            print(f"  Using Claude Code CLI (subscription)")
            return _analyze_via_cli(prompt)
    except Exception as e:
        print(f"  [ERROR] Analysis failed for {paper.get('title', paper['id'])}: {e}")
        return ""
