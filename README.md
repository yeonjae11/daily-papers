# 🤖 Daily AI/LLM Paper Briefing

AI/LLM 관련 논문을 매일 자동으로 검색하고 한국어로 깊이 있게 분석합니다.

## 🎯 트랙 구조

| Track | 이름 | 범위 |
|-------|------|------|
| 1 | ML Systems | training/serving systems, scheduling, parallelism, goodput, runtime |
| 2 | LLM Post-training | instruction tuning, RLHF, DPO/GRPO, reward modeling, alignment |
| 3 | RL for LLMs / Reasoning | reasoning RL, process reward, CoT efficiency, adaptive compute |
| 4 | Agents | tool use, multi-agent, planning, browser/computer-use, evaluation |
| 5 | Efficient LLM / Inference / Long Context | speculative decoding, KV cache, quantization, long context, sparsity |

## 🏢 모니터링 기관 (가중치 부여)

OpenAI, Anthropic, Meta, NVIDIA, Together AI, Google DeepMind, Apple, ByteDance, Microsoft, DeepSeek, Alibaba, Tencent, UC Berkeley, Stanford, MIT, CMU

## ⚙️ 운영 방식

- **매일 2편**: Fresh arXiv 1편 (14일 이내) + Track Pool 1편 (round-robin)
- **분석 형식**: Problem / Background / Methodology / Evaluation / Key Intuition
- **Slack 전송**: KST 08:00 자동 전송 (채널 또는 DM)
- **중복 방지**: 2-layer dedup (fresh_db + archive_db)
- **Track Pool**: 20개 Awesome repo + DBLP 컨퍼런스(MLSys/ASPLOS/MICRO)에서 자동 크롤링
- **분석 소스**: arXiv HTML 본문 전체 + Figure 1 이미지 추출

---

## 🚀 설치 및 설정

### 1. 레포 클론

```bash
git clone https://github.com/minseo25/daily-ai-llm-papers.git
cd daily-ai-llm-papers
```

### 2. uv 환경 설정

