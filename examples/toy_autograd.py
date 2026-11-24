"""Demonstrate reverse-mode automatic differentiation with scalar values."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable


@dataclass(eq=False)
class Value:
    data: float
    label: str = ""
    grad: float = 0.0
    _parents: tuple["Value", ...] = field(default_factory=tuple, repr=False)
    _backward: Callable[[], None] = field(default=lambda: None, repr=False)

    def __add__(self, other: "Value | float") -> "Value":
        right = other if isinstance(other, Value) else Value(float(other))
        result = Value(self.data + right.data, _parents=(self, right))

        def backward() -> None:
            self.grad += result.grad
            right.grad += result.grad

        result._backward = backward
        return result

    def __mul__(self, other: "Value | float") -> "Value":
        right = other if isinstance(other, Value) else Value(float(other))
        result = Value(self.data * right.data, _parents=(self, right))

        def backward() -> None:
            self.grad += right.data * result.grad
            right.grad += self.data * result.grad

        result._backward = backward
        return result

    def __pow__(self, exponent: float) -> "Value":
        result = Value(self.data**exponent, _parents=(self,))

        def backward() -> None:
            self.grad += exponent * self.data ** (exponent - 1) * result.grad

        result._backward = backward
        return result

    def backward(self) -> None:
        order: list[Value] = []
        visited: set[Value] = set()

        def visit(node: Value) -> None:
            if node in visited:
                return
            visited.add(node)
            for parent in node._parents:
                visit(parent)
            order.append(node)

        visit(self)
        self.grad = 1.0
        for node in reversed(order):
            node._backward()


def run_demo() -> dict:
    x = Value(2.0, "x")
    weight = Value(3.0, "weight")
    bias = Value(1.0, "bias")
    prediction = x * weight + bias
    loss = prediction**2
    loss.backward()
    return {
        "expression": "loss = (x * weight + bias) ** 2",
        "inputs": {"x": x.data, "weight": weight.data, "bias": bias.data},
        "prediction": prediction.data,
        "loss": loss.data,
        "gradients": {"x": x.grad, "weight": weight.grad, "bias": bias.grad},
    }


if __name__ == "__main__":
    print(json.dumps(run_demo(), ensure_ascii=False, indent=2))
