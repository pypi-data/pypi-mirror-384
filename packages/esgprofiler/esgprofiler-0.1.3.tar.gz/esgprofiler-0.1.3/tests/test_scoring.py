import unittest
from esgprofiler.scoring import aggregate_esg_counts, compute_overall_esg_score, score_esg_text

EXAMPLE_TEXT = """
The company invested heavily in renewable energy and reduced carbon emissions.
Diversity and inclusion programs were expanded, improving employee well-being.
The board demonstrated transparency and anti-corruption policies in all operations.
"""

class TestESGScoring(unittest.TestCase):
    def test_aggregate_esg_counts(self):
        counts = {"environment": 4, "social": 3, "governance": 3}
        subscores = aggregate_esg_counts(counts)
        self.assertTrue(0 <= subscores["environment_score"] <= 100)
        self.assertTrue(0 <= subscores["social_score"] <= 100)
        self.assertTrue(0 <= subscores["governance_score"] <= 100)

    def test_overall_score(self):
        subscores = {"environment_score": 60, "social_score": 50, "governance_score": 30}
        overall = compute_overall_esg_score(subscores, weights=(0.4, 0.4, 0.2))
        self.assertIsInstance(overall, float)
        self.assertTrue(0.0 <= overall <= 100.0)

    def test_score_esg_text(self):
        results = score_esg_text(EXAMPLE_TEXT)
        self.assertIn("environment_score", results)
        self.assertIn("social_score", results)
        self.assertIn("governance_score", results)
        self.assertIn("overall_score", results)
        self.assertIsInstance(results["overall_score"], float)

if __name__ == "__main__":
    unittest.main()
