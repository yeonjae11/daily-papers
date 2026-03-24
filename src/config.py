"""Configuration for Daily AI/LLM Paper Briefing System."""

import os

# ── Environment ──────────────────────────────────────────────────
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Model ────────────────────────────────────────────────────────
CLAUDE_MODEL = "claude-sonnet-4-20250514"
ANALYSIS_MAX_TOKENS = 3000

# ── Paths ────────────────────────────────────────────────────────
FRESH_DB_PATH = os.path.join(REPO_DIR, "papers_db", "fresh_db.json")
ARCHIVE_DB_PATH = os.path.join(REPO_DIR, "papers_db", "archive_db.json")
TRACK_POOL_PATH = os.path.join(REPO_DIR, "papers_db", "track_pool.json")

# ── Tracks ───────────────────────────────────────────────────────
TRACKS = [
    {
        "name": "ML Systems",
        "positive_keywords": [
            "llm systems", "llm serving", "language model serving",
            "inference system", "serving system", "continuous batching",
            "goodput", "scheduler", "prefill", "decoding",
            "prefill disaggregation", "disaggregated serving",
            "memory management", "kv cache", "cache management",
            "parallelism", "tensor parallelism", "pipeline parallelism",
            "expert parallelism", "context parallelism",
            "communication-efficient training", "distributed training",
            "fault tolerance", "runtime", "cluster scheduling",
            "multi-tenant serving", "system-algorithm co-design",
        ],
        "awesome_repos": [
            "Hsword/Awesome-Machine-Learning-System-Papers",
            "AmberLJC/LLMSys-PaperList",
            "AmadeusChan/Awesome-LLM-System-Papers",
            "Shenggan/awesome-distributed-ml",
            "PDZZXL/Awesome-LLM-Serving",
        ],
        "conferences": [
            {"dblp_venue": "conf/mlsys", "years": [2025, 2026]},
            {"dblp_venue": "conf/asplos", "years": [2025, 2026]},
            {"dblp_venue": "conf/micro", "years": [2025, 2026]},
        ],
        "ml_filter": True,
    },
    {
        "name": "LLM Post-training",
        "positive_keywords": [
            "post-training", "instruction tuning", "supervised fine-tuning",
            "alignment", "preference optimization", "dpo", "grpo", "ppo",
            "rlhf", "rlaif", "reward model", "process reward",
            "verifiable reward", "online rl", "offline rl",
            "self-improvement", "reasoning model", "test-time scaling",
            "reasoning adaptation",
        ],
        "awesome_repos": [
            "mbzuai-oryx/Awesome-LLM-Post-training",
            "xiyuanhao/Awesome-LLM-Post-training-Papers",
            "GaryYufei/AlignLLMHumanSurvey",
            "icip-cas/awesome-auto-alignment",
        ],
    },
    {
        "name": "RL for LLMs / Reasoning",
        "min_yymm": 2501,
        "positive_keywords": [
            "rl for reasoning", "reasoning llm", "reasoning optimization",
            "length reward", "adaptive reasoning", "short cot",
            "efficient cot", "process supervision", "outcome reward",
            "reasoning compression", "latent reasoning", "dynamic reasoning",
            "deliberation budget", "compute-aware reasoning",
            "inference-time scaling", "test-time compute", "test-time scaling",
            "inference-time compute", "scaling compute at inference",
        ],
        "awesome_repos": [
            "TsinghuaC3I/Awesome-RL-for-LRMs",
            "opendilab/awesome-RLHF",
            "Eclipsess/Awesome-Efficient-Reasoning-LLMs",
            "Junting-Lu/Awesome-LLM-Reasoning-Techniques",
            "ThreeSR/Awesome-Inference-Time-Scaling",
        ],
    },
    {
        "name": "Agents",
        "positive_keywords": [
            "ai agent", "llm agent", "agent workflow", "tool use",
            "tool learning", "function calling", "browser agent",
            "web agent", "computer use", "agent memory", "planning",
            "multi-agent", "agent benchmark", "agent evaluation",
            "observability", "agent security", "agent environment",
            "autonomous agent",
        ],
        "awesome_repos": [
            "VoltAgent/awesome-ai-agent-papers",
            "luo-junyu/Awesome-Agent-Papers",
            "l-aime/awesome-agents",
            "kyegomez/awesome-multi-agent-papers",
        ],
    },
    {
        "name": "Efficient LLM / Inference / Long Context",
        "min_yymm": 2501,
        "positive_keywords": [
            "efficient llm", "llm inference", "speculative decoding",
            "early exit", "token pruning", "layer skipping",
            "quantization", "sparsity", "moe routing",
            "cache compression", "kv cache compression",
            "context compression", "long context", "length extrapolation",
            "retrieval augmented generation", "long cot",
            "efficient transformer", "memory efficient attention",
        ],
        "awesome_repos": [
            "xlite-dev/Awesome-LLM-Inference",
            "HuangOwen/Awesome-LLM-Compression",
            "Xnhyacinth/Awesome-LLM-Long-Context-Modeling",
            "horseee/Awesome-Efficient-LLM",
        ],
    },
    {
        "name": "Diffusion Language Models",
        "min_yymm": 2506,
        "positive_keywords": [
            "diffusion language model", "discrete diffusion",
            "masked diffusion", "continuous diffusion language",
            "non-autoregressive generation", "non-autoregressive language",
            "efficient dllm", "efficient diffusion llm",
            "denoising language model", "text diffusion",
            "language diffusion", "diffusion lm",
            "mdlm", "sedd", "dream", "mercury",
        ],
        "awesome_repos": [
            "FelixMessi/Awesome-Efficient-dLLMs",
            "VILA-Lab/Awesome-DLMs",
        ],
    },
]

