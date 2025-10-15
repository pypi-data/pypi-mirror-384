from __future__ import annotations

import importlib
import json
import os
from typing import Any, Dict, Iterable, List, Sequence, Tuple, Type, TypeVar, Protocol

from .errors import RulebookSerializationError, RulebookValidationError, RulebookVersionError

SCHEMA_VERSION = "1.0"


class SupportsRulebook(Protocol):
    def register(self, name: str, rule: Any) -> Any: ...

    def get(self, name: str) -> Any: ...

    def names(self) -> Iterable[str]: ...


RulebookT = TypeVar("RulebookT", bound="SupportsRulebook")


def rulebook_to_dict(
    rulebook,
    *,
    version: str = SCHEMA_VERSION,
    include_metadata: bool = True,
    validate: bool = True,
) -> Dict[str, Any]:
    if version != SCHEMA_VERSION:
        raise RulebookVersionError(f"Unsupported schema version for export: {version!r}")

    entries: Dict[str, Any] = {}
    object_names = _build_object_name_map(rulebook)
    stack: List[int] = []

    for name in rulebook.names():
        entry = rulebook.get(name)
        entries[name] = _serialize_entry(
            entry,
            object_names=object_names,
            stack=stack,
            path=(name,),
        )

    metadata = _build_metadata(entries) if include_metadata else {}
    payload = {
        "schema_version": version,
        "metadata": metadata,
        "entries": entries,
    }

    if validate:
        validate_payload(payload, allow_inline=True)

    return payload


def rulebook_from_dict(
    rulebook_cls: Type[RulebookT],
    payload: Dict[str, Any],
    *,
    validate: bool = True,
    allow_inline: bool = True,
) -> RulebookT:
    from .api import RuleGroup, compile_rule  # local import to avoid circular dependency

    if validate:
        validate_payload(payload, allow_inline=allow_inline)

    version = payload.get("schema_version")
    if version != SCHEMA_VERSION:
        raise RulebookVersionError(f"Unsupported schema version: {version!r}")

    book = rulebook_cls()
    entries = payload.get("entries", {})

    pending_groups: Dict[str, Sequence[Any]] = {}
    for name, entry in entries.items():
        kind = entry.get("kind")
        if kind == "rule":
            source = entry.get("source")
            if not isinstance(source, str):
                raise RulebookValidationError(f"Rule entry for {name!r} is missing a 'source' string")
            rule = compile_rule(source)
            book.register(name, rule)
        elif kind == "group":
            mode = entry.get("mode", "all")
            group = RuleGroup(mode=mode)
            book.register(name, group)
            members = entry.get("members", [])
            if not isinstance(members, list):
                raise RulebookValidationError(f"Group entry for {name!r} must provide a member list")
            pending_groups[name] = members
        else:
            raise RulebookValidationError(f"Unsupported entry kind for {name!r}: {kind!r}")

    for name, members in pending_groups.items():
        group = book.get(name)
        _populate_group(group, members, book, allow_inline=allow_inline, stack=[])

    return book


def rulebook_to_json(
    rulebook,
    *,
    target=None,
    validate: bool = True,
    encoder=None,
    **json_kwargs,
):
    payload = rulebook_to_dict(rulebook, validate=validate)

    if encoder is not None:
        serialized = encoder(payload, **json_kwargs)
        if target is None:
            return serialized
        _write_serialized_output(serialized, target)
        return None

    if target is None:
        return json.dumps(payload, **json_kwargs)
    if hasattr(target, "write"):
        json.dump(payload, target, **json_kwargs)
        return None
    if isinstance(target, (str, bytes, os.PathLike)):
        path = os.fspath(target)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, **json_kwargs)
        return None
    raise RulebookSerializationError("Unsupported JSON target; expected path, file-like, or None")


