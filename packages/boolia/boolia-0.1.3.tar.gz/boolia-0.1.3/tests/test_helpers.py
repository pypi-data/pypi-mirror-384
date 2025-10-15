from boolia import (
    RuleGroup,
    compile_rule,
    evaluate_all,
    evaluate_any,
)


def test_evaluate_all_strings():
    expressions = ["1", "true", "x", "y == 1"]
    context = {"x": True, "y": 1}

    assert evaluate_all(expressions, context=context) is True


def test_evaluate_any_strings():
    expressions = ["false", "x", "y == 2"]
    context = {"x": False, "y": 1}

    assert evaluate_any(expressions, context=context) is False
    context["x"] = True
    assert evaluate_any(expressions, context=context) is True


def test_evaluate_helpers_with_rules_and_groups():
    rule_true = compile_rule("flag")
    rule_positive = compile_rule("value > 0")
    group = RuleGroup(mode="all", members=[rule_true, rule_positive])

    data = {"flag": True, "value": 10}
    assert evaluate_all([rule_true, group], context=data) is True
    data["value"] = -1
    assert evaluate_any([rule_positive, group], context=data) is False
