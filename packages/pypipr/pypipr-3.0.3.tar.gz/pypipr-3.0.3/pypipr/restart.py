import os
import sys


def restart(*argv):
    """
    Mengulang program dari awal seperti memulai awal.

    Bisa ditambahkan dengan argumen tambahan

    ```py
    restart("--stdio")
    ```
    """
    e = sys.executable
    a = argv or sys.argv
    os.execl(e, e, *a)
