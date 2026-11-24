import tempfile
import unittest
from pathlib import Path

from examples.gpu_scheduler_simulator import load_jobs, simulate


class GpuSchedulerSimulatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jobs = load_jobs(Path(__file__).resolve().parents[1] / "examples/gpu_jobs.csv")
        cls.quotas = {"team-a": 4, "team-b": 6, "team-c": 2}

    def run_policy(self, policy, outages=None):
        return simulate(self.jobs, policy, 2, 4, self.quotas, outages or [])

    def test_all_jobs_complete_with_gang_and_quota_constraints(self):
        report = self.run_policy("fifo")
        self.assertEqual(report["completed"], 6)
        self.assertEqual(report["unschedulable"], 0)
        first = next(item for item in report["schedule"] if item["job_id"] == "j1")
        blocked_by_quota = next(item for item in report["schedule"] if item["job_id"] == "j3")
        self.assertGreaterEqual(blocked_by_quota["start_ms"], first["end_ms"])
        same_node = next(item for item in report["schedule"] if item["job_id"] == "j4")
        self.assertEqual(len(same_node["allocation"]), 1)
        self.assertEqual(report["mean_wait_ms"], 125.0)
        self.assertEqual(report["p95_wait_ms"], 400.0)

    def test_priority_changes_waiting_order(self):
        fifo = self.run_policy("fifo")
        priority = self.run_policy("priority")
        fifo_j4 = next(item for item in fifo["schedule"] if item["job_id"] == "j4")
        priority_j4 = next(item for item in priority["schedule"] if item["job_id"] == "j4")
        self.assertEqual(fifo_j4["start_ms"], 500.0)
        self.assertEqual(priority_j4["start_ms"], 400.0)
        self.assertEqual(priority["mean_wait_ms"], 650 / 6)
        self.assertEqual(priority["p95_wait_ms"], 350.0)

    def test_outage_delays_new_placement(self):
        report = self.run_policy("fifo", [("node-1", 250, 700)])
        job = next(item for item in report["schedule"] if item["job_id"] == "j4")
        self.assertEqual(job["start_ms"], 650.0)
        self.assertEqual(report["mean_wait_ms"], 175.0)
        self.assertEqual(report["p95_wait_ms"], 550.0)

    def test_impossible_same_node_job_is_unschedulable(self):
        jobs = [{
            "index": 0,
            "job_id": "large",
            "arrival_ms": 0.0,
            "tenant": "team-a",
            "gpus": 5,
            "duration_ms": 100.0,
            "priority": 1,
            "same_node": True,
        }]
        report = simulate(jobs, "fifo", 2, 4, {"team-a": 8}, [])
        self.assertEqual(report["unschedulable"], 1)

    def test_unordered_arrivals_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_text(
                "job_id,arrival_ms,tenant,gpus,duration_ms,priority,same_node\n"
                "a,10,t,1,20,1,false\n"
                "b,5,t,1,20,1,false\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "line 3"):
                load_jobs(path)


if __name__ == "__main__":
    unittest.main()
