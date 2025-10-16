from .batchmaker import batchmaker
from .calculate import calculate


def batch_calculate(pattern):
    """
    Analisa perhitungan massal.
    Bisa digunakan untuk mencari alternatif terendah/tertinggi/dsb.
    """
    patterns = batchmaker(pattern)
    for i in patterns:
        try:
            yield (i, calculate(i))
        except Exception:
            yield (i, None)


def test():
    res = batch_calculate("({1 10} m) ** {1 3}")
    for k, v in res:
        print(f"{k} : {v:~P}")
