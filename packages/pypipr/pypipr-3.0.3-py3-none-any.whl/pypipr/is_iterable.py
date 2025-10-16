
def is_iterable(var, str_is_iterable=False):
    """
    Mengecek apakah suatu variabel bisa dilakukan forloop atau tidak

    ```python
    s = 'ini string'
    print(is_iterable(s))

    l = [12,21,2,1]
    print(is_iterable(l))

    r = range(100)
    print(is_iterable(r))

    d = {'a':1, 'b':2}
    print(is_iterable(d.values()))
    ```
    """

    """ Metode #1 """
    # TYPE_NONE = type(None)
    # TYPE_GENERATOR = type(i for i in [])
    # TYPE_RANGE = type(range(0))
    # TYPE_DICT_VALUES = type(dict().values())
    # it = (list, tuple, set, dict)
    # it += (TYPE_GENERATOR, TYPE_RANGE, TYPE_DICT_VALUES)
    # return isinstance(var, it)

    """ Metode #2 """
    if not str_is_iterable and isinstance(var, str) :
        return False
    # return isinstance(var, collections.abc.Iterable)

    """ Metode #3 """
    try:
        iter(var)
        return True
    except Exception:
        return False
