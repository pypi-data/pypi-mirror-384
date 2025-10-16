import sys


def iargv(key: int, cast=None, on_error=None):
    """
    Mengambil parameter input dari terminal tanpa menimbulkan error
    apabila parameter kosong.
    Parameter yg berupa string juga dapat diubah menggunakan cast.

    ```python
    print(iargv(1, cast=int, on_error=100))
    ```
    """
    try:
        v = sys.argv[key]
        if cast:
            return cast(v)
        else:
            return v
    except Exception:
        return on_error
