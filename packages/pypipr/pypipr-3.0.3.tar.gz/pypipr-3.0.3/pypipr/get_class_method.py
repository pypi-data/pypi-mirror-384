import pprint


def get_class_method(cls):
    """
    Mengembalikan berupa tuple yg berisi list dari method dalam class
    """
    for x in dir(cls):
        a = getattr(cls, x)
        if not x.startswith("__") and callable(a):
            yield a


def test():
    class ExampleGetClassMethod:
        def a(self):
            return [x for x in range(10)]

        def b(self):
            return [x for x in range(10)]

        def c(self):
            return [x for x in range(10)]

        def d(self):
            return [x for x in range(10)]

    print(get_class_method(ExampleGetClassMethod))
    pprint.pprint(list(get_class_method(ExampleGetClassMethod)))
