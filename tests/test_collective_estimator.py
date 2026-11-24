import unittest

from examples.collective_estimator import estimate


class CollectiveEstimatorTest(unittest.TestCase):
    def test_ring_all_reduce(self):
        report = estimate("all-reduce", 8, 4, 400)
        self.assertEqual(report["ideal_traffic_factor_per_device"], 1.75)
        self.assertEqual(report["ideal_traffic_gib_per_device"], 7.0)
        self.assertAlmostEqual(report["ideal_bandwidth_time_ms"], 18.79048192)

    def test_all_gather_and_reduce_scatter(self):
        gather = estimate("all-gather", 8, 4, 400)
        scatter = estimate("reduce-scatter", 8, 4, 400)
        self.assertEqual(gather["ideal_traffic_gib_per_device"], 3.5)
        self.assertEqual(scatter["ideal_traffic_gib_per_device"], 3.5)
        self.assertEqual(gather["ideal_bandwidth_time_ms"], scatter["ideal_bandwidth_time_ms"])

    def test_too_few_devices_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least 2"):
            estimate("all-reduce", 1, 4, 400)


if __name__ == "__main__":
    unittest.main()
