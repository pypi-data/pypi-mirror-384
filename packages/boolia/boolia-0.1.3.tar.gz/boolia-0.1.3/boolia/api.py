from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Literal, Optional, Set, Union

from .serialization import (
    rulebook_from_dict,
    rulebook_from_json,
    rulebook_from_yaml,
    rulebook_to_dict,
    rulebook_to_json,
    rulebook_to_yaml,
)

from .parser import parse
from .ast import Node
from .resolver import default_resolver_factory, MissingPolicy
from .functions import FunctionRegistry, DEFAULT_FUNCTIONS
from .operators import OperatorRegistry, DEFAULT_OPERATORS


RuleEntry = Union["Rule", "RuleGroup"]
RuleMember = Union[str, RuleEntry]


def compile_expr(source: str, *, operators: Optional[OperatorRegistry] = None) -> Node:
    return parse(source, operators)


def evaluate(
    source_or_ast: Union[str, Node],
    *,
    context: Optional[Dict[str, Any]] = None,
    tags: Optional[Set[str]] = None,
    resolver=None,
    on_missing: MissingPolicy = "false",
    default_value: Any = None,
    functions: Optional[FunctionRegistry] = None,
    operators: Optional[OperatorRegistry] = None,
) -> bool:
    ops = operators or DEFAULT_OPERATORS
    node = compile_expr(source_or_ast, operators=ops) if isinstance(source_or_ast, str) else source_or_ast
    ctx = context or {}
    tg = tags or set()
    res = resolver or default_resolver_factory(ctx, on_missing=on_missing, default_value=default_value)
    fns = functions or DEFAULT_FUNCTIONS
    out = node.eval(res, tg, fns, ops)
    return bool(out)


@dataclass
class Rule:
    ast: Node
    operators: OperatorRegistry = DEFAULT_OPERATORS
    source: Optional[str] = None

    def evaluate(self, *, operators: Optional[OperatorRegistry] = None, **kwargs) -> bool:
        local_kwargs = kwargs.copy()
        implicit_ops = local_kwargs.pop("operators", None)
        ops = operators or implicit_ops or self.operators
        return evaluate(self.ast, operators=ops, **local_kwargs)


def compile_rule(source: str, *, operators: Optional[OperatorRegistry] = None) -> Rule:
    ops = operators or DEFAULT_OPERATORS
    return Rule(compile_expr(source, operators=ops), ops, source)


class RuleGroup:
    def __init__(
        self,
        *,
        mode: Literal["all", "any"] = "all",
        members: Iterable[RuleMember] = (),
    ) -> None:
        if mode not in {"all", "any"}:
            raise ValueError("RuleGroup mode must be 'all' or 'any'")
        self.mode = mode
        self._members = list(members)
        self._rule_lookup: Optional[Callable[[str], RuleEntry]] = None

    @property
    def members(self):
        return tuple(self._members)

    def add(self, member: RuleMember) -> "RuleGroup":
        self._members.append(member)
        if isinstance(member, RuleGroup) and self._rule_lookup is not None:
            member.bind_lookup(self._rule_lookup)
        return self

    def extend(self, members: Iterable[RuleMember]) -> "RuleGroup":
        for member in members:
            self.add(member)
        return self

    def bind_lookup(self, lookup: Callable[[str], RuleEntry]) -> None:
        self._rule_lookup = lookup
        for member in self._members:
            if isinstance(member, RuleGroup):
                member.bind_lookup(lookup)

    def evaluate(self, **kwargs) -> bool:
        return self._evaluate(kwargs, set())

    def _evaluate(self, kwargs: Dict[str, Any], stack: Set[int]) -> bool:
        ident = id(self)
        if ident in stack:
            raise ValueError("Cycle detected while evaluating RuleGroup")
        stack.add(ident)
        try:
            if self.mode == "all":
                for member in self._members:
                    if not self._eval_member(member, kwargs, stack):
                        return False
                return True
            for member in self._members:
                if self._eval_member(member, kwargs, stack):
                    return True
            return False
        finally:
            stack.remove(ident)

    def _eval_member(self, member: RuleMember, kwargs: Dict[str, Any], stack: Set[int]) -> bool:
        if isinstance(member, RuleGroup):
            return member._evaluate(kwargs, stack)
        if isinstance(member, Rule):
            return member.evaluate(**kwargs)
        if isinstance(member, str):
            if self._rule_lookup is None:
                raise ValueError("RuleGroup with named members requires binding to a RuleBook")
            target = self._rule_lookup(member)
            if isinstance(target, RuleGroup):
                return target._evaluate(kwargs, stack)
            return target.evaluate(**kwargs)
        raise TypeError(f"Unsupported RuleGroup member type: {type(member)!r}")


