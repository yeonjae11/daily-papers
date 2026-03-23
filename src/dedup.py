"""2-layer deduplication: FreshDB (30-day rolling) + ArchiveDB (permanent)."""

import json
import os
import re
import datetime


def normalize_arxiv_id(arxiv_id: str) -> str:
    """Strip version suffix (e.g., '2603.15381v1' -> '2603.15381')."""
    return re.sub(r"v\d+$", "", arxiv_id.strip())


class FreshDB:
    """30-day rolling DB for arXiv real-time collection dedup."""

    def __init__(self, path: str):
        self.path = path
        self.data: dict = {}
        self.load()

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {}
        self._prune()

    def _prune(self):
        cutoff = (
            datetime.date.today()
            - datetime.timedelta(days=30)
        ).isoformat()
        self.data = {
            k: v for k, v in self.data.items()
            if v.get("date", "9999") >= cutoff
        }

    def contains(self, arxiv_id: str) -> bool:
        return normalize_arxiv_id(arxiv_id) in self.data

    def add(self, arxiv_id: str, metadata: dict):
        nid = normalize_arxiv_id(arxiv_id)
        if "date" not in metadata:
            metadata["date"] = datetime.date.today().isoformat()
        self.data[nid] = metadata

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)


class ArchiveDB:
    """Permanent DB for track papers already briefed. Never prunes."""

    def __init__(self, path: str):
        self.path = path
        self.data: dict = {}
        self.load()

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {}

    def contains(self, arxiv_id: str) -> bool:
        return normalize_arxiv_id(arxiv_id) in self.data

    def add(self, arxiv_id: str, metadata: dict):
        nid = normalize_arxiv_id(arxiv_id)
        if "date_briefed" not in metadata:
            metadata["date_briefed"] = datetime.date.today().isoformat()
        self.data[nid] = metadata

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
