import tempfile
import unittest
from pathlib import Path

from examples.inference_metrics import load_trace, percentile, summarize


class MetricsTest(unittest.TestCase):
    def test_sample_trace_and_slo(self):
        rows = load_trace(Path(__file__).resolve().parents[1] / "examples/sample_trace.csv")
        report = summarize(rows, 500, 200, 2000)
        self.assertEqual(report["ttft_ms_p50"], 200)
        self.assertEqual(report["ttft_ms_p95"], 600)
        self.assertEqual(report["tpot_ms_p50"], 100)
        self.assertEqual(report["good_requests"], 4)
        self.assertEqual(report["tpot_defined_requests"], 4)
        self.assertAlmostEqual(report["good_requests_per_s"], 4 / 1.7)

    def test_bad_trace_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_text("request_id,arrival_ms,first_token_ms,end_ms,output_tokens\na,0,20,10,2\n")
            with self.assertRaisesRegex(ValueError, "line 2"):
                load_trace(path)

    def test_nearest_rank(self):
        self.assertEqual(percentile([1, 2, 3, 4, 5], 0.95), 5)


if __name__ == "__main__":
    unittest.main()
