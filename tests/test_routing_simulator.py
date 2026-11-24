import tempfile
import unittest
from pathlib import Path

from examples.routing_simulator import load_requests, parse_failure, simulate


class RoutingSimulatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.requests = load_requests(
            Path(__file__).resolve().parents[1] / "examples/routing_trace.csv"
        )

    def run_policy(self, policy, failures=None):
        return simulate(
            self.requests,
            policy,
            replica_count=2,
            cache_saving_ms=80,
            max_affinity_wait_ms=100,
            failures=failures or [],
        )

    def test_prefix_affinity_changes_routing_and_cache_hits(self):
        least_queue = self.run_policy("least-queue")
        affinity = self.run_policy("prefix-affinity")
        self.assertGreater(affinity["cache_hits"], least_queue["cache_hits"])
        self.assertNotEqual(affinity["assignments"], least_queue["assignments"])

    def test_unready_replica_receives_no_new_request(self):
        report = self.run_policy("prefix-affinity", [("replica-0", 300, 500)])
        request = next(item for item in report["assignments"] if item["request_id"] == "r7")
        self.assertEqual(request["replica"], "replica-1")
        self.assertEqual(report["rejected"], 0)

    def test_all_replicas_unready_rejects_request(self):
        failures = [("replica-0", 300, 500), ("replica-1", 300, 500)]
        report = self.run_policy("least-queue", failures)
        self.assertEqual(report["rejected"], 2)

    def test_bad_trace_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_text(
                "request_id,arrival_ms,prefix,service_ms\n"
                "a,10,x,20\n"
                "b,5,y,20\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "line 3"):
                load_requests(path)

    def test_failure_parser(self):
        self.assertEqual(parse_failure("replica-0:300:500"), ("replica-0", 300.0, 500.0))


if __name__ == "__main__":
    unittest.main()
