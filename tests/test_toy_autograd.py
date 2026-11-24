import unittest

from examples.toy_autograd import Value, run_demo


class ToyAutogradTest(unittest.TestCase):
    def test_demo_gradients(self):
        report = run_demo()
        self.assertEqual(report["prediction"], 7.0)
        self.assertEqual(report["loss"], 49.0)
        self.assertEqual(report["gradients"], {"x": 42.0, "weight": 28.0, "bias": 14.0})

    def test_shared_value_accumulates_gradient(self):
        value = Value(3.0)
        result = value * value + value
        result.backward()
        self.assertEqual(result.data, 12.0)
        self.assertEqual(value.grad, 7.0)


if __name__ == "__main__":
    unittest.main()
