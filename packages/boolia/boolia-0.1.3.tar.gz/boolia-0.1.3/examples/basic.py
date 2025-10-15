from boolia import evaluate

expr = "(car and elephant) or house.light.on"
ctx = {"house": {"light": {"on": True}}}
tags = {"car"}

print(evaluate(expr, context=ctx, tags=tags))  # True