ExpressionLike = Union[str, Node, Rule, "RuleGroup"]


def _evaluate_expression(expr: ExpressionLike, kwargs: Dict[str, Any]) -> bool:
    if isinstance(expr, RuleGroup):
        return expr.evaluate(**kwargs)
    if isinstance(expr, Rule):
        return expr.evaluate(**kwargs)
    return evaluate(expr, **kwargs)


def evaluate_all(expressions: Iterable[ExpressionLike], **kwargs) -> bool:
    for expr in expressions:
        if not _evaluate_expression(expr, kwargs):
            return False
    return True


def evaluate_any(expressions: Iterable[ExpressionLike], **kwargs) -> bool:
    for expr in expressions:
        if _evaluate_expression(expr, kwargs):
            return True
    return False


class RuleBook:
    def __init__(self):
        self._rules: Dict[str, RuleEntry] = {}

    def add(self, name: str, source: str) -> Rule:
        r = compile_rule(source)
        self._store(name, r)
        return r

    def add_group(
        self,
        name: str,
        *,
        mode: Literal["all", "any"] = "all",
        members: Iterable[RuleMember] = (),
    ) -> RuleGroup:
        group = RuleGroup(mode=mode, members=members)
        self._store(name, group)
        return group

    def register(self, name: str, rule: RuleEntry) -> RuleEntry:
        self._store(name, rule)
        return rule

    def replace(self, name: str, source: str) -> Rule:
        return self.add(name, source)

    def get(self, name: str) -> RuleEntry:
        if name not in self._rules:
            raise KeyError(f"Unknown rule: {name}")
        return self._rules[name]

    def evaluate(self, name: str, **kwargs) -> bool:
        return self.get(name).evaluate(**kwargs)

    def names(self):
        return list(self._rules.keys())

    def _store(self, name: str, rule: RuleEntry) -> None:
        self._rules[name] = rule
        if isinstance(rule, RuleGroup):
            rule.bind_lookup(self.get)

    def to_dict(
        self,
        *,
        version: str = "1.0",
        include_metadata: bool = True,
        validate: bool = True,
    ) -> Dict[str, Any]:
        return rulebook_to_dict(
            self,
            version=version,
            include_metadata=include_metadata,
            validate=validate,
        )

    @classmethod
    def from_dict(
        cls,
        payload: Dict[str, Any],
        *,
        validate: bool = True,
        allow_inline: bool = True,
    ) -> "RuleBook":
        return rulebook_from_dict(
            cls,
            payload,
            validate=validate,
            allow_inline=allow_inline,
        )

    def to_json(self, target=None, *, encoder=None, **json_kwargs):
        return rulebook_to_json(self, target=target, encoder=encoder, **json_kwargs)

    @classmethod
    def from_json(
        cls,
        source,
        *,
        validate: bool = True,
        allow_inline: bool = True,
        decoder=None,
        **json_kwargs,
    ) -> "RuleBook":
        return rulebook_from_json(
            cls,
            source,
            validate=validate,
            allow_inline=allow_inline,
            decoder=decoder,
            **json_kwargs,
        )

    def to_yaml(self, target=None, **yaml_kwargs):
        return rulebook_to_yaml(self, target=target, **yaml_kwargs)

    @classmethod
    def from_yaml(
        cls,
        source,
        *,
        validate: bool = True,
        allow_inline: bool = True,
        **yaml_kwargs,
    ) -> "RuleBook":
        return rulebook_from_yaml(
            cls,
            source,
            validate=validate,
            allow_inline=allow_inline,
            **yaml_kwargs,
        )
