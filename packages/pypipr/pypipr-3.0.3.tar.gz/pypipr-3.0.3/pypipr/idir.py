def idir(obj, skip_underscore=True):
    """
    Sama seperti dir() python, tetapi skip underscore

    ```python
    iprint(idir(__import__('pypipr')))
    ```
    """
    r = []
    for i in dir(obj):
        if i.startswith("__") or i.endswith("__"):
            if skip_underscore:
                continue

        r.append(i)
    return r
