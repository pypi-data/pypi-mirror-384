import math
from collections.abc import Mapping, Sized

from .is_iterable import is_iterable


def filter_empty(
    iterable,
    *,
    zero_is_empty: bool = True,
    false_is_empty: bool = True,
    str_strip: bool = True,
    string_not_iterable: bool = True,
    drop_none: bool = True,
    drop_nan: bool = True,
    drop_empty_iterables: bool = True,
    drop_empty_mappings: bool = True,
):
    """
    Generator yang mengembalikan elemen non-kosong dari iterable.
    Lihat docstring sebelumnya untuk detail parameter.
    """

    def _is_string_like(x):
        return isinstance(x, (str, bytes, bytearray))

    for x in iterable:
        # None
        if x is None and drop_none:
            continue

        # Bool (khusus, karena subclass int)
        if isinstance(x, bool):
            if false_is_empty and x is False:
                continue
            yield x
            continue

        # String-like
        if _is_string_like(x) and string_not_iterable:
            s = x.decode() if isinstance(x, (bytes, bytearray)) else x
            if str_strip:
                s = s.strip()
            if s == "":
                continue
            yield s
            continue

        # Numerik
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            if drop_nan and isinstance(x, float) and math.isnan(x):
                continue
            if zero_is_empty and x == 0:
                continue
            yield x
            continue

        # Mapping (dict dsb.)
        if isinstance(x, Mapping):
            if drop_empty_mappings and (len(x) == 0):
                continue
            yield x
            continue

        # Iterable lain
        if is_iterable(x):
            if drop_empty_iterables and isinstance(x, Sized) and len(x) == 0:
                continue
            yield x
            continue

        # Fallback pakai to_str
        s = str(x)
        if str_strip and isinstance(s, str):
            s = s.strip()
        if not s:
            continue
        yield x


def test():
    var = [1, None, False, 0, "0", True, {}, ['eee']]
    print(filter_empty(var))
    print(list(filter_empty(var)))


# from .is_iterable import is_iterable
# from .to_str import to_str
#
#
# def filter_empty(iterable, zero_is_empty=True, str_strip=True):
#     """
#     Mengembalikan iterabel yang hanya memiliki nilai
#
#     ```python
#     var = [1, None, False, 0, "0", True, {}, ['eee']]
#     print(filter_empty(var))
#     iprint(filter_empty(var))
#     ```
#     """
#     for i in iterable:
#         if i == 0 and zero_is_empty:
#             continue
#         if isinstance(i, str) and str_strip:
#             i = i.strip()
#         if not is_iterable(i) and not to_str(i):
#             continue
#         yield i
