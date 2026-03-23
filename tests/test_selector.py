"""Unit tests for paper selection and round-robin logic."""

import datetime
import os
import tempfile
import unittest

from src.dedup import FreshDB, ArchiveDB
from src.selector import select_daily_papers, _get_track_index
from src import config


class TestRoundRobin(unittest.TestCase):

    def test_track_index_varies_by_date(self):
        """Round-robin selects different tracks for different dates."""
        indices = set()
        for day in range(1, 11):
            date = datetime.date(2026, 3, day)
            indices.add(_get_track_index(date))
        self.assertEqual(len(indices), 5, "Should hit all 5 tracks within 10 days")

    def test_track_index_range(self):
        """Track index is always 0-4."""
        for day in range(1, 366):
            date = datetime.date(2026, 1, 1) + datetime.timedelta(days=day - 1)
            idx = _get_track_index(date)
            self.assertGreaterEqual(idx, 0)
            self.assertLessEqual(idx, 4)


class TestSelectDailyPapers(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.fresh_db = FreshDB(os.path.join(self.tmpdir, "fresh.json"))
        self.archive_db = ArchiveDB(os.path.join(self.tmpdir, "archive.json"))
        # Build a mock track pool with papers for each track
        self.track_pool = {}
        for i, track in enumerate(config.TRACKS):
            self.track_pool[track["name"]] = [
                {"arxiv_id": f"2501.{10000 + i * 100 + j:05d}", "source_repo": "test/repo"}
                for j in range(10)
            ]

    def test_returns_exactly_2_papers(self):
        """Always returns exactly 2 papers."""
        date = datetime.date(2026, 3, 23)
        fresh_papers = [{
            "id": "2603.99999",
            "title": "Test Fresh Paper",
            "authors": ["Author"],
            "abstract": "Test abstract about llm serving.",
            "url": "https://arxiv.org/abs/2603.99999",
            "score": 10.0,
            "track": "ML Systems",
        }]
        result = select_daily_papers(date, self.fresh_db, self.archive_db, self.track_pool, fresh_papers)
        self.assertEqual(len(result), 2)

    def test_dedup_prevents_repeat(self):
        """Papers already in archive_db are not selected."""
        date = datetime.date(2026, 3, 23)
        track_idx = _get_track_index(date)
        track_name = config.TRACKS[track_idx]["name"]

        # Mark first 5 papers as already briefed
        for j in range(5):
            aid = f"2501.{10000 + track_idx * 100 + j:05d}"
            self.archive_db.add(aid, {"title": "old", "track": track_name})

        fresh_papers = [{
            "id": "2603.88888",
            "title": "Fresh",
            "authors": [],
            "abstract": "",
            "url": "https://arxiv.org/abs/2603.88888",
            "score": 5.0,
            "track": "ML Systems",
        }]
        result = select_daily_papers(date, self.fresh_db, self.archive_db, self.track_pool, fresh_papers)
        self.assertEqual(len(result), 2)
        # Track paper should not be any of the first 5
        track_paper = result[1]
        for j in range(5):
            self.assertNotEqual(track_paper["id"], f"2501.{10000 + track_idx * 100 + j:05d}")

    def test_fallback_to_2_track_papers(self):
        """When no fresh papers, selects 2 track papers from different tracks."""
        date = datetime.date(2026, 3, 23)
        result = select_daily_papers(date, self.fresh_db, self.archive_db, self.track_pool, [])
        self.assertEqual(len(result), 2)
        # Both should be from track pool
        self.assertEqual(result[0].get("source"), "track_pool")
        self.assertEqual(result[1].get("source"), "track_pool")

    def test_fallback_different_tracks(self):
        """When 2 track papers needed, they come from different tracks."""
        date = datetime.date(2026, 3, 23)
        result = select_daily_papers(date, self.fresh_db, self.archive_db, self.track_pool, [])
        self.assertEqual(len(result), 2)
        # Should be from different tracks
        self.assertNotEqual(result[0]["track"], result[1]["track"])

    def test_pool_exhaustion_falls_through(self):
        """When current track is empty, falls through to next track."""
        date = datetime.date(2026, 3, 23)
        track_idx = _get_track_index(date)
        track_name = config.TRACKS[track_idx]["name"]

        # Empty the current track's pool
        self.track_pool[track_name] = []

        fresh_papers = [{
            "id": "2603.77777",
            "title": "Fresh",
            "authors": [],
            "abstract": "",
            "url": "https://arxiv.org/abs/2603.77777",
            "score": 5.0,
            "track": "ML Systems",
        }]
        result = select_daily_papers(date, self.fresh_db, self.archive_db, self.track_pool, fresh_papers)
        self.assertEqual(len(result), 2)
        # Track paper should come from a different track
        self.assertNotEqual(result[1]["track"], track_name)


if __name__ == "__main__":
    unittest.main()
