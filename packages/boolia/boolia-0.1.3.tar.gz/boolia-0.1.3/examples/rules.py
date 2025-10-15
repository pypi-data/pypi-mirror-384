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
print(
    rules.evaluate(
        "eligible",
        context={"user": {"age": 22, "country": "Brazil", "roles": ["member"]}},
    )
)
print(
    rules.evaluate(
        "eligible",
        context={"user": {"age": 22, "country": "Chile", "roles": ["vip"]}},
    )
)
print(
    rules.evaluate(
        "eligible",
        context={"user": {"age": 17, "country": "Chile", "roles": ["member"]}},
    )
)