# ── Core Keywords (binary presence check for exclusion override) ─
CORE_KEYWORDS = [
    "llm", "language model", "large model", "foundation model",
    "reasoning model", "agent", "tool use", "multi-agent",
    "serving", "inference", "kv cache", "parallelism",
    "scheduler", "runtime", "post-training", "alignment",
    "preference optimization", "rlhf", "long context",
    "compression", "speculative decoding", "quantization",
]

# ── Org Boost (additive weight, NOT a filter) ────────────────────
ORG_BOOST = [
    "openai", "anthropic", "meta", "nvidia", "together ai",
    "google deepmind", "deepmind", "google", "apple", "bytedance",
    "microsoft", "deepseek", "alibaba", "tencent",
    "uc berkeley", "berkeley", "stanford", "mit", "cmu",
]
ORG_BOOST_SCORE = 3.0

# ── Exclusion Keywords ───────────────────────────────────────────
EXCLUDE_HARD = [
    "biology", "biological", "bioinformatics", "genomics", "genomic",
    "protein", "proteins", "molecule", "molecular", "drug",
    "drug discovery", "chemistry", "chemical", "materials",
    "material science", "battery", "medical", "medicine", "clinical",
    "healthcare", "ehr", "radiology", "pathology", "diagnosis",
    "omics", "neuroscience", "eeg", "ecg",
    "finance", "financial", "stock", "trading", "economics",
    "legal", "law", "education", "marketing", "advertising",
    "customer support", "recommendation", "recommender",
    "sentiment", "social media", "survey analysis",
    "robot", "robotics", "embodied", "embodiment",
    "vision-language-action", "vla", "manipulation",
    "navigation", "physical ai", "world model for robotics",
]

EXCLUDE_LOW_PRIORITY = [
    "fpga", "asic", "analog", "photonic", "circuit",
    "silicon", "sram", "noc", "wafer-scale", "hardware accelerator",
]
LOW_PRIORITY_PENALTY = -1.0

# ── Keyword Match Score ──────────────────────────────────────────
KEYWORD_MATCH_SCORE = 2.0

# ── arXiv Categories ─────────────────────────────────────────────
ARXIV_CATEGORIES_MAIN = ["cs.CL", "cs.LG", "cs.AI"]
ARXIV_CATEGORIES_SECONDARY = ["cs.MA", "cs.DC", "cs.SE"]
ARXIV_CATEGORIES = ARXIV_CATEGORIES_MAIN + ARXIV_CATEGORIES_SECONDARY

# ── ML Relevance Keywords (for filtering conference papers) ─────
ML_RELEVANCE_KEYWORDS = [
    "llm", "language model", "transformer", "neural", "deep learning",
    "machine learning", "inference", "training", "gpu", "model serving",
    "attention", "distributed training", "tensor", "batch",
    "fine-tun", "pretrain", "embedding", "token", "accelerat",
    "diffusion", "generative", "foundation model", "large model",
    "kv cache", "speculative", "quantiz", "sparsity", "parallelism",
]

# ── Search Settings ──────────────────────────────────────────────
FRESH_DAYS_BACK = 14
FRESH_DB_RETENTION_DAYS = 30
