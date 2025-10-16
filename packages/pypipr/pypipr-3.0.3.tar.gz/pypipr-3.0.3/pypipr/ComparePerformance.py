import time

def _avg(i):
    return sum(i) / len(i)

class ComparePerformance:
    """
    Menjalankan seluruh method dalam class,
    Kemudian membandingkan waktu yg diperlukan.
    Nilai 100 berarti yang tercepat.
    """

    number = 1

    def get_all_instance_methods(self):
        c = set(dir(__class__))
        t = (x for x in dir(self) if x not in c)
        a = []
        for x in t:
            if callable(getattr(self, x)) and not x.startswith("_"):
                a.append(x)
        return a

    def test_method_performance(self, methods):
        d = {x: [] for x in methods}
        for _ in range(self.number):
            for i in set(methods):
                d[i].append(self.get_method_performance(i))
        return d

    def get_method_performance(self, callable_method):
        c = getattr(self, callable_method)
        s = time.perf_counter_ns()
        for _ in range(self.number):
            c()
        f = time.perf_counter_ns()
        return f - s

    def calculate_average(self, d: dict):
        r1 = {i: _avg(v) for i, v in d.items()}
        min_value = min(r1.values()) / 100
        r2 = {i: int(v / min_value) for i, v in r1.items()}
        return r2

    def compare_performance(self):
        m = self.get_all_instance_methods()
        p = self.test_method_performance(m)
        a = self.calculate_average(p)
        return a

    def compare_result(self):
        m = self.get_all_instance_methods()
        return {x: getattr(self, x)() for x in m}


def test():
    import pprint

    class ExampleComparePerformance(ComparePerformance):
        # number = 1
        z = 10

        def a(self):
            return (x for x in range(self.z))

        def b(self):
            return tuple(x for x in range(self.z))

        def c(self):
            return [x for x in range(self.z)]

        def d(self):
            return list(x for x in range(self.z))

    pprint.pprint(ExampleComparePerformance().compare_result())
    print(ExampleComparePerformance().compare_performance())
    print(ExampleComparePerformance().compare_performance())
    print(ExampleComparePerformance().compare_performance())
    print(ExampleComparePerformance().compare_performance())
    print(ExampleComparePerformance().compare_performance())
