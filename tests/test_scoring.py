"""Unit tests for scoring logic."""

import unittest
from src import config
from src.scoring import score_paper


class TestScoring(unittest.TestCase):

    def test_medical_llm_serving_not_excluded(self):
        """medical + llm serving → NOT excluded (core keyword 'llm' present)."""
        paper = {
            "title": "Medical LLM Serving Optimization",
            "abstract": "We optimize llm serving for medical applications.",
            "categories": ["cs.CL"],
            "affiliation_text": "",
        }
        score, track = score_paper(paper)
        self.assertGreaterEqual(score, 0, "Paper with core keyword 'llm' should not be excluded")

    def test_protein_folding_excluded(self):
        """protein folding → excluded (no core keyword)."""
        paper = {
            "title": "Protein Folding Prediction with Transformers",
            "abstract": "We predict protein folding structures using deep learning.",
            "categories": ["cs.LG"],
            "affiliation_text": "",
        }
        score, track = score_paper(paper)
        self.assertLess(score, 0, "Paper without core keyword should be excluded")

    def test_medical_imaging_excluded(self):
        """medical imaging classification → excluded (no core keyword)."""
        paper = {
            "title": "Medical Imaging Classification",
            "abstract": "A neural network for medical image diagnosis.",
            "categories": ["cs.CV"],
            "affiliation_text": "",
        }
        score, track = score_paper(paper)
        self.assertLess(score, 0, "Medical paper without core keyword should be excluded")

    def test_kv_cache_compression_track5(self):
        """efficient kv cache compression for llm → Track 5, high score."""
        paper = {
            "title": "Efficient KV Cache Compression for LLM Inference",
            "abstract": "We propose kv cache compression and quantization for long context llm inference.",
            "categories": ["cs.CL"],
            "affiliation_text": "",
        }
        score, track = score_paper(paper)
        self.assertGreater(score, 0)
        self.assertEqual(track, "Efficient LLM / Inference / Long Context")

    def test_org_boost_adds_score(self):
        """Org boost adds exactly ORG_BOOST_SCORE when org is present."""
        paper_with_org = {
            "title": "Speculative Decoding for LLM",
            "abstract": "A new approach to speculative decoding.",
            "categories": ["cs.CL"],
            "affiliation_text": "researchers at deepmind propose a new method",
        }
        paper_without_org = {
            "title": "Speculative Decoding for LLM",
            "abstract": "A new approach to speculative decoding.",
            "categories": ["cs.CL"],
            "affiliation_text": "researchers at unknown lab propose a new method",
        }
        score_with, _ = score_paper(paper_with_org)
        score_without, _ = score_paper(paper_without_org)
        self.assertAlmostEqual(
            score_with - score_without, config.ORG_BOOST_SCORE,
            msg="Org boost should add exactly ORG_BOOST_SCORE",
        )

    def test_cs_lg_without_core_keyword_filtered(self):
        """cs.LG paper about 'neural scaling' without LLM keyword gets filtered."""
        paper = {
            "title": "Neural Scaling Laws in Deep Networks",
            "abstract": "We study scaling behavior of deep networks on vision tasks.",
            "categories": ["cs.LG"],
            "affiliation_text": "",
        }
        score, track = score_paper(paper)
        self.assertLess(score, 0, "cs.LG paper without core keyword should be filtered")


if __name__ == "__main__":
    unittest.main()
