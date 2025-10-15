# boolia

A tiny, safe **boolean expression** engine: like Jinja for logic.

- **Grammar**: `and`, `or`, `not`, parentheses, comparisons (`== != > >= <= <`), `in`
- **Values**: numbers, strings, booleans, `null/None`, identifiers, dotted paths (`user.age`, `house.light.on`, `cart.owner.country`, `cart.owner.get_country`)
- **Tags**: bare identifiers evaluate `True` if present in a `tags: set[str]`
- **Functions**: user-registered, safe callables (`starts_with`, `matches`, ...)
- **RuleBook**: name your rules and evaluate them later
- **RuleGroup**: compose rules with `all`/`any` semantics and nested groups
- **Missing policy**: choose to **raise** or substitute **None/False/custom default**
- **Serialization**: export/import rule books as JSON or (optionally) YAML

```py
from boolia import evaluate, RuleBook, DEFAULT_FUNCTIONS

expr = "(car and elephant) or house.light.on"
print(evaluate(expr, context={"house": {"light": {"on": True}}}, tags={"car"}))  # True
```

## Install

```bash
pip install boolia
```

## Tooling

The project ships with Ruff for linting and MyPy for type checking. After installing the
development extras you can run the primary checks with:

```bash
ruff check .
mypy .
```

## Quick start

```py
from boolia import evaluate, DEFAULT_FUNCTIONS

ctx  = {"user": {"age": 21, "roles": ["admin", "ops"]}}
tags = {"beta"}
expr = "user.age >= 18 and 'admin' in user.roles"
print(evaluate(expr, context=ctx, tags=tags))  # True
```

### Context traversal

When context values are plain objects, boolia walks their public attributes and automatically invokes bound methods that accept no arguments, letting you jump across Python models without adapters.

```py
from boolia import evaluate


class Account:
    country = "Australia"
    province = "NSW"

    def get_country(self):
        return self.country


class User:
    def get_account(self):
        return Account()


ctx = {"user": User()}
print(evaluate("user.get_account.get_country == 'Australia' and user.get_account.province == 'NSW'", context=ctx))  # True
```

If a bound method requires positional arguments, the resolver treats it as a missing path. That means `on_missing="raise"` surfaces a `MissingVariableError`, while the other policies (`false`, `none`, or `default`) return their configured fallback.

### Functions

```py
from boolia import evaluate, DEFAULT_FUNCTIONS

DEFAULT_FUNCTIONS.register("starts_with", lambda s, p: str(s).startswith(str(p)))

expr = "starts_with(user.name, 'Sn')"
print(evaluate(expr, context={"user": {"name": "Snoopy"}}))  # True
```

### Bulk evaluation

```py
from boolia import evaluate_all, evaluate_any

rules = ["1", "true", "x", "y == 1"]
context = {"x": True, "y": 1}

evaluate_all(rules, context=context)  # True
evaluate_any(["false", "x"], context=context)  # True
```

### Custom operators

```py
from boolia import evaluate, DEFAULT_OPERATORS

custom_ops = DEFAULT_OPERATORS.copy()
custom_ops.register(
    "XOR", # The operator identifier
    precedence=20, # Higher precedence than AND/OR
    evaluator=lambda left, right: bool(left) ^ bool(right), # XOR logic
    keywords=("xor",), # Use "xor" in expressions
)

print(evaluate("true xor false", operators=custom_ops))  # True
print(evaluate("true xor true", operators=custom_ops))   # False
```

Operators can be declared with `keywords=("xor",)` for word-style syntax or `symbols=("^",)`
for symbolic tokens. Use `compile_rule(expr, operators=custom_ops)` to persist custom
operators inside compiled rules. When evaluating rules or rule groups you can still pass a
different registry with `operators=` if you need to override their behavior.

### RuleBook

```py
from boolia import RuleBook, RuleGroup

rules = RuleBook()
rules.add("adult", "user.age >= 18")
rules.add("brazilian", "starts_with(user.country, 'Br')")
rules.add("vip", "contains(user.roles, 'vip')")
rules.add_group(
    "eligible",
    mode="all",
    members=[
        "adult",
        RuleGroup(mode="any", members=["brazilian", "vip"]),
    ],
)

ok = rules.evaluate(
    "eligible",
    context={"user": {"age": 22, "country": "Brazil", "roles": ["member"]}},
)
print(ok)  # True

print(rules.evaluate("eligible", context={"user": {"age": 22, "country": "Chile", "roles": ["vip"]}}))  # True
print(rules.evaluate("eligible", context={"user": {"age": 17, "country": "Chile", "roles": ["member"]}}))  # False
```

`RuleGroup` members can be rule names, already compiled `Rule` objects, or other `RuleGroup` instances. Nested groups short-circuit according to their mode (`all`/`any`), empty groups are vacuously `True`/`False`, and cycles raise a helpful error. Add groups with `RuleBook.add_group` or register existing ones with `RuleBook.register`.

#### RuleBook serialization

```py
from boolia import RuleBook

rules = RuleBook()
rules.add("adult", "user.age >= 18")
rules.add_group("gate", members=["adult"])

payload = rules.to_dict()
clone = RuleBook.from_dict(payload)
assert clone.evaluate("gate", context={"user": {"age": 21}})

json_blob = rules.to_json(indent=2)
loaded = RuleBook.from_json(json_blob)

# Optional YAML helpers (requires: pip install boolia[yaml])
yaml_blob = rules.to_yaml()
RuleBook.from_yaml(yaml_blob)
```

- `RuleBook.to_dict` / `RuleBook.from_dict` are the canonical API and perform schema validation by default.
- `to_json` / `from_json` are always available via the standard library.
- `to_yaml` / `from_yaml` lazily import PyYAML; missing dependencies raise a clear `RulebookSerializationError`.
- Pass custom JSON encoders/decoders (e.g. `orjson.dumps`) via the `encoder=` / `decoder=` keyword arguments.

Payloads include a schema version to enable future migrations. Inline rules or groups are supported when importing by default; pass `allow_inline=False` to reject them.

### Missing policy

```py
from boolia import evaluate, MissingVariableError

try:
    evaluate("user.age >= 18 and house.light.on", context={"user": {"age": 20}}, on_missing="raise")
except MissingVariableError as e:
    print(e)  # Missing variable/path: house.light.on

print(evaluate("score >= 10", context={}, on_missing="default", default_value=0))  # False
print(evaluate("flag and beta", context={}, tags={"beta"}, on_missing="none"))     # False (flag is None)
```

### Notes

- Use `on_missing="none"` if you want **tags to override** missing bare identifiers.
- For stricter semantics on dotted paths, keep `on_missing="raise"` and allow tags only for bare names.

## Local development

```bash
pip install -e .[dev]
pytest -q
ruff check .
mypy .
```
