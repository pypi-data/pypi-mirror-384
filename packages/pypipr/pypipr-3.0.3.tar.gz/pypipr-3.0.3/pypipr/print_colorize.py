import time

import colorama

from .text_colorize import text_colorize


def print_colorize(
    text,
    color=colorama.Fore.GREEN,
    bright=colorama.Style.BRIGHT,
    text_end="\n",
    delay=0.05,
):
    """
    Print text dengan warna untuk menunjukan text penting

    ```py
    print_colorize("Print some text")
    print_colorize("Print some text", color=colorama.Fore.RED)
    ```
    """
    teks = text_colorize(text, color=color, bright=bright)
    print(teks, end=text_end, flush=True)
    if delay:
        time.sleep(delay)