def rulebook_from_json(
    rulebook_cls: Type[RulebookT],
    source,
    *,
    validate: bool = True,
    allow_inline: bool = True,
    decoder=None,
    **json_kwargs,
) -> RulebookT:
    payload = _load_json(source, decoder=decoder, **json_kwargs)
    if not isinstance(payload, dict):
        raise RulebookValidationError("JSON payload must deserialize to a dictionary")
    return rulebook_from_dict(
        rulebook_cls,
        payload,
        validate=validate,
        allow_inline=allow_inline,
    )


def rulebook_to_yaml(rulebook, *, target=None, validate: bool = True, **yaml_kwargs):
    yaml_mod = _require_yaml()
    payload = rulebook_to_dict(rulebook, validate=validate)
    if target is None:
        return yaml_mod.safe_dump(payload, **yaml_kwargs)
    if hasattr(target, "write"):
        yaml_mod.safe_dump(payload, target, **yaml_kwargs)
        return None
    if isinstance(target, (str, bytes, os.PathLike)):
        path = os.fspath(target)
        with open(path, "w", encoding="utf-8") as handle:
            yaml_mod.safe_dump(payload, handle, **yaml_kwargs)
        return None
    raise RulebookSerializationError("Unsupported YAML target; expected path, file-like, or None")


def rulebook_from_yaml(
    rulebook_cls: Type[RulebookT],
    source,
    *,
    validate: bool = True,
    allow_inline: bool = True,
    **yaml_kwargs,
) -> RulebookT:
    yaml_mod = _require_yaml()
    payload = _load_yaml(yaml_mod, source, **yaml_kwargs)
    if not isinstance(payload, dict):
        raise RulebookValidationError("YAML payload must deserialize to a dictionary")
    return rulebook_from_dict(
        rulebook_cls,
        payload,
        validate=validate,
        allow_inline=allow_inline,
    )


def validate_payload(payload: Dict[str, Any], *, allow_inline: bool) -> None:
    if not isinstance(payload, dict):
        raise RulebookValidationError("Payload must be a dictionary")

    version = payload.get("schema_version")
    if not isinstance(version, str):
        raise RulebookValidationError("Payload missing 'schema_version' string")

    metadata = payload.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        raise RulebookValidationError("Payload 'metadata' must be a dictionary when present")

    entries = payload.get("entries")
    if not isinstance(entries, dict):
        raise RulebookValidationError("Payload 'entries' must be a dictionary")

    for name, entry in entries.items():
        if not isinstance(name, str):
            raise RulebookValidationError("Entry names must be strings")
        _validate_entry(entry, allow_inline=allow_inline, path=(name,))


def _validate_entry(entry: Any, *, allow_inline: bool, path: Tuple[str, ...]) -> None:
    if not isinstance(entry, dict):
        raise RulebookValidationError(_format_path(path, "Entry must be a dictionary"))

    kind = entry.get("kind")
    if kind not in {"rule", "group"}:
        raise RulebookValidationError(_format_path(path, "Entry kind must be 'rule' or 'group'"))

    if kind == "rule":
        source = entry.get("source")
        if not isinstance(source, str):
            raise RulebookValidationError(_format_path(path, "Rule entries require a 'source' string"))
        return

    # group validation
    mode = entry.get("mode")
    if mode not in {"all", "any"}:
        raise RulebookValidationError(_format_path(path, "Group mode must be 'all' or 'any'"))

    members = entry.get("members")
    if not isinstance(members, list):
        raise RulebookValidationError(_format_path(path, "Group members must be a list"))

    for index, member in enumerate(members):
        member_path = path + (f"members[{index}]",)
        if isinstance(member, str):
            continue
        if not allow_inline:
            raise RulebookValidationError(_format_path(member_path, "Inline member definitions are disabled"))
        if not isinstance(member, dict):
            raise RulebookValidationError(_format_path(member_path, "Inline members must be dictionaries"))
        _validate_entry(member, allow_inline=allow_inline, path=member_path)


