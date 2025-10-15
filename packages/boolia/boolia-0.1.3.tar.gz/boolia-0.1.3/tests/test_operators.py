import pytest

from boolia import evaluate, compile_rule, DEFAULT_OPERATORS, OperatorRegistry


def make_ops_with_xor() -> OperatorRegistry:
    ops = DEFAULT_OPERATORS.copy()
    ops.register(
        "XOR",
        precedence=20,
        evaluator=lambda left, right: bool(left) ^ bool(right),
        keywords=("xor",),
    )
    return ops


def test_expression_with_custom_word_operator():
    ops = make_ops_with_xor()

    # Without the custom operator the expression should fail to parse.
    with pytest.raises(SyntaxError):
        evaluate("true xor false")

    assert evaluate("true xor false", operators=ops) is True
    assert evaluate("true xor true", operators=ops) is False


def test_expression_with_custom_symbol_operator():
    ops = DEFAULT_OPERATORS.copy()
    ops.register(
        "XOR",
        precedence=20,
        evaluator=lambda left, right: bool(left) ^ bool(right),
        symbols=("^",),
    )

    assert evaluate("true ^ false", operators=ops) is True
    assert evaluate("false ^ false", operators=ops) is False


def test_rule_compilation_preserves_custom_operators():
    ops = make_ops_with_xor()
    rule = compile_rule("a xor b", operators=ops)

    assert rule.evaluate(context={"a": True, "b": False}) is True
    assert rule.evaluate(context={"a": True, "b": True}) is False

    # Rules still accept an override when needed.
    override = DEFAULT_OPERATORS.copy()
    override.register(
        "XOR",
        precedence=20,
        evaluator=lambda left, right: bool(left) ^ bool(right),
        keywords=("xor",),
    )
    assert rule.evaluate(context={"a": False, "b": True}, operators=override) is True
