def print_to_last_line(text: str, latest=1, clear=True):
    """
    Melakukan print ke konsol tetapi akan menimpa baris terakhir.
    Berguna untuk memberikan progress secara interaktif.

    ```python
    for i in range(5):
        print(str(i) * 10)
    print_to_last_line(f" === last ===")
    ```
    """
    t = ""

    if latest:
        t += f"\033[{latest}A"

    # if append:
    #     t += "\033[10000C" 
    # else:
    #     # t += "\r"
    #     t += "\033[F"
    #     # if clear:
    #     #     t += "\033[K"

    if clear:
        t += "\033[K"

    t += text
    print(t)