def _serialize_entry(
    entry,
    *,
    object_names: Dict[int, str],
    stack: List[int],
    path: Tuple[str, ...],
) -> Dict[str, Any]:
    from .api import Rule, RuleGroup  # local import to avoid circular dependency

    if isinstance(entry, Rule):
        return _serialize_rule(entry, object_names=object_names, path=path)
    if isinstance(entry, RuleGroup):
        return _serialize_group(entry, object_names=object_names, stack=stack, path=path)
    raise RulebookSerializationError(_format_path(path, f"Unsupported entry type: {type(entry)!r}"))


def _serialize_rule(rule, *, object_names: Dict[int, str], path: Tuple[str, ...]) -> Dict[str, Any]:
    if rule.source is None:
        raise RulebookSerializationError(_format_path(path, "Rule is missing original source; cannot serialize"))
    return {
        "kind": "rule",
        "source": rule.source,
    }


def _serialize_group(
    group,
    *,
    object_names: Dict[int, str],
    stack: List[int],
    path: Tuple[str, ...],
) -> Dict[str, Any]:
    ident = id(group)
    if ident in stack:
        raise RulebookSerializationError(_format_path(path, "Cycle detected while serializing group"))

    stack.append(ident)
    try:
        members = [
            _serialize_member(member, object_names=object_names, stack=stack, path=path + ("members", str(index)))
            for index, member in enumerate(group.members)
        ]
    finally:
        stack.pop()

    return {
        "kind": "group",
        "mode": group.mode,
        "members": members,
    }


def _serialize_member(
    member,
    *,
    object_names: Dict[int, str],
    stack: List[int],
    path: Tuple[str, ...],
) -> Any:
    from .api import Rule, RuleGroup  # local import to avoid circular dependency

    named = object_names.get(id(member))
    if named is not None:
        return named

    if isinstance(member, str):
        return member
    if isinstance(member, Rule):
        return _serialize_rule(member, object_names=object_names, path=path)
    if isinstance(member, RuleGroup):
        return _serialize_group(member, object_names=object_names, stack=stack, path=path)
    raise RulebookSerializationError(_format_path(path, f"Unsupported member type: {type(member)!r}"))


def _populate_group(group, members: Sequence[Any], book, *, allow_inline: bool, stack: List[int]) -> None:
    from .api import RuleGroup, compile_rule  # local import to avoid circular dependency

    group_id = id(group)
    if group_id in stack:
        raise RulebookSerializationError("Cycle detected while rebuilding group members")

    stack.append(group_id)
    try:
        for member in members:
            if isinstance(member, str):
                _ensure_reference(member, book)
                group.add(member)
                continue

            if not allow_inline:
                raise RulebookValidationError("Inline members are disabled for this import")

            if not isinstance(member, dict):
                raise RulebookValidationError("Inline group members must be dictionaries")

            kind = member.get("kind")
            if kind == "rule":
                source = member.get("source")
                if not isinstance(source, str):
                    raise RulebookValidationError("Inline rule members require a 'source' string")
                inline_rule = compile_rule(source)
                group.add(inline_rule)
                continue

            if kind == "group":
                mode = member.get("mode", "all")
                inline_group = RuleGroup(mode=mode)
                inline_group.bind_lookup(book.get)
                inner_members = member.get("members", [])
                _populate_group(inline_group, inner_members, book, allow_inline=allow_inline, stack=stack)
                group.add(inline_group)
                continue

            raise RulebookValidationError(f"Unsupported inline member kind: {kind!r}")
    finally:
        stack.pop()


def _ensure_reference(name: str, book) -> None:
    try:
        book.get(name)
    except KeyError as exc:
        raise RulebookValidationError(f"Unknown rulebook reference: {name!r}") from exc


def _build_object_name_map(rulebook) -> Dict[int, str]:
    mapping: Dict[int, str] = {}
    for name in rulebook.names():
        entry = rulebook.get(name)
        mapping[id(entry)] = name
    return mapping


