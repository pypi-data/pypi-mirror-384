from boolia import evaluate, DEFAULT_FUNCTIONS


def test_starts_with_and_matches():
    DEFAULT_FUNCTIONS.register("starts_with", lambda s, p: str(s).startswith(str(p)))
    expr = "starts_with(user.name, 'Jo') and matches(user.email, '.*@acme.com')"
    ctx = {"user": {"name": "João", "email": "joao@acme.com"}}
    assert evaluate(expr, context=ctx) is True
