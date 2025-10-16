from collections.abc import Iterable, Mapping
from typing import Any, Literal

from .filter_empty import filter_empty

DictMode = Literal["values", "keys", "items"]


def ijoin(
    iterable: Any,
    separator: Any = "",
    start: str = "",
    end: str = "",
    remove_empty: bool = False,
    recursive: bool = True,
    recursive_flat: bool = False,
    str_strip: bool = False,
    *,
    dict_mode: DictMode = "values",
    string_not_iterable: bool = True,
) -> str:
    """
    Versi cepat & dapat dikonfigurasi dari ijoin.

    Parameters
    ----------
    iterable : Any
        Sumber data; jika bukan iterable maka diperlakukan sebagai satu elemen.
    separator : Any
        Pemisah antar elemen (akan di-cast ke str).
    start, end : str
        Prefiks & sufiks hasil akhir (pembungkus).
    remove_empty : bool
        Jika True, elemen kosong (sesuai filter_empty) dibuang.
    recursive : bool
        Jika True, struktur bersarang diproses rekursif.
    recursive_flat : bool
        Jika True, level dalam **tidak** memakai start/end (hanya join).
        Jika False, level dalam ikut memakai start/end (perilaku lama).
    str_strip : bool
        Jika True, setiap elemen di-strip() setelah to_str.
    dict_mode : {'values','keys','items'}
        Cara menangani dict: pakai values/keys/items.
        Untuk 'items', setiap item jadi "key=value" (lihat _item_to_str()).
    string_not_iterable : bool
        Jika True, str/bytes **tidak** diperlakukan sebagai iterable (aman).

    Returns
    -------
    str
        String gabungan.

    Catatan performa
    ----------------
    Menggunakan strategi "kumpulkan bagian → 'separator'.join(parts)" agar
    kompleksitas waktu mendekati O(n) dan menghindari O(n²) dari '+='.
    """

    sep = str(separator)

    def _is_scalar(x: Any) -> bool:
        # Non-iterable atau string/bytes (jika diminta) dianggap satuan.
        if string_not_iterable and isinstance(x, (str, bytes, bytearray)):
            return True
        try:
            iter(x)
            return False
        except TypeError:
            return True

    def _item_to_str(x: Any) -> str:
        s = str(x)
        return s.strip() if str_strip else s

    def _dict_iter(d: Mapping) -> Iterable:
        if dict_mode == "values":
            return d.values()
        if dict_mode == "keys":
            return d.keys()
        # 'items'
        return (f"{_item_to_str(k)}={_item_to_str(v)}" for k, v in d.items())

    def _normalize(it: Any) -> Iterable:
        # Jika bukan iterable → jadikan [it]
        if _is_scalar(it):
            return [it]
        if isinstance(it, Mapping):
            return _dict_iter(it)
        return it

    def _recurse(it: Any, wrap: bool) -> str:
        # wrap=True → gunakan start/end untuk level ini
        it_norm = _normalize(it)
        if remove_empty:
            it_norm = filter_empty(it_norm)

        parts: list[str] = []

        for elem in it_norm:
            if recursive and not _is_scalar(elem) and not isinstance(elem, Mapping):
                # Tentukan apakah level dalam dibungkus
                inner = _recurse(elem, wrap=not recursive_flat)
                parts.append(inner)
            elif recursive and isinstance(elem, Mapping):
                inner = _recurse(_dict_iter(elem), wrap=not recursive_flat)
                parts.append(inner)
            else:
                parts.append(_item_to_str(elem))

        core = sep.join(parts)
        return (start + core + end) if wrap else core

    # Level terluar selalu dibungkus sesuai argumen start/end
    return _recurse(iterable, wrap=True)


# def ijoin(
#     iterable,
#     separator="",
#     start="",
#     end="",
#     remove_empty=False,
#     recursive=True,
#     recursive_flat=False,
#     str_strip=False,
# ):
#     """
#     Simplify Python join functions like PHP function.
#     Iterable bisa berupa sets, tuple, list, dictionary.
#
#     ```python
#     arr = {'asd','dfs','weq','qweqw'}
#     print(ijoin(arr, ', '))
#
#     arr = '/ini/path/seperti/url/'.split('/')
#     print(ijoin(arr, ','))
#     print(ijoin(arr, ',', remove_empty=True))
#
#     arr = {'a':'satu', 'b':(12, 34, 56), 'c':'tiga', 'd':'empat'}
#     print(ijoin(arr, separator='</li>\\n<li>', start='<li>', end='</li>',
#         recursive_flat=True))
#     print(ijoin(arr, separator='</div>\\n<div>', start='<div>', end='</div>'))
#     print(ijoin(10, ' '))
#     ```
#     """
#     if not is_iterable(iterable):
#         iterable = [iterable]
#
#     separator = to_str(separator)
#
#     if isinstance(iterable, dict):
#         iterable = iterable.values()
#
#     if remove_empty:
#         # iterable = (i for i in filter_empty(iterable))
#         iterable = filter_empty(iterable)
#
#     if recursive:
#         rec_flat = dict(start=start, end=end)
#         if recursive_flat:
#             rec_flat = dict(start="", end="")
#
#         def rec(x):
#             return ijoin(
#                 iterable=x,
#                 separator=separator,
#                 **rec_flat,
#                 remove_empty=remove_empty,
#                 recursive=recursive,
#                 recursive_flat=recursive_flat,
#             )
#
#         iterable = ((rec(i) if is_iterable(i) else i) for i in iterable)
#
#     # iterable = (str(i) for i in iterable)
#     iterable = map(str, iterable)
#
#     if str_strip:
#         # iterable = (i.strip() for i in iterable)
#         iterable = map(str.strip, iterable)
#
#     result = start
#
#     for index, value in enumerate(iterable):
#         if index:
#             result += separator
#         result += value
#
#     result += end
#
#     return result