def _build_metadata(entries: Dict[str, Any]) -> Dict[str, Any]:
    rule_count = sum(1 for entry in entries.values() if entry.get("kind") == "rule")
    group_count = sum(1 for entry in entries.values() if entry.get("kind") == "group")
    return {
        "rule_count": rule_count,
        "group_count": group_count,
    }


def _load_json(source, *, decoder=None, **json_kwargs):
    if hasattr(source, "read"):
        if decoder is None:
            return json.load(source, **json_kwargs)
        data = source.read()
        return decoder(data, **json_kwargs)
    if isinstance(source, os.PathLike):
        path = os.fspath(source)
        with open(path, "rb" if decoder else "r", encoding=None if decoder else "utf-8") as handle:
            if decoder is None:
                return json.load(handle, **json_kwargs)
            data = handle.read()
        return decoder(data, **json_kwargs)
    if isinstance(source, (str, bytes)):
        text = source.decode("utf-8") if isinstance(source, bytes) else source
        if decoder is None:
            if _path_looks_like_file(text):
                try:
                    with open(text, "r", encoding="utf-8") as handle:
                        return json.load(handle, **json_kwargs)
                except FileNotFoundError:
                    pass
            return json.loads(text, **json_kwargs)

        # decoder provided
        if isinstance(source, bytes):
            data = source
        else:
            data = text
            if _path_looks_like_file(text):
                try:
                    with open(text, "rb") as handle:
                        data = handle.read()
                except FileNotFoundError:
                    pass
        return decoder(data, **json_kwargs)
    raise RulebookSerializationError("Unsupported JSON source; expected path, file-like, or text")


def _path_looks_like_file(value: str) -> bool:
    return os.path.sep in value or value.endswith(".json")


def _require_yaml():
    try:
        return importlib.import_module("yaml")
    except ImportError as exc:  # pragma: no cover - exercised via tests with importorskip
        raise RulebookSerializationError("PyYAML is required for YAML support. Install with 'pip install boolia[yaml]'.") from exc


def _load_yaml(yaml_mod, source, **yaml_kwargs):
    if hasattr(source, "read"):
        return yaml_mod.safe_load(source, **yaml_kwargs)
    if isinstance(source, os.PathLike):
        path = os.fspath(source)
        with open(path, "r", encoding="utf-8") as handle:
            return yaml_mod.safe_load(handle, **yaml_kwargs)
    if isinstance(source, (str, bytes)):
        text = source.decode("utf-8") if isinstance(source, bytes) else source
        if _path_looks_like_yaml(text):
            try:
                with open(text, "r", encoding="utf-8") as handle:
                    return yaml_mod.safe_load(handle, **yaml_kwargs)
            except FileNotFoundError:
                pass
        return yaml_mod.safe_load(text, **yaml_kwargs)
    raise RulebookSerializationError("Unsupported YAML source; expected path, file-like, or text")


def _path_looks_like_yaml(value: str) -> bool:
    return value.endswith(".yaml") or value.endswith(".yml") or os.path.sep in value


def _format_path(path: Sequence[str], message: str) -> str:
    joined = " -> ".join(path)
    return f"{message} ({joined})"


def _write_serialized_output(data, target) -> None:
    if hasattr(target, "write"):
        _write_to_stream(target, data)
        return

    if isinstance(target, (str, bytes, os.PathLike)):
        path = os.fspath(target)
        if isinstance(data, bytes):
            with open(path, "wb") as handle:
                handle.write(data)
            return
        if isinstance(data, str):
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(data)
            return
        raise RulebookSerializationError(f"Encoder returned unsupported type {type(data)!r}; expected str or bytes for path targets")

    raise RulebookSerializationError("Unsupported JSON target; expected path, file-like, or None")


def _write_to_stream(stream, data) -> None:
    if isinstance(data, bytes):
        stream.write(data)
    elif isinstance(data, str):
        stream.write(data)
    else:
        raise RulebookSerializationError(f"Encoder returned unsupported type {type(data)!r}; expected str or bytes for stream targets")
