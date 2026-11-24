import unittest

from examples.model_memory_estimator import estimate


class ModelMemoryEstimatorTest(unittest.TestCase):
    def test_default_teaching_configuration(self):
        report = estimate(7, 2, 32, 32, 32, 128, 4, 4096, 2, 2)
        self.assertAlmostEqual(report["weights_gib"], 13.0385160446)
        self.assertEqual(report["kv_cache_gib"], 8.0)
        self.assertEqual(report["attention_scores_gib_per_layer_if_materialized"], 4.0)

    def test_grouped_kv_heads_reduce_estimate(self):
        full = estimate(7, 2, 32, 32, 32, 128, 4, 4096, 2, 2)
        grouped = estimate(7, 2, 32, 32, 8, 128, 4, 4096, 2, 2)
        self.assertEqual(grouped["kv_cache_gib"], full["kv_cache_gib"] / 4)
        self.assertEqual(
            grouped["conceptual_attention_score_elements_per_layer"],
            full["conceptual_attention_score_elements_per_layer"],
        )

    def test_invalid_head_counts_rejected(self):
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            estimate(7, 2, 32, 8, 16, 128, 1, 1024, 2, 2)

    def test_nonfinite_value_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be positive"):
            estimate(float("nan"), 2, 32, 32, 32, 128, 1, 1024, 2, 2)


if __name__ == "__main__":
    unittest.main()
