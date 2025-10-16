import re

from .is_raw_string import is_raw_string


def ireplace(
    string: str,
    replacements: dict,
    flags=re.DOTALL | re.MULTILINE | re.IGNORECASE,
):
    """
    STRing TRanslate mengubah string menggunakan kamus dari dict.
    Replacement dapat berupa text biasa ataupun regex pattern.
    Apabila replacement berupa regex, gunakan raw string `r"..."`
    Untuk regex capturing gunakan `(...)`, dan untuk mengaksesnya
    gunakan `\\1`, `\\2`, .., dst.

    ```python
    text = 'aku ini mau ke sini'
    replacements = {
        "sini": "situ",
        r"(ini)": r"itu dan \\1",
    }
    print(ireplace(text, replacements))
    ```
    """
    for i, v in replacements.items():
        if is_raw_string(i) or is_raw_string(v):
            string = re.sub(i, v, string, flags=flags)
        else:
            string = string.replace(i, v)
    return string
