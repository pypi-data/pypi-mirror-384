import re

from .irange import irange

# batchmaker()
__batchmaker__regex_pattern__ = r"{(?:[^a-zA-Z0-9{}]+)?([a-zA-Z0-9]+)(?:[^a-zA-Z0-9{}]+([a-zA-Z0-9]+))?(?:[^a-zA-Z0-9{}]+(\d+))?(?:[^a-zA-Z0-9{}]+)?}"
__batchmaker__regex_compile__ = re.compile(__batchmaker__regex_pattern__)


def batchmaker(pattern: str):
    """
    Alat Bantu untuk membuat teks yang berulang.
    Gunakan `{[start][separator][finish]([separator][step])}`.
    ```
    [start] dan [finish]    -> bisa berupa huruf maupun angka
    ([separator][step])     -> bersifat optional
    [separator]             -> selain huruf dan angka
    [step]                  -> berupa angka positif
    ```
    """
    s = __batchmaker__regex_compile__.search(pattern)
    if s is None:
        yield pattern
        return

    find = s.group()
    start, finish, step = s.groups()

    for i in irange(start, finish, step, outer=True):
        r = pattern.replace(find, str(i), 1)
        yield from batchmaker(r)


def test():
    import pprint
    pattern = "Urutan {1/6/3} dan {10:9} dan {j k} dan {Z - A - 15} saja."
    pprint.pprint(list(batchmaker(pattern)))
