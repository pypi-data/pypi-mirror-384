# Konstanta yang tidak berubah (dibuat sekali di import time)
_EMPTY_STRS = frozenset({"0", "", "-0", "\n", "\t"})

def is_empty(variable):
    """
    Versi cepat dan aman dari is_empty sesuai himpunan "kosong" yang Anda definisikan:
      - None
      - False
      - Angka 0 (termasuk -0.0)
      - String: "0", "", "-0", "\\n", "\\t"
      - Koleksi kosong: list(), tuple(), dict(), set()
    """
    # 1) Identity checks (O(1), tidak memanggil __eq__)
    if variable is None:
        return True
    if variable is False:               # hindari True==1 jebakan
        return True

    # 2) Numerik 0 (hindari bool; bool subclass int)
    if isinstance(variable, (int, float)) and not isinstance(variable, bool):
        # -0.0 == 0.0 -> True
        if variable == 0:
            return True

    # 3) String "kosong" sesuai definisi
    if isinstance(variable, str):
        if variable in _EMPTY_STRS:     # O(1) membership di frozenset
            return True
        return False

    # 4) Koleksi kosong persis tipe yang ditentukan
    if isinstance(variable, (list, tuple, dict, set)):
        return len(variable) == 0

    # 5) Selain itu: bukan "kosong" menurut definisi
    return False

# # is_empty()
# __empty_list__ = [None, False, 0, -0]
# __empty_list__ += ["0", "", "-0", "\n", "\t"]
# __empty_list__ += [set(), dict(), list(), tuple()]
#
#
# def is_empty(variable, empty=__empty_list__):
#     """
#     Mengecek apakah variable setara dengan nilai kosong pada empty.
#
#     Pengecekan nilai yang setara menggunakan simbol '==', sedangkan untuk
#     pengecekan lokasi memory yang sama menggunakan keyword 'is'
#
#     ```python
#     print(is_empty("teks"))
#     print(is_empty(True))
#     print(is_empty(False))
#     print(is_empty(None))
#     print(is_empty(0))
#     print(is_empty([]))
#     ```
#     """
#     for e in empty:
#         if variable == e:
#             return True
#     return False
