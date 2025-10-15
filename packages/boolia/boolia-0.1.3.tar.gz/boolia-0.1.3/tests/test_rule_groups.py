import pytest

from boolia import RuleBook, RuleGroup


def test_rule_group_all_mode():
    rules = RuleBook()
    rules.add("is_adult", "user.age >= 18")
    rules.add("has_discount", "user.discount")
    rules.register("eligible", RuleGroup(mode="all", members=["is_adult", "has_discount"]))

    ctx = {"user": {"age": 22, "discount": True}}
    assert rules.evaluate("eligible", context=ctx) is True

    ctx["user"]["discount"] = False
    assert rules.evaluate("eligible", context=ctx) is False


def test_rule_group_any_mode_nested():
    rules = RuleBook()
    rules.add("is_adult", "user.age >= 18")
    rules.add("has_discount", "user.discount")
    rules.add("vip_account", "user.vip")
    nested = RuleGroup(mode="all", members=["is_adult", "has_discount"])
    rules.register(
        "marketing_target",
        RuleGroup(mode="any", members=[nested, "vip_account"]),
    )

    assert (
        rules.evaluate(
            "marketing_target",
            context={"user": {"age": 19, "discount": True, "vip": False}},
        )
        is True
    )
    assert (
        rules.evaluate(
            "marketing_target",
            context={"user": {"age": 17, "discount": False, "vip": True}},
        )
        is True
    )
    assert (
        rules.evaluate(
            "marketing_target",
            context={"user": {"age": 17, "discount": False, "vip": False}},
        )
        is False
    )


def test_rule_group_cycle_detection():
    rules = RuleBook()
    group = RuleGroup(mode="all", members=["self"])
    rules.register("self", group)

    with pytest.raises(ValueError, match="Cycle detected"):
        rules.evaluate("self", context={})
