import inspect

c = {
    "module": inspect.ismodule,
    "class": inspect.isclass,
    "method": inspect.ismethod,
    "function": inspect.isfunction,
}


def ivars(obj, skip_underscore=True):
    """
    Membuat dictionary berdasarkan kategori untuk setiap
    member dari object.

    ```python
    iprint(ivars(__import__('pypipr')))
    ```
    """
    r = {}
    z = None
    for i, v in vars(obj).items():

        for x, y in c.items():
            if y(v):
                z = x
                break
        else:
            z = "variable"

        if i.startswith("__") or i.endswith("__"):
            if skip_underscore:
                continue
            z = f"__{z}__"

        r.setdefault(z, {})[i] = v

    return r
