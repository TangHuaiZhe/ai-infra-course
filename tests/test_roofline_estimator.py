import unittest

from examples.roofline_estimator import estimate


class RooflineEstimatorTest(unittest.TestCase):
    def test_default_teaching_configuration(self):
        report = estimate(1, 100, 100, 2000, 14, 64)
        self.assertEqual(report["arithmetic_intensity_flop_per_byte"], 10.0)
        self.assertEqual(report["ridge_point_flop_per_byte"], 50.0)
        self.assertEqual(report["ideal_compute_time_ms"], 10.0)
        self.assertEqual(report["ideal_memory_time_ms"], 50.0)
        self.assertEqual(report["roofline_lower_bound_ms"], 50.0)
        self.assertEqual(report["roofline_ceiling_tflops"], 20.0)
        self.assertEqual(report["roofline_region"], "memory-bound")
        self.assertEqual(report["ideal_host_device_transfer_ms"], 218.75)

    def test_compute_bound_configuration(self):
        report = estimate(10, 10, 100, 2000, 1, 64)
        self.assertEqual(report["roofline_region"], "compute-bound")
        self.assertEqual(report["roofline_ceiling_tflops"], 100.0)
        self.assertEqual(report["roofline_lower_bound_ms"], 100.0)

    def test_nonfinite_value_rejected(self):
        with self.assertRaisesRegex(ValueError, "positive and finite"):
            estimate(float("inf"), 100, 100, 2000, 14, 64)


if __name__ == "__main__":
    unittest.main()
