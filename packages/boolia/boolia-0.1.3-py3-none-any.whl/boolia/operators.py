from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Tuple


BinaryFunc = Callable[[Any, Any], Any]


@dataclass(frozen=True)
class BinaryOperator:
    token: str
    precedence: int
    evaluator: BinaryFunc
    keywords: Tuple[str, ...]
    symbols: Tuple[str, ...]

    def with_bindings(self, *, keywords: Iterable[str], symbols: Iterable[str]) -> "BinaryOperator":
        return BinaryOperator(
            token=self.token,
            precedence=self.precedence,
            evaluator=self.evaluator,
            keywords=tuple(keywords),
            symbols=tuple(symbols),
        )


class OperatorRegistry:
    def __init__(self) -> None:
        self._operators: Dict[str, BinaryOperator] = {}
        self._keyword_map: Dict[str, str] = {}
        self._symbol_map: Dict[str, str] = {}

    def register(
        self,
        token: str,
        *,
        precedence: int,
        evaluator: BinaryFunc,
        keywords: Iterable[str] | None = None,
        symbols: Iterable[str] | None = None,
    ) -> None:
        token = token.upper()
        kws = tuple(k.lower() for k in (keywords or ()))
        syms = tuple(symbols or ())
        op = BinaryOperator(token, precedence, evaluator, kws, syms)
        self._operators[token] = op
        for kw in kws:
            self._keyword_map[kw] = token
        for sym in syms:
            self._symbol_map[sym] = token

    def unregister(self, token: str) -> None:
        token = token.upper()
        op = self._operators.pop(token, None)
        if op is None:
            return
        for kw in op.keywords:
            self._keyword_map.pop(kw, None)
        for sym in op.symbols:
            # avoid removing symbols reused by other operators
            if self._symbol_map.get(sym) == token:
                self._symbol_map.pop(sym, None)

    def has(self, token: str) -> bool:
        return token.upper() in self._operators

    def binding_power(self, token: str) -> int:
        return self._operators[token.upper()].precedence

    def evaluate(self, token: str, left: Any, right: Any) -> Any:
        return self._operators[token.upper()].evaluator(left, right)

    def keyword_tokens(self) -> Dict[str, str]:
        return dict(self._keyword_map)

    def symbol_tokens(self) -> Dict[str, str]:
        return dict(self._symbol_map)

    def copy(self) -> "OperatorRegistry":
        clone = OperatorRegistry()
        for token, op in self._operators.items():
            clone.register(
                token,
                precedence=op.precedence,
                evaluator=op.evaluator,
                keywords=op.keywords,
                symbols=op.symbols,
            )
        return clone


DEFAULT_OPERATORS = OperatorRegistry()
DEFAULT_OPERATORS.register(
    "OR",
    precedence=10,
    evaluator=lambda left, right: bool(left) or bool(right),
    keywords=("or",),
)
DEFAULT_OPERATORS.register(
    "AND",
    precedence=20,
    evaluator=lambda left, right: bool(left) and bool(right),
    keywords=("and",),
)
DEFAULT_OPERATORS.register(
    "EQ",
    precedence=40,
    evaluator=lambda left, right: left == right,
    symbols=("==",),
)
DEFAULT_OPERATORS.register(
    "NE",
    precedence=40,
    evaluator=lambda left, right: left != right,
    symbols=("!=",),
)
DEFAULT_OPERATORS.register(
    "GT",
    precedence=40,
    evaluator=lambda left, right: left > right,
    symbols=(">",),
)
DEFAULT_OPERATORS.register(
    "LT",
    precedence=40,
    evaluator=lambda left, right: left < right,
    symbols=("<",),
)
DEFAULT_OPERATORS.register(
    "GE",
    precedence=40,
    evaluator=lambda left, right: left >= right,
    symbols=(">=",),
)
DEFAULT_OPERATORS.register(
    "LE",
    precedence=40,
    evaluator=lambda left, right: left <= right,
    symbols=("<=",),
)
DEFAULT_OPERATORS.register(
    "IN",
    precedence=40,
    evaluator=lambda left, right: (left in right) if hasattr(right, "__contains__") else False,
    keywords=("in",),
)
