from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, List, Set

Resolver = Callable[[List[str]], Any]


class Node:
    def eval(self, resolve: Resolver, tags: Set[str], functions, operators) -> Any:
        raise NotImplementedError()


@dataclass
class Literal(Node):
    value: Any

    def eval(self, resolve, tags, functions, operators):
        return self.value


@dataclass
class Name(Node):
    parts: List[str]  # e.g., ["house","light","on"] or ["car"]

    def eval(self, resolve, tags, functions, operators):
        if len(self.parts) == 1:
            name = self.parts[0]
            val = resolve(self.parts)
            # If missing policy returns None and tag is present, treat as True
            if val is None and name in tags:
                return True
            return val
        else:
            return resolve(self.parts)


@dataclass
class Unary(Node):
    op: str
    right: Node

    def eval(self, resolve, tags, functions, operators):
        v = self.right.eval(resolve, tags, functions, operators)
        if self.op == "NOT":
            return not bool(v)
        raise ValueError(f"Unknown unary op {self.op}")


@dataclass
class Binary(Node):
    left: Node
    op: str
    right: Node

    def eval(self, resolve, tags, functions, operators):
        left_val = self.left.eval(resolve, tags, functions, operators)
        right_val = self.right.eval(resolve, tags, functions, operators)
        return operators.evaluate(self.op, left_val, right_val)


@dataclass
class Call(Node):
    name: str
    args: List[Node]

    def eval(self, resolve, tags, functions, operators):
        fn = functions.get(self.name)
        vals = [a.eval(resolve, tags, functions, operators) for a in self.args]
        return fn(*vals)
