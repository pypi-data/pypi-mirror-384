import pytest
from boolia import evaluate, MissingVariableError


def test_raise_on_missing():
    with pytest.raises(MissingVariableError):
        evaluate("user.age >= 18 and house.light.on", context={"user": {"age": 20}}, on_missing="raise")


def test_default_on_missing_none():
    assert evaluate("score == None", context={}, on_missing="none") is True


def test_default_on_missing_custom():
    assert evaluate("score >= 10", context={}, on_missing="default", default_value=0) is False
    assert evaluate("score >= 10", context={"score": 12}, on_missing="default", default_value=0) is True
