from pathlib import Path

from inspect import stack


def dirname(path=None, indeks=-2):
    path = path or stack()[1].filename
    path_obj = Path(path)
    parts = path_obj.parts
    return parts[indeks]
