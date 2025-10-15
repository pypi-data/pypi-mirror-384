import json

import pytest

from boolia import (
    Rule,
    RuleBook,
    RuleGroup,
    RulebookSerializationError,
    RulebookValidationError,
    compile_expr,
    compile_rule,
)


def _build_sample_rulebook() -> RuleBook:
    book = RuleBook()
    book.add("adult", "user.age >= 18")
    book.add("vip", "'vip' in user.roles")
    book.add_group("eligible", mode="all", members=["adult", "vip"])
    return book


def test_rulebook_dict_roundtrip_preserves_semantics() -> None:
    book = _build_sample_rulebook()
    payload = book.to_dict(include_metadata=False)
    clone = RuleBook.from_dict(payload)

    assert clone.to_dict(include_metadata=False) == payload
    assert clone.evaluate("eligible", context={"user": {"age": 22, "roles": ["vip"]}})


def test_inline_members_serialization_roundtrip() -> None:
    book = RuleBook()
    book.add("base", "true")
    inline_rule = compile_rule("user.age >= 21")
    book.add_group(
        "mixed",
        mode="any",
        members=[RuleGroup(mode="all", members=[inline_rule, "base"])],
    )

    payload = book.to_dict(include_metadata=False)
    members = payload["entries"]["mixed"]["members"]
    assert isinstance(members[0], dict)
    assert members[0]["kind"] == "group"

    clone = RuleBook.from_dict(payload)
    assert clone.evaluate("mixed", context={"user": {"age": 22}}, tags=set())


def test_import_disallows_inline_when_requested() -> None:
    book = RuleBook()
    book.add("base", "true")
    inline_rule = compile_rule("user.age >= 21")
    book.add_group("mixed", members=[inline_rule, "base"])

    payload = book.to_dict(include_metadata=False)

    with pytest.raises(RulebookValidationError):
        RuleBook.from_dict(payload, allow_inline=False)


def test_json_helpers_support_strings_and_paths(tmp_path) -> None:
    book = _build_sample_rulebook()

    text = book.to_json(indent=2)
    assert isinstance(text, str)
    from_text = RuleBook.from_json(text)
    assert from_text.evaluate("eligible", context={"user": {"age": 19, "roles": ["vip"]}})

    target_path = tmp_path / "rules.json"
    book.to_json(target=target_path, indent=2)
    from_path = RuleBook.from_json(target_path)
    assert from_path.to_dict(include_metadata=False) == book.to_dict(include_metadata=False)


def test_yaml_helpers_optional_dependency() -> None:
    pytest.importorskip("yaml")
    book = _build_sample_rulebook()

    text = book.to_yaml()
    assert isinstance(text, str)
    loaded = RuleBook.from_yaml(text)
    assert loaded.evaluate("eligible", context={"user": {"age": 30, "roles": ["vip"]}})


def test_yaml_helpers_raise_without_dependency(monkeypatch) -> None:
    book = _build_sample_rulebook()

    import boolia.serialization as serialization_mod

    original_import = serialization_mod.importlib.import_module

    def fake_import(name, package=None):
        if name == "yaml":
            raise ImportError("yaml missing")
        return original_import(name, package)

    monkeypatch.setattr(serialization_mod.importlib, "import_module", fake_import)

    with pytest.raises(RulebookSerializationError):
        book.to_yaml()


def test_missing_source_raises_serialization_error() -> None:
    book = RuleBook()
    expr = compile_expr("user.age >= 18")
    book.register("raw", Rule(expr))

    with pytest.raises(RulebookSerializationError):
        book.to_dict()


def test_metadata_counts_rules_and_groups() -> None:
    book = _build_sample_rulebook()
    book.add_group("inline_only", members=[RuleGroup(mode="all")])

    payload = book.to_dict()
    assert payload["metadata"]["rule_count"] == 2
    assert payload["metadata"]["group_count"] == 2


def test_to_json_supports_custom_encoder(tmp_path) -> None:
    book = _build_sample_rulebook()

    def encoder(payload, **_):
        wrapped = {"wrapped": payload}
        return json.dumps(wrapped).encode("utf-8")

    target = tmp_path / "custom.json"
    book.to_json(target=target, encoder=encoder)

    written = target.read_bytes()
    assert b"wrapped" in written


def test_from_json_supports_custom_decoder() -> None:
    book = _build_sample_rulebook()
    payload = {"wrapped": book.to_dict(include_metadata=False)}
    blob = json.dumps(payload)

    def decoder(data, **_):
        text = data.decode("utf-8") if isinstance(data, bytes) else data
        return json.loads(text)["wrapped"]

    clone = RuleBook.from_json(blob, decoder=decoder)
    assert clone.to_dict(include_metadata=False) == book.to_dict(include_metadata=False)