[uv](https://docs.astral.sh/uv/)를 사용하는 경우:

```bash
# uv 설치 (없는 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 가상환경 생성 + 의존성 설치
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

기존 pip을 사용하는 경우:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Slack Bot 연결

1. https://api.slack.com/apps 접속 → **Create New App** → **From scratch**
2. App 이름 지정 (예: `Daily Papers Bot`), Workspace 선택
3. **OAuth & Permissions** 메뉴로 이동
4. **Bot Token Scopes**에 아래 권한 추가:
   - `chat:write` — 메시지 전송
   - `files:write` — Figure 이미지 업로드
5. 상단 **Install to Workspace** 클릭 → **Bot User OAuth Token** 복사 (`xoxb-...`)
6. 전송할 Slack **채널 ID** 확인:
   - 채널 링크의 `/archives/C...` 부분 (예: `C0ANP5PD95X`)

### 4. Claude 분석 모드 선택

논문 분석에 Claude를 사용합니다. **두 가지 모드** 중 하나를 선택하세요:

| 모드 | 대상 | 설정 방법 | 비용 |
|------|------|-----------|------|
| **Claude Code CLI** | Pro / Pro Max 구독자 | `ANTHROPIC_API_KEY`를 비워두기 | 월정액에 포함 |
| **Anthropic API** | API 사용자 | `ANTHROPIC_API_KEY` 설정 | 토큰당 과금 (~$0.03/일) |

- **Pro Max 구독자**: `ANTHROPIC_API_KEY`를 비워두면 자동으로 `claude` CLI를 사용합니다. Claude Code가 설치되어 있어야 합니다.
- **API 사용자**: https://console.anthropic.com 에서 API key를 발급받아 설정하세요.

### 5. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열고 아래 값을 채워주세요:

```env
SLACK_BOT_TOKEN=xoxb-여기에-봇-토큰-붙여넣기
SLACK_CHANNEL=C여기에-채널-ID
ANTHROPIC_API_KEY=                       # 비워두면 Claude CLI 사용 (Pro Max)
GITHUB_TOKEN=ghp_여기에-깃헙-토큰       # 선택사항 (rate limit 완화)
```

| 변수 | 필수 | 설명 |
|------|------|------|
| `SLACK_BOT_TOKEN` | O | Slack Bot OAuth Token |
| `SLACK_CHANNEL` | O | 채널 ID (`C...`) → 채널 전송, 본인 Member ID (`U...`) → DM 전송 |
| `ANTHROPIC_API_KEY` | △ | Anthropic API Key. 비워두면 Claude CLI 사용 (Pro/Pro Max 구독 필요) |
| `GITHUB_TOKEN` | X | GitHub Personal Access Token (크롤링 rate limit 완화) |

### 6. 첫 실행

```bash
source .venv/bin/activate

# 1) Track Pool 구축 (Awesome repo 크롤링) + 테스트 실행
set -a && source .env && set +a && python3 daily_briefing.py --crawl --dry-run

# 2) 결과 확인 후 실제 실행 (Slack 전송 + Git push)
set -a && source .env && set +a && python3 daily_briefing.py
```

| 플래그 | 설명 |
|--------|------|
| `--crawl` | Awesome repo 강제 크롤링 (보통 7일마다 자동 실행) |
| `--dry-run` | Slack 전송 / Git push 없이 분석 결과만 stdout 출력 |
| `--no-git` | Slack 전송 + 파일 저장만 하고 git commit/push 건너뛰기 |
| (없음) | 정상 실행 |

### 7. Crontab 등록 (자동 실행)

매일 **KST 08:00**에 자동 실행 (서버 타임존이 KST인 경우):

```bash
crontab -e
```

아래 줄 추가 (경로를 본인 환경에 맞게 수정):

```cron
0 8 * * * cd /home/minseokim/daily-ai-llm-papers && bash run.sh
```

macOS에서 cron이 안 되는 경우 **launchd** 사용:

```bash
# ~/Library/LaunchAgents/com.daily-papers.plist 생성
cat > ~/Library/LaunchAgents/com.daily-papers.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.daily-papers</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/yourname/daily-ai-llm-papers/run.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>/Users/yourname/daily-ai-llm-papers</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

# 등록
launchctl load ~/Library/LaunchAgents/com.daily-papers.plist
```

---

## 📁 프로젝트 구조

```
daily-ai-llm-papers/
├── daily_briefing.py      # 메인 오케스트레이터
├── run.sh                 # Cron 실행 스크립트
├── requirements.txt       # Python 의존성
├── .env.example           # 환경 변수 템플릿
├── src/                   # 핵심 모듈
│   ├── config.py          #   트랙/키워드/기관 설정
│   ├── arxiv_search.py    #   arXiv API 검색
│   ├── scoring.py         #   논문 점수 산정
│   ├── crawler.py         #   Awesome repo 크롤러
│   ├── dedup.py           #   2-layer 중복 방지
│   ├── selector.py        #   일일 논문 선정 (1 fresh + 1 track)
│   ├── analyzer.py        #   Claude 5항목 깊이 분석
│   ├── slack_sender.py    #   Slack 전송 (채널/DM + Figure 업로드)
│   └── github_archive.py  #   마크다운 저장 + README + Git push
├── tests/                 # 유닛 테스트
│   ├── test_scoring.py    #   스코어링 테스트
│   └── test_selector.py   #   선정 로직 테스트
├── papers_db/             # 데이터
│   ├── fresh_db.json      #   30일 rolling dedup DB
│   ├── archive_db.json    #   영구 dedup DB
│   └── track_pool.json    #   Awesome repo 논문 풀
└── YYYY/MM/YYYY-MM-DD.md  # 일일 브리핑 아카이브
```

<!-- AUTO-GENERATED BELOW -->
