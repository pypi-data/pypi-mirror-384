import sys

from .is_empty import is_empty


def exit_if_empty(*args):
    """
    Keluar dari program apabila seluruh variabel
    setara dengan empty

    ```py
    var1 = None
    var2 = '0'
    exit_if_empty(var1, var2)
    ```
    """
    for i in args:
        if not is_empty(i):
            return
    sys.exit()
