from .print_colorize import print_colorize
from .LINUX import LINUX
from .WINDOWS import WINDOWS

if WINDOWS:
    import msvcrt as getch

if LINUX:
    import getch as getch


def input_char(
    prompt=None,
    prompt_ending="",
    newline_after_input=True,
    echo_char=True,
    default=None,
    color=None,
):
    """
    Meminta masukan satu huruf tanpa menekan Enter.

    ```py
    input_char("Input char : ")
    input_char("Input char : ", default='Y')
    input_char("Input Char without print : ", echo_char=False)
    ```
    """
    if prompt:
        print_colorize(prompt, end=prompt_ending, flush=True)

    if default is not None:
        a = default
    else:
        a = getch.getche() if echo_char else getch.getch()

    if newline_after_input:
        print()

    if WINDOWS:
        return a.decode()
    if LINUX:
        return a
    raise Exception("Platform tidak didukung.")
