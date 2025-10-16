from .exit_if_empty import exit_if_empty
from .input_char import input_char
from .print_colorize import print_colorize


def print_choices(lists):
    for i, v in enumerate(lists):
        print(f"{i}. {v}")


def get_choices(prompt):
    print_colorize(prompt, text_end="")
    i = input_char()
    print()
    return i


def convert_to_str(daftar):
    if len(daftar) == 1:
        daftar = daftar[0]
    return daftar


def filter_choices(contains, daftar):
    r = []
    if contains.isdigit():
        for i, v in enumerate(daftar):
            if contains in str(i):
                r.append(v)
        # daftar = [v for i, v in enumerate(daftar) if contains in str(i)]
    else:
        for v in daftar:
            if contains in v:
                r.append(v)
        # daftar = [v for v in daftar if contains in v]
    return r


def get_contains(daftar, prompt):
    print_choices(daftar)
    contains = get_choices(prompt)
    exit_if_empty(len(contains))
    return contains


def choices(daftar, contains=None, prompt="Choose : "):
    """
    Memudahkan dalam membuat pilihan untuk user dalam tampilan console

    ```py
    var = {
        "Pertama" : "Pilihan Pertama",
        "Kedua" : "Pilihan Kedua",
        "Ketiga" : "Pilihan Ketiga",
    }
    res = choices(
        var,
        prompt="Pilih dari dictionary : "
    )
    print(res)
    ```
    """
    daftar = list(str(v) for v in daftar)
    while isinstance(daftar, list):
        contains = contains or get_contains(daftar, prompt)
        daftar = filter_choices(contains, daftar)
        exit_if_empty(daftar)
        daftar = convert_to_str(daftar)
        contains = None
    return daftar
