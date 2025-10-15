from boolia import evaluate


def test_and_or():
    assert evaluate("true and false or true") is True


def test_dotted_and_tags():
    ctx = {"house": {"light": {"on": False}}}
    assert evaluate("(car and elephant) or house.light.on", context=ctx, tags={"car"}) is False
    ctx["house"]["light"]["on"] = True
    assert evaluate("(car and elephant) or house.light.on", context=ctx, tags={"car"}) is True


def test_comparisons_in():
    ctx = {"user": {"age": 21, "roles": ["admin", "ops"]}}
    assert evaluate("user.age >= 18 and 'admin' in user.roles", context=ctx)


def test_object_attribute_resolution():
    class Obj:
        flag = True

    ctx = {"obj": Obj()}
    assert evaluate("obj.flag", context=ctx) is True


def test_object_method_resolution():
    class ObjA:
        flag = True

    class ObjB:
        def get_obj_a(self):
            return ObjA()

    ctx = {"obj": ObjB()}
    assert evaluate("obj.get_obj_a.flag", context=ctx) is True


def test_object_with_mixed_properties_and_methods():
    class ObjA:
        flag = True

        def get_flag(self):
            return self.flag

    class ObjB:
        def __init__(self):
            self.obj_a = ObjA()

        def get_obj_a(self):
            return self.obj_a

    ctx = {"obj": ObjB()}
    assert evaluate("obj.get_obj_a.flag and obj.obj_a.get_flag", context=ctx) is True


def test_property_method_failure_is_missing():
    class Obj:
        def method_with_arg(self, x):
            return x

    ctx = {"obj": Obj()}
    assert evaluate("obj.method_with_arg", context=ctx, on_missing="false") is False
    assert evaluate("obj.method_with_arg", context=ctx, on_missing="none") is False
    assert evaluate("obj.method_with_arg", context=ctx, on_missing="default", default_value=42) is True
    try:
        evaluate("obj.method_with_arg", context=ctx, on_missing="raise")
    except Exception as e:
        assert e.__class__.__name__ == "MissingVariableError"
    else:
        assert False, "Expected MissingVariableError"
